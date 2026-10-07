from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import ChessGame, Move, Friendship, DailyTraining, WeeklyChallenge, WeeklyChallengeEntry, GameInvitation, DismissedNotice
from .notices import items
from .weekly import week_start

class NoticeTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('notices_player')
        self.other=User.objects.create_user('notices_friend')
        self.stranger=User.objects.create_user('notices_stranger')
        self.client.force_login(self.user)
        self.game=ChessGame.objects.create(white_user=self.user,black_user=self.other,white_player=self.user.username,black_player=self.other.username)
    def payload(self):
        return self.client.get(reverse('game_notifications')).json()
    def dismiss(self,key):
        return self.client.post(reverse('notice_dismiss',args=[key]))
    def test_turn_private_and_finished_filtered(self):
        ChessGame.objects.create(white_user=self.other,black_user=self.stranger,white_player='secret',black_player='private')
        data=self.payload();self.assertEqual(len(data['action_notices']),1)
        self.assertIn(self.other.username,data['action_notices'][0]['label'])
        Move.objects.create(game=self.game,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')
        self.assertEqual(self.payload()['action_notices'],[])
        self.game.status='finished';self.game.save()
        self.assertEqual(self.payload()['action_notices'],[])
    def test_dismiss_is_durable_and_next_turn_returns(self):
        key=self.payload()['action_notices'][0]['key']
        self.assertEqual(self.dismiss(key).status_code,200)
        self.assertEqual(self.dismiss(key).status_code,200)
        self.assertEqual(DismissedNotice.objects.count(),1)
        self.assertEqual(self.payload()['action_notices'],[])
        Move.objects.create(game=self.game,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')
        Move.objects.create(game=self.game,move_number=2,from_square='e7',to_square='e5',piece_type='pawn',piece_color='black')
        self.assertNotEqual(self.payload()['action_notices'][0]['key'],key)
        self.assertEqual(ChessGame.objects.get(pk=self.game.pk).status,'draft')
    def test_friend_requests_only_recipient_and_pending(self):
        low,high=sorted([self.user,self.other],key=lambda u:u.pk)
        friendship=Friendship.objects.create(low_user=low,high_user=high,requester=self.other)
        self.assertEqual(len(items(self.user,'es')['action_notices']),2)
        self.assertEqual(len(items(self.other,'es')['action_notices']),0)
        friendship.status='accepted';friendship.save()
        self.assertEqual(len(items(self.user,'es')['action_notices']),1)
    def test_cannot_dismiss_other_users_game_or_forged_key(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.dismiss(f'game:{self.game.pk}:0').status_code,404)
        self.assertEqual(self.dismiss('weekly:2000-01-01').status_code,404)
        self.assertFalse(DismissedNotice.objects.exists())
    def test_dismiss_requires_post_login_and_csrf(self):
        url=reverse('notice_dismiss',args=[f'game:{self.game.pk}:0'])
        self.assertEqual(self.client.get(url).status_code,405)
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post(url).status_code,403)
        self.client.logout();self.assertEqual(self.client.post(url).status_code,302)
    def test_daily_reminder_only_current_unfinished_plan(self):
        self.assertEqual(len(self.payload()['training_notices']),1)
        DailyTraining.objects.create(user=self.other,date=timezone.localdate(),tasks=[],progress=[])
        DailyTraining.objects.create(user=self.user,date=timezone.localdate()-timedelta(days=1),tasks=[],progress=[])
        plan=DailyTraining.objects.create(user=self.user,date=timezone.localdate(),tasks=[{}],progress=[{}])
        key=f'daily:{plan.date.isoformat()}'
        self.assertEqual(len(self.payload()['training_notices']),2)
        self.dismiss(key);self.assertEqual(len(self.payload()['training_notices']),1)
        plan.completed_at=timezone.now();plan.save()
        self.assertEqual(len(items(self.user,'es',True)['training_notices']),1)
    def test_weekly_dismiss_resets_only_with_new_week(self):
        key=f'weekly:{week_start().isoformat()}'
        self.dismiss(key);self.assertEqual(self.payload()['training_notices'],[])
        with patch('games.weekly.week_start',return_value=week_start()+timedelta(days=7)):
            self.assertEqual(len(self.payload()['training_notices']),1)
    def test_completed_weekly_entry_removes_reminder(self):
        challenge=WeeklyChallenge.objects.create(week_start=week_start(),tasks=[])
        entry=WeeklyChallengeEntry.objects.create(user=self.user,challenge=challenge,progress=[])
        self.assertIn('posiciones',items(self.user,'es')['training_notices'][0]['label'])
        entry.completed_at=timezone.now();entry.save()
        self.assertEqual(self.payload()['training_notices'],[])
    def test_poll_does_not_create_training_and_is_not_cached(self):
        response=self.client.get(reverse('game_notifications'))
        self.assertIn('no-store',response['Cache-Control'])
        self.assertFalse(WeeklyChallenge.objects.exists())
        self.assertFalse(DailyTraining.objects.exists())
        self.assertFalse(DismissedNotice.objects.exists())
    def test_invitation_dismiss_does_not_decline_and_is_private(self):
        invitation=GameInvitation.objects.create(creator=self.other,opponent=self.user,opponent_mode='direct',creator_color='white')
        self.assertEqual(len(self.payload()['invitations']),1)
        self.assertEqual(self.dismiss(f'invite:{invitation.pk}').status_code,200)
        self.assertEqual(self.payload()['invitations'],[])
        invitation.refresh_from_db();self.assertEqual(invitation.status,'pending')
        self.client.force_login(self.stranger)
        self.assertEqual(self.dismiss(f'invite:{invitation.pk}').status_code,404)
    def test_guest_random_invitation_and_personal_invite_priority(self):
        GameInvitation.objects.create(creator_guest_name='Guest rival',opponent_mode='random',creator_color='white')
        direct=GameInvitation.objects.create(creator=self.other,opponent=self.user,opponent_mode='direct',creator_color='white')
        invitations=self.payload()['invitations']
        self.assertEqual(invitations[0]['id'],direct.pk)
        self.assertEqual(invitations[1]['creator'],'Guest rival')
