import json
from unittest.mock import patch

import chess
from django.test import TestCase
from games import test_trainer


class CoachReliabilityTests(TestCase):
    def test_invalid_payloads_return_client_error(self):
        for payload in ([], {"moves":[None]}, {"moves":[3]}, {"moves":[{"from":"a1"}]}):
            with self.subTest(payload=payload):
                response=self.client.post('/coach-analysis/',json.dumps(payload),content_type='application/json')
                self.assertEqual(response.status_code,400)

    def test_shutdown_error_does_not_erase_success(self):
        engine=test_trainer.TrainerTests.engine(self)
        engine.quit.side_effect=chess.engine.EngineError('private cleanup details')
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine):
            response=self.client.post('/coach-analysis/',json.dumps({'moves':[{'from':'e2','to':'e4'}]}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertNotIn('private cleanup details',response.content.decode())

    def test_engine_error_is_retryable_without_private_details(self):
        engine=test_trainer.TrainerTests.engine(self)
        engine.analyse.side_effect=chess.engine.EngineError('private analysis details')
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine):
            response=self.client.post('/coach-analysis/',json.dumps({'moves':[{'from':'e2','to':'e4'}]}),content_type='application/json')
        self.assertEqual(response.status_code,500)
        self.assertTrue(response.json()['retryable'])
        self.assertNotIn('private analysis details',response.content.decode())


    def test_turn_questions_use_selected_board_without_external_services(self):
        for language, question, expected in (("es","¿A quién le toca jugar ahora?","negras"),("pt","De quem é a vez?","pretas"),("en","Whose turn is it?","Black")):
            with patch("games.views.open_stockfish_engine") as engine, patch("games.views.generate_gemini_explanation") as provider:
                response=self.client.post('/trainer-chat/',json.dumps({"question":question,"moves":["e2e4"],"language":language}),content_type='application/json')
            self.assertEqual(response.json()["source"],"board")
            self.assertIn(expected,response.json()["answer"])
            engine.assert_not_called()
            provider.assert_not_called()

    def test_finished_game_has_no_turn(self):
        response=self.client.post('/trainer-chat/',json.dumps({"question":"Whose turn is it?","moves":["f2f3","e7e5","g2g4","d8h4"],"language":"en"}),content_type='application/json')
        self.assertIn("Black won",response.json()["answer"])
        self.assertNotIn("to move",response.json()["answer"])


    def test_unsupported_move_gets_one_verified_correction(self):
        engine=test_trainer.TrainerTests.engine(self)
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine),patch('games.views.generate_gemini_explanation',side_effect=['Play Qh8.','Develop a piece.']) as provider:
            response=self.client.post('/trainer-chat/',json.dumps({'question':'Best move?','language':'en'}),content_type='application/json')
        self.assertEqual(response.json()['status'],'ok')
        self.assertEqual(provider.call_count,2)
        self.assertIn('CORRECTION:',provider.call_args.args[0])
        self.assertIn('deadline',provider.call_args.kwargs)

    def test_mate_outcome_is_explicit_in_conversation_context(self):
        engine=test_trainer.TrainerTests.engine(self)
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine),patch('games.views.generate_gemini_explanation',return_value='Black won by checkmate.') as provider:
            response=self.client.post('/trainer-chat/',json.dumps({'question':'Explain this chess position','moves':['f2f3','e7e5','g2g4','d8h4'],'language':'en'}),content_type='application/json')
        self.assertEqual(response.json()['status'],'ok')
        self.assertIn('"game_over":true',provider.call_args.args[0])
        self.assertIn('"result":"0-1"',provider.call_args.args[0])
        self.assertIn('"termination":"CHECKMATE"',provider.call_args.args[0])

    def test_plain_language_piece_origins_are_verified_without_accepting_illegal_moves(self):
        from games.engine_analysis import build_trainer_engine_context, explanation_moves_are_grounded
        board=chess.Board()
        board.push_uci('e2e4')
        board.push_uci('e7e5')
        context=build_trainer_engine_context(test_trainer.TrainerTests.engine(self),board,['e4','e5'],'best move','white','es')
        self.assertTrue(explanation_moves_are_grounded('Podés desarrollar el caballo de b1 a c3 con Nc3.',context))
        self.assertTrue(explanation_moves_are_grounded('Tu peón avanzó de e2 a e4.',context))
        self.assertFalse(explanation_moves_are_grounded('Jugá Qh8.',context))
        self.assertFalse(explanation_moves_are_grounded('Jugá e2e5.',context))


    def test_spanish_followup_with_inverted_question_mark_keeps_chess_position(self):
        engine=test_trainer.TrainerTests.engine(self)
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine),patch('games.views.generate_gemini_explanation',return_value='Tu e4 ocupa el centro.') as provider:
            response=self.client.post('/trainer-chat/',json.dumps({'question':'¿Por qué?','moves':['e2e4','e7e5'],'reference_moves':['e2e4'],'history':[{'role':'user','text':'¿Mi jugada fue buena?'}],'language':'es'}),content_type='application/json')
        self.assertEqual(response.json()['topic'],'chess')
        self.assertEqual(response.json()['position_moves'],['e2e4'])
        self.assertIn('"played_move"',provider.call_args.args[0])


class TrainerProviderBudgetTests(test_trainer.SimpleTestCase):
    def test_expired_correction_budget_never_calls_provider(self):
        from games.gemini_service import generate_gemini_explanation, GeminiFailure
        from django.core.cache import cache
        cache.clear()
        with patch.dict('os.environ', {'GEMINI_ENABLED':'true','GEMINI_API_KEY':'test-only'}), patch('games.gemini_service.time.monotonic',side_effect=[0,3,3,3]), patch('games.gemini_service.request.urlopen') as provider:
            with self.assertRaises(GeminiFailure) as failure:
                generate_gemini_explanation('expired correction',report_errors=True,deadline=2)
        self.assertEqual(failure.exception.code,'timeout')
        provider.assert_not_called()


class EmptyBoardCoachTests(TestCase):
    def test_last_move_question_is_fast_local_and_translated(self):
        for language,question,expected in (('es','¿La última jugada fue buena?','Todavía no hay'),('pt','A última jogada foi boa?','Ainda não há'),('en','Was the last move good?','There is no move')):
            with patch('games.views.generate_gemini_explanation') as provider,patch('games.views.open_stockfish_engine') as engine:
                response=self.client.post('/trainer-chat/',json.dumps(dict(question=question,language=language)),content_type='application/json')
            self.assertEqual(response.json()['source'],'board')
            self.assertEqual(response.json()['status'],'ok')
            self.assertIn(expected,response.json()['answer'])
            provider.assert_not_called();engine.assert_not_called()
    def test_explicit_proposed_move_still_requires_analysis(self):
        from .trainer_conversation import position_turn_answer
        self.assertIsNone(position_turn_answer('Would e4 be a good last move?',chess.Board(),'en'))
