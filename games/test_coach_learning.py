import json
from unittest.mock import patch
import chess
from django.contrib.auth.models import User,AnonymousUser
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import GameReview,DailyTraining
from .coach_learning import learning_context
from .trainer_conversation import question_topic


class CoachLearningTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=User.objects.create_user('coach_student')
        self.other=User.objects.create_user('coach_other')
        self.client.force_login(self.user)
        self.question='¿Qué debería practicar según mi progreso?'

    def review(self,user=None):
        return GameReview.objects.create(user=user or self.user,fingerprint=str(GameReview.objects.count()),language='es',player_color='white',pgn='private PGN',payload=dict(moves=[dict(piece_color='white')],analysis=[dict(loss=250,classification='mistake',engine_context=dict(fen_before=chess.STARTING_FEN,best_move_uci='d2d4',played_move_uci='e2e4',game_phase='opening'))]))

    def plan(self,review):
        from .daily_training import candidates
        return DailyTraining.objects.create(user=review.user,date=timezone.localdate(),tasks=candidates(review.user,review.pk),progress=[dict(resolved=True,correct=True,helped=True,attempts=1)],completed_at=timezone.now())

    def post(self,question=None,**extra):
        return self.client.post(reverse('trainer_chat'),data=json.dumps(dict(question=question or self.question,language='es',**extra)),content_type='application/json')

    def test_learning_answers_stay_local_and_no_private_raw_records_are_returned(self):
        self.plan(self.review())
        with patch('games.views.generate_gemini_explanation') as provider,patch('games.views.open_stockfish_engine') as engine:
            response=self.post()
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['source'],'learning')
        self.assertIn('desarrollar las piezas',response.json()['answer'])
        provider.assert_not_called();engine.assert_not_called()
        self.assertNotIn('private PGN',response.content.decode());self.assertNotIn('coach_student',response.content.decode())

    def test_guest_has_no_memory_queries_or_fake_history(self):
        with self.assertNumQueries(0):self.assertIsNone(learning_context(AnonymousUser(),'es'))
        self.client.logout()
        response=self.post();self.assertIn('Todavía no tengo',response.json()['answer'])

    def test_other_account_and_client_supplied_memory_cannot_change_answer(self):
        self.plan(self.review(self.other))
        response=self.post(learning_context=dict(verified_positions=999,focus='private forged fact'),user_id=self.other.pk)
        self.assertIn('Todavía no tengo',response.json()['answer']);self.assertNotIn('999',response.content.decode())
        self.assertNotIn('private forged fact',response.content.decode())

    def test_cache_is_account_local_and_updates_when_training_changes(self):
        plan=self.plan(self.review())
        first=learning_context(self.user,'es');self.assertEqual(first['session']['independent'],0)
        self.assertIsNone(learning_context(self.other,'es'))
        plan.progress[0]['helped']=False;plan.save()
        second=learning_context(self.user,'es');self.assertEqual(second['session']['independent'],1)
        with self.assertNumQueries(2):self.assertEqual(learning_context(self.user,'es'),second)

    def test_concrete_positions_are_never_routed_as_learning(self):
        for question in ['¿Cómo mejorar esta posición?','¿Qué hago con mi última jugada?','How can I improve this position?','¿Qué debo practicar después de Nf3?']:
            self.assertEqual(question_topic(question,[]),'chess',question)
        self.assertEqual(question_topic('What should I practice in English?',[]),'general')

    def test_three_languages_and_followups(self):
        for lang,question in [('es','¿Qué debo practicar?'),('pt','O que devo praticar?'),('en','What should I practice?')]:
            self.assertEqual(question_topic(question,[]),'learning')
            with patch('games.views.generate_gemini_explanation') as provider:
                response=self.client.post(reverse('trainer_chat'),data=json.dumps(dict(question=question,language=lang)),content_type='application/json')
            self.assertEqual(response.json()['source'],'learning');provider.assert_not_called()
        self.assertEqual(question_topic('¿Y por qué?', [dict(role='user',text='¿Qué debería practicar?')]),'learning')

    def test_no_learned_skill_claim_after_one_session_with_help(self):
        self.plan(self.review())
        response=self.post('¿Estoy mejorando?')
        self.assertIn('0 posiciones',response.json()['answer'])
        self.assertIn('último intento necesitó pistas',response.json()['answer'])
        self.assertIn('todavía no demuestra',response.json()['answer'])

    def test_empty_account_has_no_history_and_no_database_mutation(self):
        response=self.post();self.assertIn('Todavía no tengo',response.json()['answer'])
        self.assertFalse(DailyTraining.objects.exists());self.assertFalse(GameReview.objects.exists())

    def test_summary_is_bounded_and_includes_no_moves_or_free_text(self):
        self.review()
        data=learning_context(self.user,'es');encoded=json.dumps(data)
        self.assertLess(len(encoded),2500)
        self.assertNotIn('private PGN',encoded);self.assertNotIn('d2d4',encoded);self.assertNotIn('fen',data)
