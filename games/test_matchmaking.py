from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import ChessGame, GameInvitation
from .matchmaking import start_search, match_search

class MatchmakingTests(TestCase):
    def setUp(self):
        self.a=User.objects.create_user('queue_a')
        self.b=User.objects.create_user('queue_b')
        self.client.force_login(self.a)
    def search(self,user,**changes):
        return start_search(user,**dict(dict(color='random',rated=False,blindfold=False,minutes=5),**changes))
    def test_matching_creates_one_shared_game_and_preserves_color(self):
        first=self.search(self.a)
        second=self.search(self.b,color='white')
        matched=match_search(self.b,second.pk)
        first.refresh_from_db()
        self.assertEqual(first.game_id,matched.game_id)
        self.assertEqual(ChessGame.objects.count(),1)
        self.assertEqual(matched.game.white_user,self.b)
        self.assertEqual(matched.game.black_user,self.a)
        self.assertEqual(matched.game.time_control_minutes,5)
        self.assertIsNone(matched.game.clock_started_at)
        match_search(self.b,second.pk)
        self.assertEqual(ChessGame.objects.count(),1)
    def test_incompatible_rules_and_same_color_never_match(self):
        for different in [dict(minutes=3),dict(rated=True),dict(blindfold=True),dict(color='white')]:
            GameInvitation.objects.all().delete()
            first=self.search(self.a,color='white')
            second=self.search(self.b,**different)
            self.assertIsNone(match_search(self.b,second.pk).game_id)
        self.assertEqual(ChessGame.objects.count(),0)
    def test_stale_and_cancelled_searches_are_not_opponents(self):
        first=self.search(self.a)
        GameInvitation.objects.filter(pk=first.pk).update(search_seen_at=timezone.now()-timedelta(minutes=1))
        second=self.search(self.b)
        self.assertIsNone(match_search(self.b,second.pk).game_id)
        GameInvitation.objects.filter(pk=first.pk).update(status='cancelled',search_seen_at=timezone.now())
        self.assertIsNone(match_search(self.b,second.pk).game_id)
    def test_duplicate_search_reuses_and_changed_rules_cancel_previous(self):
        first=self.search(self.a)
        self.assertEqual(first.pk,self.search(self.a).pk)
        second=self.search(self.a,minutes=10)
        first.refresh_from_db()
        self.assertEqual(first.status,'cancelled')
        self.assertNotEqual(first.pk,second.pk)
        self.assertIsNone(match_search(self.a,second.pk).game_id)
    def test_endpoint_is_post_only_and_owner_only(self):
        first=self.search(self.a)
        url=reverse('search_tick',args=[first.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url).status_code,200)
        self.client.force_login(self.b)
        self.assertEqual(self.client.post(url).status_code,404)
        self.client.logout()
        self.assertEqual(self.client.post(url).status_code,302)
    def test_oldest_search_resumes_and_both_players_open_same_game(self):
        first=self.search(self.a)
        second=self.search(self.b)
        match_search(self.a,first.pk)
        matched=match_search(self.b,second.pk)
        response=self.client.get(reverse('game_invitation_wait',args=[first.pk]))
        self.assertRedirects(response,reverse('game_detail',args=[matched.game_id]))
    def test_pending_search_visible_only_to_its_owner(self):
        first=self.search(self.a)
        response=self.client.get(reverse('games_list'))
        self.assertEqual(response.context['pending_search'],first)
        self.client.force_login(self.b)
        self.assertIsNone(self.client.get(reverse('games_list')).context['pending_search'])
    def test_game_creation_matches_existing_compatible_search(self):
        self.search(self.b)
        response=self.client.post(reverse('game_create'),{'opponent_mode':'random','color_choice':'random','game_type':'casual','time_control_minutes':'5'})
        game=ChessGame.objects.get()
        self.assertRedirects(response,reverse('game_detail',args=[game.pk]))
    def test_old_manual_invitation_is_not_automatically_matched(self):
        GameInvitation.objects.create(creator=self.a,opponent_mode='random',creator_color='random',time_control_minutes=5)
        second=self.search(self.b)
        self.assertIsNone(match_search(self.b,second.pk).game_id)
    def test_languages_and_waiting_page_keep_translated_client_messages(self):
        from .i18n import ui_texts
        first=self.search(self.a)
        for lang in ('es','pt','en'):
            session=self.client.session;session['language']=lang;session.save()
            response=self.client.get(reverse('game_invitation_wait',args=[first.pk]))
            self.assertEqual(response.status_code,200)
            self.assertIn('search_connection_retry',ui_texts(lang))
            self.assertContains(response,reverse('search_tick',args=[first.pk]))

    def test_anonymous_cannot_inspect_or_cancel_registered_search(self):
        first=self.search(self.a)
        anonymous=Client()
        for name in ('game_invitation_wait','invitation_status'):
            self.assertEqual(anonymous.get(reverse(name,args=[first.pk])).status_code,404)
        self.assertEqual(anonymous.post(reverse('cancel_invitation',args=[first.pk])).status_code,404)
        first.refresh_from_db()
        self.assertEqual(first.status,'pending')

    def test_csrf_required_on_search_tick(self):
        first=self.search(self.a)
        protected=Client(enforce_csrf_checks=True)
        protected.force_login(self.a)
        self.assertEqual(protected.post(reverse('search_tick',args=[first.pk])).status_code,403)
