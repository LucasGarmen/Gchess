from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import UserPuzzleStats, PlayerProfile
from .models import LearningReward, ChessGame, Move, DailyTraining, WeeklyChallenge, WeeklyChallengeEntry, GameReview
from .rewards import grant, summary, today, reward_game, reward_session, reward_weekly, reward_review
from .views import record_puzzle_progress

class RewardsTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('reward_student')
        self.other=User.objects.create_user('reward_rival')

    def total(self):
        return UserPuzzleStats.objects.get(user=self.user).xp_total

    def test_duplicate_and_daily_cap_preserve_existing_xp(self):
        UserPuzzleStats.objects.create(user=self.user,xp_total=95,nivel=1,xp_del_nivel_actual=95)
        self.assertEqual(grant(self.user,'one','review',10,cap=20),10)
        self.assertEqual(grant(self.user,'one','review',10,cap=20),0)
        self.assertEqual(grant(self.user,'two','review',10,cap=20),10)
        self.assertEqual(grant(self.user,'three','review',10,cap=20),0)
        stats=UserPuzzleStats.objects.get(user=self.user)
        self.assertEqual((stats.xp_total,stats.nivel,stats.xp_del_nivel_actual),(115,2,15))
        self.assertEqual(stats.puzzles_resueltos,0)
        tomorrow=today()+timedelta(days=1)
        with patch('games.rewards.today',return_value=tomorrow):
            self.assertEqual(grant(self.user,'three','review',10,cap=20),0)
            self.assertEqual(grant(self.user,'four','review',10,cap=20),10)

    def test_repeated_puzzle_keeps_stats_without_more_xp(self):
        self.assertEqual(record_puzzle_progress(self.user,'same',True,mate_in=1)['xp_ganado'],5)
        self.assertEqual(record_puzzle_progress(self.user,'same',True,mate_in=1)['xp_ganado'],0)
        stats=UserPuzzleStats.objects.get(user=self.user)
        self.assertEqual(stats.puzzles_correctos,2)
        self.assertEqual(stats.xp_total,5)
        self.assertEqual(record_puzzle_progress(self.user,'wrong',False)['xp_ganado'],0)

    def test_sessions_require_actual_correct_answer(self):
        plan=DailyTraining.objects.create(user=self.user,date=today(),tasks=[],progress=[{'correct':False}],completed_at=timezone.now())
        self.assertEqual(reward_session(plan),0)
        plan.progress=[{'correct':True}]
        self.assertEqual(reward_session(plan),20)
        self.assertEqual(reward_session(plan),0)
        challenge=WeeklyChallenge.objects.create(week_start=today(),tasks=[])
        entry=WeeklyChallengeEntry.objects.create(user=self.user,challenge=challenge,progress=[{'first_correct':False}],completed_at=timezone.now())
        self.assertEqual(reward_weekly(entry),0)
        entry.progress=[{'first_correct':True}]
        self.assertEqual(reward_weekly(entry),25)
        self.assertEqual(reward_weekly(entry),0)

    def test_review_canonical_dedup_and_short_game(self):
        review=GameReview.objects.create(user=self.user,fingerprint='first',language='pt',player_color='white',pgn='1. e4 e5 2. Nf3 Nc6 *',payload={})
        self.assertEqual(reward_review(review),10)
        review.pgn='[Event "Different header"]\n\n1. e4 e5 2. Nf3 Nc6 *'
        self.assertEqual(reward_review(review),0)
        review.pgn='1. d4 d5 *'
        self.assertEqual(reward_review(review),0)

    def game(self,peer=None,moves=12):
        game=ChessGame.objects.create(white_user=self.user,black_user=peer or self.other,white_player='A',black_player='B')
        Move.objects.bulk_create([Move(game=game,move_number=i+1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white') for i in range(moves)])
        game.status='finished';game.result='draw';game.save()
        return game

    def test_game_rewards_both_players_once_and_limit_same_rival(self):
        game=self.game()
        reward_game(game.pk);reward_game(game.pk)
        self.assertEqual(self.total(),5)
        self.assertEqual(UserPuzzleStats.objects.get(user=self.other).xp_total,5)
        reward_game(self.game().pk)
        self.assertEqual(self.total(),5)
        self.assertFalse(PlayerProfile.objects.filter(user=self.user).exists())

    def test_no_short_game_selfplay_or_coach_rewards(self):
        reward_game(self.game(moves=2).pk)
        reward_game(self.game(peer=self.user).pk)
        game=ChessGame.objects.create(white_user=self.user,white_player='A',black_player='Coach',status='finished',result='white')
        reward_game(game.pk)
        self.assertFalse(LearningReward.objects.filter(xp__gt=0).exists())

    def test_activity_streak_and_readonly_owned_endpoint(self):
        grant(self.user,'one','review',10)
        with patch('games.rewards.today',return_value=today()-timedelta(days=1)):
            grant(self.user,'two','review',10)
        self.assertEqual(summary(self.user)['streak'],2)
        url=reverse('reward_progress')
        self.assertEqual(self.client.get(url).status_code,302)
        self.client.force_login(self.user)
        game=ChessGame.objects.create(white_user=self.other,white_player='A',black_player='B')
        self.assertEqual(self.client.get(url,{'game':game.pk}).status_code,404)
        before=LearningReward.objects.count()
        self.assertEqual(self.client.get(url).json()['total'],20)
        self.assertEqual(self.client.post(url).status_code,405)
        self.assertEqual(LearningReward.objects.count(),before)

    def test_compact_ui_languages_and_guest(self):
        self.client.force_login(self.user)
        for language in ('pt','es','en'):
            session=self.client.session;session['language']=language;session.save()
            response=self.client.get(reverse('training'))
            self.assertContains(response,'reward-progress')
            self.assertContains(response,'+20 XP')
        self.client.logout()
        self.assertNotContains(self.client.get(reverse('training')),'reward-progress')

    def test_finished_game_signal_awards_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            game=self.game()
        self.assertEqual(self.total(),5)
        with self.captureOnCommitCallbacks(execute=True):
            game.save()
        self.assertEqual(self.total(),5)

    def test_puzzle_daily_cap(self):
        for index,expected in enumerate((50,50,0)):
            self.assertEqual(record_puzzle_progress(self.user,'hard-'+str(index),True,mate_in=5)['xp_ganado'],expected)
        self.assertEqual(self.total(),100)

    def test_database_rejects_duplicate_key(self):
        from django.db import transaction, IntegrityError
        grant(self.user,'unique','review',10)
        with self.assertRaises(IntegrityError), transaction.atomic():
            LearningReward.objects.create(user=self.user,key='unique',kind='review',xp=10,date=today())

    def test_daily_http_completion_returns_persisted_reward(self):
        import json
        self.client.force_login(self.user)
        self.client.post(reverse('daily_training_start'))
        plan=DailyTraining.objects.get(user=self.user,date=timezone.localdate())
        for index,task in enumerate(plan.tasks):
            response=self.client.post(reverse('daily_training_answer'), data=json.dumps(dict(id=plan.pk,index=index,action='try' if index==0 else 'reveal',move=task['solution'])),content_type='application/json')
            self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['state']['reward_xp'],20)
        self.assertEqual(self.total(),20)
        self.client.get(reverse('daily_training'))
        self.assertEqual(self.total(),20)
