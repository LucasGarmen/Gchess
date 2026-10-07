from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import DailyTraining, WeeklyChallenge, WeeklyChallengeEntry, GameReview
from .learning_progress import learning_progress
from .weekly import week_start

class LearningProgressTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('progress_student')
        self.other=User.objects.create_user('progress_other')
        self.client.force_login(self.user)
        self.today=timezone.localdate()
    def plan(self,offset=0,done=True,user=None,progress=None):
        return DailyTraining.objects.create(user=user or self.user,date=self.today-timedelta(days=offset),tasks=[{}]*3,progress=progress or [dict(attempts=1,correct=True,resolved=True,helped=False)]*3,completed_at=timezone.now() if done else None)
    def weekly(self,score=20,user=None,attempts=5,offset=0):
        challenge,_=WeeklyChallenge.objects.get_or_create(week_start=week_start()-timedelta(days=offset),defaults={'tasks':[{}]*5})
        return WeeklyChallengeEntry.objects.create(challenge=challenge,user=user or self.user,score=score,progress=[dict(attempted=i<attempts,first_correct=False,resolved=i<attempts,helped=False) for i in range(5)])
    def dashboard(self):return learning_progress(self.user,'es',[])
    def test_read_only_empty_page_and_authentication(self):
        with patch('games.views.open_stockfish_engine') as engine:
            response=self.client.get(reverse('learning'))
        self.assertEqual(response.status_code,200);engine.assert_not_called()
        self.assertEqual(response.context['progress']['days'],0)
        self.assertEqual(response.context['progress']['activities'],[])
        self.assertFalse(DailyTraining.objects.exists());self.assertFalse(WeeklyChallenge.objects.exists())
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.client.logout();self.assertEqual(self.client.get(reverse('learning')).status_code,302)
    def test_seven_days_excludes_future_old_and_other_accounts(self):
        self.plan(0);self.plan(2);self.plan(6);self.plan(7);self.plan(-1);self.plan(1,user=self.other)
        d=self.dashboard();self.assertEqual(d['days'],3);self.assertTrue(d['goal_reached']);self.assertEqual(d['goal_progress'],3)
        self.assertEqual(d['resolved'],9);self.assertEqual(d['independent'],9)
        self.assertEqual(len(d['calendar']),7);self.assertEqual(d['calendar'][0]['date'],self.today-timedelta(days=6))
        self.assertTrue(d['calendar'][-1]['today']);self.assertEqual(d['calendar'][-1]['status'],'done')
    def test_partial_plan_not_counted_as_completed_day(self):
        self.plan(done=False,progress=[dict(attempts=1,correct=True,resolved=True,helped=False),dict(attempts=2,correct=False,resolved=False,helped=False),dict(attempts=0,correct=False,resolved=False,helped=False)])
        d=self.dashboard();self.assertEqual(d['days'],0);self.assertEqual(d['resolved'],1);self.assertEqual(d['daily_resolved'],1)
        self.assertEqual(d['daily_status'],'in_progress');self.assertEqual(d['next_step']['url'],reverse('daily_training'))
    def test_hints_retries_and_reveals_are_not_first_attempt_success(self):
        self.plan(progress=[dict(attempts=1,correct=True,resolved=True,helped=True),dict(attempts=2,correct=True,resolved=True,helped=False),dict(attempts=0,correct=False,resolved=True,helped=True)])
        d=self.dashboard();self.assertEqual(d['days'],1);self.assertEqual(d['resolved'],3);self.assertEqual(d['independent'],0)
    def test_next_step_prioritizes_daily_then_weekly(self):
        self.weekly(attempts=2)
        self.assertEqual(self.dashboard()['next_step']['url'],reverse('daily_training'))
        self.plan()
        self.assertEqual(self.dashboard()['next_step']['url'],reverse('weekly_challenge'))
    def test_finished_current_challenges_select_pending_review_then_practice(self):
        self.plan();self.weekly()
        review=GameReview.objects.create(user=self.user,fingerprint='pending',language='es',player_color='white',pgn='1. e4',payload={})
        rows=[dict(review=review,summary={'errors':1,'focus_name':'Apertura'})]
        d=learning_progress(self.user,'es',rows);self.assertEqual(d['next_step']['url'],reverse('review_detail',args=[review.pk]))
        review.goal_completed_at=timezone.now()
        self.assertEqual(learning_progress(self.user,'es',rows)['next_step']['url'],reverse('practice'))
    def test_previous_challenge_cannot_replace_current_week(self):
        self.plan();past=self.weekly(offset=7,score=50)
        d=self.dashboard();self.assertIsNone(d['weekly_score']);self.assertEqual(d['weekly_status'],'not_started')
        self.assertEqual(d['next_step']['url'],reverse('weekly_challenge'))
        self.assertIn('?practice=1',next(a['url'] for a in d['activities'] if a['title']=='Desafío semanal'))
    def test_zero_point_participation_is_visible_without_other_users(self):
        self.weekly(score=0,attempts=1);self.weekly(score=50,user=self.other)
        d=self.dashboard();self.assertEqual(d['weekly_score'],0);self.assertEqual(d['weekly_attempts'],1)
        self.assertEqual(len(d['activities']),1);self.assertIn('0 / 50',d['activities'][0]['detail'])
    def test_unused_plan_does_not_fabricate_activity(self):
        self.plan(done=False,progress=[dict(attempts=0,correct=False,resolved=False,helped=False)]*3)
        self.assertEqual(self.dashboard()['activities'],[])
    def test_goal_progress_caps_without_hiding_extra_training(self):
        for i in range(7):self.plan(i)
        d=self.dashboard();self.assertEqual(d['days'],7);self.assertEqual(d['goal_progress'],3)
    def test_languages_and_integration_with_saved_reviews(self):
        self.plan();self.weekly()
        GameReview.objects.create(user=self.other,fingerprint='secret-other',language='es',player_color='white',pgn='private-other',payload={})
        for lang in ['es','pt','en']:
            session=self.client.session;session['language']=lang;session.save()
            response=self.client.get(reverse('learning'))
            self.assertEqual(response.status_code,200);self.assertNotContains(response,'private-other')
            self.assertContains(response,response.context['progress']['texts']['habit'])
