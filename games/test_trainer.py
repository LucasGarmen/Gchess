import json
import os
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

import chess
from django.test import TestCase, SimpleTestCase
from django.core.cache import cache
from .gemini_service import generate_gemini_explanation, GeminiFailure, cache_key_for_prompt, gemini_model, discard_gemini_explanation
from .engine_analysis import build_trainer_engine_context, explanation_moves_are_grounded
from .prompts import build_trainer_chat_prompt


class GeminiTests(SimpleTestCase):
    def test_rejected_answer_is_removed_from_cache(self):
        prompt = 'test position'
        key = cache_key_for_prompt('trainer_chat', gemini_model(), prompt)
        cache.set(key, 'unsupported move')
        discard_gemini_explanation(prompt)
        self.assertIsNone(cache.get(key))

    def setUp(self):
        cache.clear()
        self.env = patch.dict(os.environ, {"GEMINI_ENABLED": "true", "GEMINI_API_KEY": "secret", "GEMINI_TIMEOUT_SECONDS": "15"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_provider_failures(self):
        for failure, code in [(TimeoutError(), "timeout"), (HTTPError("url", 429, "quota", {}, None), "quota"), (HTTPError("url", 404, "missing", {}, None), "model_unavailable"), (HTTPError("url", 500, "provider", {}, None), "provider_error")]:
            with self.subTest(code=code), patch("games.gemini_service.request.urlopen", side_effect=failure):
                with self.assertLogs("games.gemini_service", level="WARNING") as logs:
                    with self.assertRaises(GeminiFailure) as raised:
                        generate_gemini_explanation("question", report_errors=True)
                self.assertEqual(raised.exception.code, code)
                self.assertNotIn("secret", str(logs.output))

    def test_transient_failure_retries_and_recovers(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"candidates":[{"content":{"parts":[{"text":"Try developing a piece."}]}}]}'
        for failure in (TimeoutError(), HTTPError("url", 503, "busy", {}, None)):
            cache.clear()
            with patch("games.gemini_service.request.urlopen", side_effect=[failure, response]) as call:
                self.assertEqual(generate_gemini_explanation("retry", report_errors=True), "Try developing a piece.")
            self.assertEqual(call.call_count, 2)

    def test_permanent_failures_do_not_retry(self):
        for status in (403, 404, 429):
            with patch("games.gemini_service.request.urlopen", side_effect=HTTPError("url", status, "error", {}, None)) as call:
                with self.assertRaises(GeminiFailure):
                    generate_gemini_explanation("permanent", report_errors=True)
            self.assertEqual(call.call_count, 1)

    def test_retry_uses_remaining_budget(self):
        with patch("games.gemini_service.time.monotonic", side_effect=[0, 0, 0, 19, 25]), patch("games.gemini_service.request.urlopen", side_effect=TimeoutError()) as call:
            with self.assertRaises(GeminiFailure):
                generate_gemini_explanation("budget", report_errors=True)
        self.assertEqual([item.kwargs["timeout"] for item in call.call_args_list], [15, 6])

    def test_empty_malformed_and_truncated_responses(self):
        for payload, code in [(b"not json", "invalid_response"), (b"[]", "invalid_response"), (b'{}', "empty_response"), (b'{"candidates":[{"finishReason":"MAX_TOKENS","content":{"parts":[{"text":"half"}]}}]}', "invalid_response")]:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = payload
            with patch("games.gemini_service.request.urlopen", return_value=response), self.assertRaises(GeminiFailure) as raised:
                generate_gemini_explanation("question", report_errors=True)
            self.assertEqual(raised.exception.code, code)

    def test_timeout_metrics_exclude_content_and_key(self):
        with patch("games.gemini_service.time.monotonic", side_effect=[1, 1, 1, 9, 17]), patch("games.gemini_service.request.urlopen", side_effect=TimeoutError()) as call, self.assertLogs("games.gemini_service", level="INFO") as logs:
            with self.assertRaises(GeminiFailure):
                generate_gemini_explanation("PRIVATE_QUESTION", report_errors=True)
        self.assertIn("category=timeout", str(logs.output))
        self.assertIn("elapsed_ms=16000", str(logs.output))
        self.assertNotIn("PRIVATE_QUESTION", str(logs.output))
        self.assertNotIn("secret", str(logs.output))
        self.assertEqual(call.call_args.kwargs["timeout"], 15)

    def test_success_and_cached_responses_are_measured(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"A star is hot gas."}]}}]}'
        with patch("games.gemini_service.request.urlopen", return_value=response) as call, self.assertLogs("games.gemini_service", level="INFO") as logs:
            self.assertEqual(generate_gemini_explanation("PRIVATE_GENERAL"), "A star is hot gas.")
            self.assertEqual(generate_gemini_explanation("PRIVATE_GENERAL"), "A star is hot gas.")
        self.assertEqual(call.call_count, 1)
        self.assertIn("category=ok", str(logs.output))
        self.assertIn("category=cached", str(logs.output))
        self.assertNotIn("PRIVATE_GENERAL", str(logs.output))
        self.assertNotIn("A star is hot gas", str(logs.output))


class TrainerTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_last_move_answer_can_mention_verified_previous_move(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="e5 fue buena: responde a tu e4. Ahora podés desarrollar con Cf3."):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"¿La última jugada fue buena?", "moves":["e2e4", "e7e5"], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["source"], "gemini")

    def test_unsupported_move_remains_rejected_and_cache_is_discarded(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="Jugá Qh8."), patch("games.views.discard_gemini_explanation") as discard:
            response = self.client.post("/trainer-chat/", json.dumps({"question":"¿La última jugada fue buena?", "moves":["e2e4", "e7e5"], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["status"], "invalid_response")
        self.assertIsNone(response.json()["answer"])
        self.assertEqual(discard.call_count, 2)

    def test_starting_position_supplies_pawn_origin_and_destination(self):
        engine = self.engine()
        info = {"score": chess.engine.PovScore(chess.engine.Cp(45), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]}
        engine.analyse.side_effect = lambda board, limit, **kwargs: [info] if kwargs.get('multipv') else info
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=engine), patch("games.views.generate_gemini_explanation", return_value="Todavía estás en la posición inicial: mové el peón de e2 a e4.") as gemini:
            response = self.client.post("/trainer-chat/", json.dumps({"question":"¿Qué hago ahora en esta posición?", "moves":[], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["status"], "ok")
        prompt = gemini.call_args.args[0]
        self.assertIn('"move_count":0', prompt)
        self.assertIn('"best_move_details":{"piece":"pawn","color":"white","from":"e2","to":"e4"}', prompt)
        self.assertIn('explicitly say this is the starting position', prompt)

    def test_local_piece_letters_are_validated_without_ignoring_moves(self):
        context = {"legal_moves_san":["Nc3", "Bb5", "Rae1", "Qh5", "Kf1"], "engine":{"candidate_lines":[]}}
        for move in ["Cc3", "Ab5", "Tae1", "Dh5", "Rf1", "Nc3"]:
            self.assertTrue(explanation_moves_are_grounded(move, context), move)
        self.assertFalse(explanation_moves_are_grounded("Cc6", context))

    def test_implicit_last_move_after_greeting_uses_engine(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="e4 mantiene la evaluacion.") as gemini:
            response = self.client.post("/trainer-chat/", json.dumps({"question":"esa estuvo buena?", "moves":["e2e4"], "history":[{"role":"user", "text":"que onda wey"}], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["topic"], "chess")
        self.assertIn('"played_move"', gemini.call_args.args[0])
        self.assertIn('"move_san":"e4"', gemini.call_args.args[0])

    def test_now_uses_new_board_instead_of_old_chat_position(self):
        moves = ["e2e4", "e7e5", "b1c3"]
        board = chess.Board()
        for move in moves:
            board.push_uci(move)
        for question in ["y ahi, que hago?", "ahora, ahora que hago? el caballo ya lo movi a c3"]:
            with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="Ahora juegan las negras.") as gemini:
                response = self.client.post("/trainer-chat/", json.dumps({"question":question, "moves":moves, "reference_moves":["e2e4"], "history":[{"role":"user", "text":"e4 fue buena?"}], "language":"es"}), content_type="application/json")
            self.assertEqual(response.json()["status"], "ok")
            self.assertEqual(response.json()["fen"], board.fen())
            self.assertIn('"turn":"black"', gemini.call_args.args[0])

    def engine(self):
        engine = MagicMock()
        def analyze(board, limit, **kwargs):
            move = next(iter(board.legal_moves), None)
            result = {"score": chess.engine.PovScore(chess.engine.Cp(45), chess.WHITE), "pv": [move] if move else []}
            return [result] if kwargs else result
        engine.analyse.side_effect = analyze
        return engine

    def test_position_color_history_and_fallback(self):
        history = [{"role":"user", "text":"Why e4?"}, {"role":"assistant", "text":"Controla el centro."}]
        engine = self.engine()
        for code in ("timeout", "quota", "empty_response", "invalid_response", "model_unavailable", "disabled"):
            with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=engine), patch("games.views.generate_gemini_explanation", side_effect=GeminiFailure(code)) as gemini:
                response = self.client.post("/trainer-chat/", json.dumps({"question":"And now?", "moves":[{"from":"e2", "to":"e4"}], "player_color":"black", "language":"es", "history":history}), content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], code)
            self.assertEqual(response.json()["fen"], self.expected_fen())
            prompt = gemini.call_args.args[0]
            self.assertIn('"player_color":"black"', prompt)
            self.assertIn('Why e4?', prompt)
            self.assertIsNone(response.json()["answer"])
            self.assertEqual(response.json()["source"], "unavailable")
        self.assertEqual(engine.analyse.call_count, 1)

    def expected_fen(self):
        board = chess.Board()
        board.push_uci("e2e4")
        return board.fen()

    def test_extended_history_preserves_position_metadata(self):
        history = [{"role": "user" if i % 2 == 0 else "assistant", "text": f"message {i}", "fen": chess.Board().fen()} for i in range(12)]
        with patch("games.views.generate_gemini_explanation", return_value="Hello.") as gemini:
            response = self.client.post("/trainer-chat/", json.dumps({"question": "hello", "moves": [], "history": history}), content_type="application/json")
        self.assertEqual(response.json()["status"], "ok")
        self.assertIn("message 0", gemini.call_args.args[0])
        self.assertIn("message 11", gemini.call_args.args[0])
        self.assertIn(chess.Board().fen(), gemini.call_args.args[0])

    def test_invalid_inputs_rejected_before_engine(self):
        for data in ({"question":{}}, {"question":"q", "history":[{}]}, {"question":"q", "history":[{}]*13}, {"question":"q", "moves":[{"from":"e2", "to":"e5"}]}):
            with patch("games.views.open_stockfish_engine") as engine:
                response = self.client.post("/trainer-chat/", json.dumps(data), content_type="application/json")
            self.assertEqual(response.status_code, 400)
            engine.assert_not_called()

    def test_budget_and_illegal_move(self):
        engine = self.engine()
        with patch.dict(os.environ, {"TRAINER_ANALYSIS_SECONDS":"0.3"}):
            context = build_trainer_engine_context(engine, chess.Board(), [], "e2e5", "black", "es")
        self.assertFalse(context["proposed_move"]["legal"])
        self.assertEqual(engine.analyse.call_args.args[1].time, 0.3)
        self.assertEqual(context["engine"]["score_cp_for_player"], -45)

    def test_success_and_unsupported_move(self):
        for answer, source in [("Consider e4.", "gemini"), ("Play Qh5.", "unavailable")]:
            with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value=answer):
                response = self.client.post("/trainer-chat/", json.dumps({"question":"best move?", "moves":[], "language":"es"}), content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["source"], source)

    def test_terminal_position(self):
        board = chess.Board()
        for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
            board.push_uci(move)
        context = build_trainer_engine_context(self.engine(), board, [], "help", "white", "es")
        from .views import trainer_context_fallback
        self.assertIn("no hay jugada", trainer_context_fallback(context, "es"))

    def test_saved_game_analyzer_uses_black_player_perspective(self):
        from django.contrib.auth.models import User
        from .models import ChessGame
        white = User.objects.create_user(username="trainer-white", password="pass")
        black = User.objects.create_user(username="trainer-black", password="pass")
        game = ChessGame.objects.create(owner=white, white_user=white, black_user=black, white_player="trainer-white", black_player="trainer-black", status="finished", result="white")
        self.client.force_login(black)
        response = self.client.get("/analyze/", {"game_id":game.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["trainer_player_color"], "black")

    def test_engine_missing_response_hides_path(self):
        with patch("games.views.configured_stockfish_path", return_value=("", "secret path")):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"best move?"}), content_type="application/json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "engine_unavailable")
        self.assertNotIn("secret path", response.content.decode())

    def test_bot_engine_failure_is_explicit_and_engine_is_closed(self):
        engine = self.engine()
        engine.play.side_effect = chess.engine.EngineError("private engine details")
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=engine):
            response = self.client.post("/engine-move/", json.dumps({"moves":[], "elo":2000}), content_type="application/json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["code"], "engine_unavailable")
        self.assertNotIn("private engine details", response.content.decode())
        engine.quit.assert_called_once()

    def test_bot_missing_engine_is_explicit(self):
        with patch("games.views.configured_stockfish_path", return_value=("", "missing")):
            response = self.client.post("/engine-move/", json.dumps({"moves":[], "elo":1320}), content_type="application/json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "engine_unavailable")

    def test_e4_was_good_uses_played_move_and_before_position(self):
        engine = self.engine()
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=engine), patch("games.views.generate_gemini_explanation", return_value="e4 mantiene la evaluacion.") as gemini:
            response = self.client.post("/trainer-chat/", json.dumps({"question":"e4 fue buena?", "moves":["e2e4"], "player_color":"white", "language":"es"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "gemini")
        prompt = gemini.call_args.args[0]
        self.assertIn('"played_move"', prompt)
        self.assertIn('"move_san":"e4"', prompt)
        self.assertIn('"before_fen":"' + chess.STARTING_FEN, prompt)
        self.assertIn('"change_for_mover_cp":0', prompt)
        self.assertNotIn('"proposed_move":{"raw":"e4","legal":false', prompt)

    def test_followup_keeps_original_position_after_board_changes(self):
        reference_board = chess.Board()
        reference_board.push_uci("e2e4")
        history = [{"role":"user", "text":"e4 fue buena?", "fen":reference_board.fen()}, {"role":"assistant", "text":"e4 mantiene la evaluacion.", "fen":reference_board.fen()}]
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="e4 mantiene la evaluacion.") as gemini:
            response = self.client.post("/trainer-chat/", json.dumps({"question":"Por que?", "moves":["e2e4", "e7e5"], "reference_moves":["e2e4"], "history":history, "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["fen"], reference_board.fen())
        self.assertEqual(response.json()["position_moves"], ["e2e4"])
        self.assertIn('"played_move"', gemini.call_args.args[0])
        self.assertIn('Por que?', gemini.call_args.args[0])

    def test_general_questions_and_unverifiable_information(self):
        for question, answer in [("Como se forman las estrellas en el espacio?", "Las estrellas se forman en nubes de gas."), ("Que anuncio la NASA hoy?", "No puedo verificar noticias de hoy.")]:
            with patch("games.views.open_stockfish_engine") as engine, patch("games.views.generate_gemini_explanation", return_value=answer) as gemini:
                response = self.client.post("/trainer-chat/", json.dumps({"question":question,"history":[{"role":"user","text":"e4 fue buena?"}],"language":"es"}), content_type="application/json")
            self.assertEqual(response.json()["answer"], answer)
            self.assertEqual(response.json()["topic"], "general")
            engine.assert_not_called()
            self.assertIn("NO browsing or live tools", gemini.call_args.args[0])
            self.assertIn("Respond in Spanish", gemini.call_args.args[0])

    def test_general_failure_never_substitutes_stockfish(self):
        for code in ["timeout", "quota", "empty_response", "provider_error"]:
            with patch("games.views.open_stockfish_engine") as engine, patch("games.views.generate_gemini_explanation", side_effect=GeminiFailure(code)):
                response = self.client.post("/trainer-chat/", json.dumps({"question":"Hablame del espacio", "language":"es"}), content_type="application/json")
            data = response.json()
            self.assertEqual(data["status"], code)
            self.assertIsNone(data["answer"])
            self.assertIsNone(data["engine_analysis"])
            self.assertTrue(data["retryable"])
            engine.assert_not_called()

    def test_chess_failure_exposes_only_labelled_engine_facts(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", side_effect=GeminiFailure("timeout")):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"e4 fue buena?", "moves":["e2e4"], "language":"es"}), content_type="application/json")
        self.assertIsNone(response.json()["answer"])
        self.assertIn("e4", response.json()["engine_analysis"])
        self.assertNotIn("Recomendacion", response.json()["engine_analysis"])
        self.assertEqual(response.json()["source"], "unavailable")

    def test_failed_why_does_not_receive_unrelated_best_move(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", side_effect=GeminiFailure("quota")):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"Por que?", "history":[{"role":"user","text":"Que es una apertura de ajedrez?"}], "language":"es"}), content_type="application/json")
        self.assertIsNone(response.json()["engine_analysis"])

    def test_followup_after_general_topic_stays_general(self):
        with patch("games.views.open_stockfish_engine") as engine, patch("games.views.generate_gemini_explanation", return_value="La gravedad atrae el gas."):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"Por que?", "history":[{"role":"user", "text":"Como nacen las estrellas en el espacio?"}], "reference_moves":["e2e4"], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["topic"], "general")
        engine.assert_not_called()

    def test_why_about_space_changes_topic_after_chess(self):
        with patch("games.views.open_stockfish_engine") as engine, patch("games.views.generate_gemini_explanation", return_value="Por la gravedad."):
            response = self.client.post("/trainer-chat/", json.dumps({"question":"Por que nacen estrellas en el espacio?", "history":[{"role":"user", "text":"e4 fue buena?"}], "language":"es"}), content_type="application/json")
        self.assertEqual(response.json()["topic"], "general")
        engine.assert_not_called()


class TrainerMoveTrackingTests(TestCase):
    engine = TrainerTests.engine
    def setUp(self):
        cache.clear()

    def ask_move(self, question, color="white"):
        return self.client.post("/trainer-chat/", json.dumps({"question":question,
            "moves":["e2e4", "e7e5"], "language":"es", "player_color":color}),
            content_type="application/json")

    def test_my_move_after_opponent_reply(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", return_value=self.engine()), patch("games.views.generate_gemini_explanation", return_value="Tu peón de e2 avanzó a e4.") as gemini:
            response = self.ask_move("¿Mi jugada fue buena?")
        self.assertEqual(response.json()["status"], "ok")
        prompt = gemini.call_args.args[0]
        context = json.loads(prompt.split("ENGINE_CONTEXT (null for a general question):\n")[1])
        self.assertEqual(context["played_move"]["move_uci"], "e2e4")
        self.assertEqual(context["played_move"]["moving_color"], "white")

    def test_retry_reuses_analysis_but_color_has_its_own_context(self):
        with patch("games.views.configured_stockfish_path", return_value=("stockfish", "")), patch("games.views.open_stockfish_engine", side_effect=lambda path:self.engine()) as engine, patch("games.views.generate_gemini_explanation", side_effect=GeminiFailure("timeout")):
            self.ask_move("¿Mi jugada fue buena?")
            self.ask_move("¿Mi jugada fue buena?")
            self.assertEqual(engine.call_count, 1)
            self.ask_move("¿Mi jugada fue buena?", "black")
            self.assertEqual(engine.call_count, 2)
