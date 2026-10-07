from unittest.mock import patch
import json
import chess
from django.contrib.auth.models import User,AnonymousUser
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from .models import GameReview
from .error_patterns import recurring_errors,detect
from .coach_learning import learning_context

HANGING='4r1k1/8/8/8/4N3/8/8/R5K1 w - - 0 1'
MISSED='6k1/8/8/8/4r3/8/8/2B1R1K1 w - - 0 1'

class ErrorPatternTests(TestCase):
    def setUp(self):
        cache.clear();self.user=User.objects.create_user('pattern_student');self.other=User.objects.create_user('pattern_other')
        self.client.force_login(self.user)
    def review(self,fen=HANGING,played='a1a2',best='e4c3',**changes):
        fields=dict(user=self.user,fingerprint=str(GameReview.objects.count()),language='es',player_color='white',pgn='private game text',payload=dict(moves=[dict(piece_color='white')],analysis=[dict(move_number=1,loss=250,classification='blunder',engine_context=dict(fen_before=fen,played_move_uci=played,best_move_uci=best,game_phase='middlegame'))]))
        fields.update(changes);return GameReview.objects.create(**fields)
    def test_detects_verified_unprotected_piece(self):
        board=chess.Board(HANGING)
        self.assertTrue(board.is_valid())
        result=detect(board,chess.Move.from_uci('a1a2'),chess.Move.from_uci('e4c3'))
        self.assertEqual(result,dict(kind='hanging',square='e4',piece_type=chess.KNIGHT))
    def test_detects_missed_capture(self):
        board=chess.Board(MISSED)
        self.assertTrue(board.is_valid())
        self.assertEqual(detect(board,chess.Move.from_uci('c1d2'),chess.Move.from_uci('e1e4'))['kind'],'missed')
    def test_two_distinct_games_required_and_one_game_counts_once(self):
        one=self.review()
        self.assertEqual(recurring_errors(self.user,'es')['patterns'],[])
        self.review(fingerprint=one.fingerprint,language='en')
        self.assertEqual(recurring_errors(self.user,'es')['patterns'],[])
        self.review()
        pattern=recurring_errors(self.user,'es')['patterns'][0]
        self.assertEqual(pattern['games'],2)
        self.assertIn('caballo en e4',pattern['examples'][0]['explanation'])
    def test_recapturable_piece_not_classified_as_unprotected(self):
        from .error_patterns import loose_targets
        board=chess.Board('4r1k1/8/8/8/4N3/8/8/4R1K1 b - - 0 1')
        self.assertNotIn(chess.E4,loose_targets(board,chess.WHITE))
    def test_illegal_and_opponent_moves_are_ignored(self):
        self.review(played='a1a8');self.review(player_color='black')
        self.assertFalse(recurring_errors(self.user,'es')['patterns'])
    def test_accounts_and_anonymous_are_isolated(self):
        self.review(user=self.other);self.review(user=self.other)
        self.assertFalse(recurring_errors(self.user,'es')['patterns'])
        with self.assertNumQueries(0):self.assertFalse(recurring_errors(AnonymousUser(),'es')['patterns'])
    def test_coach_uses_local_evidence_in_all_languages(self):
        self.review();self.review()
        for language in ('es','pt','en'):
            context=learning_context(self.user,language)
            self.assertEqual(context['recurring'][0]['games'],2)
        with patch('games.views.generate_gemini_explanation') as provider,patch('games.views.open_stockfish_engine') as engine:
            response=self.client.post(reverse('trainer_chat'),json.dumps(dict(question='¿Cuáles son mis errores?',language='es')),content_type='application/json')
        self.assertEqual(response.json()['source'],'learning');self.assertIn('caballo en e4',response.json()['answer'])
        self.assertNotIn('private game text',response.json()['answer']);provider.assert_not_called();engine.assert_not_called()
    def test_learning_page_links_to_owned_examples_and_practice(self):
        one=self.review();two=self.review()
        response=self.client.get(reverse('learning'))
        self.assertContains(response,reverse('review_detail',args=[one.pk]))
        self.assertContains(response,reverse('review_practice',args=[two.pk]))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('review_detail',args=[one.pk])).status_code,404)
    def test_sample_is_limited_to_thirty_distinct_games(self):
        for i in range(32):self.review()
        result=recurring_errors(self.user,'es')
        self.assertEqual(result['reviewed'],30);self.assertEqual(result['patterns'][0]['games'],30)
    def test_improvement_question_keeps_cautious_progress_answer(self):
        self.review();self.review()
        response=self.client.post(reverse('trainer_chat'),json.dumps(dict(question='¿Estoy mejorando?',language='es')),content_type='application/json')
        self.assertIn('Todavía no tengo suficientes repasos',response.json()['answer'])

    def test_targeted_practice_uses_detected_position(self):
        self.review();target=self.review()
        url=reverse('review_practice',args=[target.pk])
        response=self.client.get(url+'?pattern=hanging')
        self.assertContains(response,'name="pattern" value="hanging"')
        response=self.client.post(reverse('review_practice_start',args=[target.pk]),{'pattern':'hanging'})
        self.assertRedirects(response,url+'?pattern=hanging')
        plan=self.client.session['review-practice-'+str(target.pk)]
        self.assertEqual(plan['tasks'][0]['fen'],HANGING)
        self.assertEqual(plan['pattern'],'hanging')
    def test_unverified_pattern_cannot_be_forced_into_practice(self):
        target=self.review()
        response=self.client.get(reverse('review_practice',args=[target.pk])+'?pattern=missed')
        self.assertFalse(response.context['has_positions'])
    def test_repeated_error_questions_route_locally(self):
        from .trainer_conversation import question_topic
        for question in ('¿Qué errores repito?','Quais erros eu repito?','What mistakes do I repeat?'):
            self.assertEqual(question_topic(question,[]),'learning')
    def test_same_game_multiple_errors_does_not_inflate_count(self):
        target=self.review();payload=target.payload
        payload['moves']*=3;payload['analysis']*=3;target.payload=payload;target.save()
        self.review()
        self.assertEqual(recurring_errors(self.user,'es')['patterns'][0]['games'],2)
