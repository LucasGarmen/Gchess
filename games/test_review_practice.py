import json
from django.test import TestCase,Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch
from .models import GameReview,DailyTraining,WeeklyChallengeEntry
from .daily_training import candidates
from .first_steps import TEXTS

class ReviewPracticeTests(TestCase):
    def setUp(self):
        cache.clear();self.user=User.objects.create_user('review_learner');self.other=User.objects.create_user('outsider');self.client.force_login(self.user)
        self.review=GameReview.objects.create(user=self.user,fingerprint='one',language='es',player_color='white',pgn='1. e4',payload={'moves':[{'piece_color':'white'}],'analysis':[dict(move_number=1,loss=200,classification='mistake',engine_context={'fen_before':'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1','best_move_uci':'d2d4','played_move_uci':'e2e4','game_phase':'opening'})]})
    def begin(self):return self.client.post(reverse('review_practice_start',args=[self.review.pk]))
    def answer(self,action,move=None,index=0):return self.client.post(reverse('review_practice_answer'),json.dumps(dict(id=self.review.pk,index=index,action=action,move=move)),content_type='application/json')
    def test_owned_verified_positions_no_live_engine_or_global_training_writes(self):
        with patch('games.views.open_stockfish_engine') as engine:self.assertEqual(self.begin().status_code,302)
        engine.assert_not_called();response=self.client.get(reverse('review_practice',args=[self.review.pk]))
        self.assertEqual(response.context['session_data']['total'],1);self.assertNotIn('solution',response.context['session_data']['task'])
        self.assertFalse(DailyTraining.objects.exists());self.assertFalse(WeeklyChallengeEntry.objects.exists())
    def test_read_only_get_then_idempotent_start_and_resume(self):
        self.client.get(reverse('review_practice',args=[self.review.pk]));self.assertNotIn('review-practice-'+str(self.review.pk),self.client.session)
        self.begin();self.answer('try','e2e4');self.begin()
        plan=self.client.session['review-practice-'+str(self.review.pk)];self.assertEqual(plan['progress'][0]['attempts'],1)
        state=self.answer('try','d2d4').json()['state'];self.assertTrue(state['completed']);self.assertEqual(state['helped'],1)
    def test_hints_solution_restart_and_replay_guard(self):
        self.begin();self.answer('hint');self.assertTrue(self.answer('reveal').json()['state']['completed'])
        self.assertEqual(self.answer('try','d2d4').status_code,409)
        self.client.post(reverse('review_practice_start',args=[self.review.pk]),{'restart':'1'})
        state=self.answer('try','d2d4').json()['state'];self.assertEqual(state['independent'],1)
        self.review.refresh_from_db();self.assertIsNotNone(self.review.goal_completed_at)
    def test_illegal_move_and_wrong_index_do_not_change_progress(self):
        self.begin();self.assertEqual(self.answer('try','a1a8').status_code,400);self.assertEqual(self.answer('reveal',index=2).status_code,409)
        self.assertEqual(self.client.session['review-practice-'+str(self.review.pk)]['progress'][0]['attempts'],0)
    def test_private_access_post_csrf_and_login(self):
        self.begin();self.client.force_login(self.other)
        for name in ['review_practice','review_practice_start']:
            response=self.client.get(reverse(name,args=[self.review.pk])) if name=='review_practice' else self.client.post(reverse(name,args=[self.review.pk]))
            self.assertEqual(response.status_code,404)
        self.assertEqual(self.answer('reveal').status_code,404)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.user);self.assertEqual(secure.post(reverse('review_practice_start',args=[self.review.pk])).status_code,403)
        self.client.logout();self.assertEqual(self.begin().status_code,302)
    def test_no_fabricated_positions_and_review_filter(self):
        blank=GameReview.objects.create(user=self.user,fingerprint='blank',language='es',player_color='white',pgn='',payload={})
        self.assertEqual(candidates(self.user,blank.pk),[])
        response=self.client.get(reverse('review_practice',args=[blank.pk]));self.assertFalse(response.context['has_positions'])
        self.assertEqual(candidates(self.other,self.review.pk),[])
    def test_three_languages_and_entry_routes(self):
        self.begin()
        for lang in ['es','pt','en']:
            session=self.client.session;session['language']=lang;session.save()
            home=self.client.get(reverse('home'))
            for word in ['coach','friends','train']:self.assertContains(home,TEXTS[lang][word])
            self.assertContains(home,reverse('game_create'));self.assertContains(home,reverse('training'))
            self.assertEqual(self.client.get(reverse('review_practice',args=[self.review.pk])).status_code,200)
