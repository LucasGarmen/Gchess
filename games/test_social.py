from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from .models import Friendship, GameInvitation, ChessGame


class FriendsTests(TestCase):
    def setUp(self):
        self.a=User.objects.create_user('alice',email='secret-alice@example.com',password='test-pass')
        self.b=User.objects.create_user('bob',password='test-pass')
        self.c=User.objects.create_user('carol',password='test-pass')
        self.client.force_login(self.a)
        session=self.client.session;session['language']='es';session.save()

    def action(self, target, action):
        return self.client.post(reverse('friend_action',args=[target.pk]),{'action':action})

    def accepted(self):
        return Friendship.objects.create(low_user=self.a,high_user=self.b,requester=self.a,status='accepted')

    def test_request_needs_recipient_acceptance(self):
        self.assertEqual(self.action(self.b,'send').status_code,302)
        self.assertEqual(self.action(self.b,'send').status_code,302)
        self.assertEqual(Friendship.objects.count(),1)
        self.assertEqual(self.action(self.b,'accept').status_code,400)
        self.client.force_login(self.b)
        self.assertEqual(self.action(self.a,'accept').status_code,302)
        self.assertEqual(Friendship.objects.get().status,'accepted')

    def test_opposite_requests_do_not_implicitly_accept(self):
        self.action(self.b,'send');self.client.force_login(self.b);self.action(self.a,'send')
        self.assertEqual(Friendship.objects.count(),1)
        self.assertEqual(Friendship.objects.get().status,'pending')

    def test_third_party_cannot_modify_pair(self):
        self.accepted();self.client.force_login(self.c)
        self.assertEqual(self.action(self.a,'remove').status_code,400)
        self.assertEqual(self.action(self.a,'accept').status_code,400)
        self.assertEqual(Friendship.objects.get().status,'accepted')

    def test_self_get_and_csrf_rejected(self):
        self.assertEqual(self.action(self.a,'send').status_code,400)
        self.assertEqual(self.client.get(reverse('friend_action',args=[self.b.pk])).status_code,405)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.a)
        self.assertEqual(secure.post(reverse('friend_action',args=[self.b.pk]),{'action':'send'}).status_code,403)

    def test_decline_cancel_and_remove_authorization(self):
        self.action(self.b,'send');self.assertEqual(self.action(self.b,'decline').status_code,400)
        self.assertEqual(self.action(self.b,'cancel').status_code,302)
        self.action(self.b,'send');self.client.force_login(self.b)
        self.assertEqual(self.action(self.a,'cancel').status_code,400)
        self.assertEqual(self.action(self.a,'decline').status_code,302)
        self.accepted();self.assertEqual(self.action(self.a,'remove').status_code,302)
        self.assertFalse(Friendship.objects.exists())

    def test_constraints_reject_duplicate_self_or_nonmember(self):
        self.accepted()
        for values in [dict(low_user=self.a,high_user=self.b,requester=self.a),dict(low_user=self.a,high_user=self.a,requester=self.a),dict(low_user=self.b,high_user=self.c,requester=self.a)]:
            with self.assertRaises(IntegrityError),transaction.atomic():Friendship.objects.create(**values)

    def test_friends_page_search_and_privacy(self):
        response=self.client.get(reverse('friends'),{'q':'ali'})
        self.assertNotContains(response,'secret-alice@example.com')
        response=self.client.get(reverse('friends'),{'q':'bo'})
        self.assertContains(response,'bob');self.assertContains(response,'Agregar amigo')
        self.a.is_active=False;self.a.save();self.client.force_login(self.b)
        self.assertNotContains(self.client.get(reverse('friends'),{'q':'ali'}),'alice')

    def test_rankings_only_friends_and_separate_records(self):
        from accounts.models import UserPuzzleStats
        from .models import BlitzBestResult, StreakBestResult
        self.accepted()
        UserPuzzleStats.objects.update_or_create(user=self.b,defaults={'puzzle_rating':900})
        BlitzBestResult.objects.create(user=self.b,score=77)
        StreakBestResult.objects.create(user=self.b,mejor_racha=8)
        for metric,value in [('puzzles',900),('blitz',77),('streak',8)]:
            response=self.client.get(reverse('friends'),{'metric':metric})
            rows=response.context['ranking'];self.assertEqual({r['user'].pk for r in rows},{self.a.pk,self.b.pk})
            self.assertEqual(next(r['value'] for r in rows if r['user']==self.b),value)
        self.assertEqual(self.client.get(reverse('friends'),{'metric':'email'}).context['metric'],'puzzles')

    def test_history_handles_both_colors_and_draws(self):
        self.accepted()
        for white,black,result in [(self.a,self.b,'white'),(self.b,self.a,'black'),(self.a,self.b,'black'),(self.b,self.a,'draw')]:
            ChessGame.objects.create(white_user=white,black_user=black,white_player=white.username,black_player=black.username,status='finished',result=result)
        self.assertEqual(self.client.get(reverse('friends')).context['friends'][0]['history'],dict(wins=2,losses=1,draws=1))

    def test_challenge_requires_friendship_and_valid_options(self):
        url=reverse('friend_challenge',args=[self.b.pk])
        self.assertEqual(self.client.post(url).status_code,400)
        self.accepted()
        self.assertEqual(self.client.post(url,{'minutes':'9999'}).status_code,400)
        self.assertEqual(self.client.post(url,{'kind':'anything'}).status_code,400)
        self.assertEqual(GameInvitation.objects.count(),0)

    def test_offline_friend_challenge_reuses_existing_game_flow(self):
        self.accepted();url=reverse('friend_challenge',args=[self.b.pk])
        data={'minutes':'5','kind':'ranked'}
        self.assertEqual(self.client.post(url,data).status_code,302)
        self.client.post(url,data);self.assertEqual(GameInvitation.objects.count(),1)
        invitation=GameInvitation.objects.get();self.assertTrue(invitation.is_rated)
        self.assertEqual(invitation.opponent,self.b)
        self.client.force_login(self.b)
        response=self.client.post(reverse('accept_invitation',args=[invitation.pk]))
        self.assertEqual(response.status_code,200)
        invitation.refresh_from_db();game=invitation.game
        self.assertIsNotNone(game);self.assertIsNone(game.clock_started_at)
        self.assertEqual({game.white_user_id,game.black_user_id},{self.a.pk,self.b.pk})

    def test_login_and_three_languages(self):
        self.client.logout();self.assertEqual(self.client.get(reverse('friends')).status_code,302)
        self.client.force_login(self.a)
        for lang,title in [('es','Amigos'),('pt','Amigos'),('en','Friends')]:
            session=self.client.session;session['language']=lang;session.save()
            self.assertContains(self.client.get(reverse('friends')),title)
