from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password,check_password
from django.core.cache import cache
from django.urls import reverse
from .models import Tournament,TournamentEntry,TournamentNotice,Friendship


class TournamentVisibilityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner=User.objects.create_user('cup_host')
        self.friend=User.objects.create_user('cup_friend')
        self.stranger=User.objects.create_user('cup_stranger')
        self.cup=Tournament.objects.create(creator=self.owner,name='Secret cup',password_hash=make_password('demo-cup-pass'),max_players=4)
        TournamentEntry.objects.create(tournament=self.cup,user=self.owner)
        self.action=reverse('tournament_action',args=[self.cup.token]);self.detail=reverse('tournament_detail',args=[self.cup.token])
        self.client.force_login(self.stranger)

    def test_private_roster_hidden_and_password_enforced(self):
        TournamentEntry.objects.create(tournament=self.cup,user=self.friend)
        response=self.client.get(self.detail)
        self.assertTemplateUsed(response,'games/tournament_locked.html')
        self.assertNotContains(response,self.friend.username)
        self.assertNotContains(response,self.cup.password_hash)
        for password in ('','wrong'):
            self.assertIn('wrong_password',self.client.post(self.action,{'action':'join','password':password}).url)
        self.assertFalse(self.cup.entries.filter(user=self.stranger).exists())
        self.client.post(self.action,{'action':'join','password':'demo-cup-pass'})
        self.assertTrue(self.cup.entries.filter(user=self.stranger).exists())
        self.assertTemplateUsed(self.client.get(self.detail),'games/tournament_detail.html')
        self.assertEqual(self.client.post(self.action,{'action':'join'}).status_code,302)
        self.assertEqual(self.cup.entries.count(),3)

    def test_friend_invitation_never_bypasses_password(self):
        Friendship.objects.create(low_user=self.owner,high_user=self.friend,requester=self.owner,status='accepted')
        self.client.force_login(self.owner);self.client.post(self.action,{'action':'invite','friend_id':self.friend.pk})
        self.assertTrue(TournamentNotice.objects.filter(user=self.friend).exists())
        self.client.force_login(self.friend)
        self.assertIn('wrong_password',self.client.post(self.action,{'action':'join'}).url)
        self.client.post(self.action,{'action':'join','password':'demo-cup-pass'})
        self.assertTrue(self.cup.entries.filter(user=self.friend).exists())

    def test_public_discovery_counts_every_player_and_keeps_privates_hidden(self):
        public=Tournament.objects.create(creator=self.owner,name='Open cup',visibility='public')
        TournamentEntry.objects.create(tournament=public,user=self.owner)
        TournamentEntry.objects.create(tournament=public,user=self.friend)
        response=self.client.get(reverse('tournaments'))
        self.assertContains(response,'Open cup');self.assertNotContains(response,'Secret cup')
        self.assertEqual(response.context['public_tournaments'][0].player_count,2)
        self.client.post(reverse('tournament_action',args=[public.token]),{'action':'join'})
        response=self.client.get(reverse('tournaments'))
        self.assertEqual(response.context['tournaments'][0].player_count,3)
        self.assertEqual(self.client.get(reverse('tournament_detail',args=[public.token])).status_code,200)

    def test_creation_requires_private_password_and_never_renders_or_stores_raw(self):
        self.client.force_login(self.owner);url=reverse('tournament_create')
        base=dict(name='New protected cup',visibility='private',max_players=8,time_control_minutes=10)
        for password in ('','abc','      '):
            response=self.client.post(url,dict(base,password=password));self.assertEqual(response.status_code,200)
            self.assertFalse(Tournament.objects.filter(name=base['name']).exists())
        raw='synthetic-private-pass'
        response=self.client.post(url,dict(base,password=raw));self.assertEqual(response.status_code,302)
        cup=Tournament.objects.get(name=base['name']);self.assertTrue(check_password(raw,cup.password_hash));self.assertNotEqual(raw,cup.password_hash)
        self.assertNotContains(self.client.get(response.url),raw)
        response=self.client.post(url,dict(base,name='Public created',visibility='public',password='x'))
        self.assertEqual(response.status_code,302);self.assertEqual(Tournament.objects.get(name='Public created').password_hash,'')

    def test_legacy_lobby_requires_owner_setup_and_keeps_existing_members(self):
        self.cup.password_hash='';self.cup.save()
        self.assertIn('wrong_password',self.client.post(self.action,{'action':'join','password':'whatever'}).url)
        self.assertEqual(self.client.post(self.action,{'action':'password','password':'other-pass'}).status_code,403)
        self.client.force_login(self.owner)
        TournamentEntry.objects.create(tournament=self.cup,user=self.friend)
        self.assertIn('password_required',self.client.post(self.action,{'action':'start'}).url)
        self.client.post(self.action,{'action':'password','password':'updated-demo-pass'})
        self.cup.refresh_from_db();self.assertTrue(check_password('updated-demo-pass',self.cup.password_hash))
        self.client.force_login(self.friend);self.assertTemplateUsed(self.client.get(self.detail),'games/tournament_detail.html')
        self.assertEqual(self.client.post(self.action,{'action':'join'}).status_code,302)

    def test_closed_full_and_leaving_preserve_enrollment_rules(self):
        self.client.post(self.action,{'action':'join','password':'demo-cup-pass'})
        self.client.post(self.action,{'action':'leave'})
        self.assertIn('wrong_password',self.client.post(self.action,{'action':'join'}).url)
        self.cup.max_players=2;self.cup.save();TournamentEntry.objects.create(tournament=self.cup,user=self.friend)
        self.assertIn('notice=full',self.client.post(self.action,{'action':'join','password':'demo-cup-pass'}).url)
        self.client.force_login(self.owner);self.client.post(self.action,{'action':'start'})
        self.client.force_login(self.stranger)
        self.assertIn('notice=closed',self.client.post(self.action,{'action':'join','password':'demo-cup-pass'}).url)
        self.assertEqual(self.client.get(reverse('tournament_state',args=[self.cup.token])).status_code,403)

    def test_password_attempts_are_rate_limited_and_csrf_protected(self):
        for _ in range(8):self.assertEqual(self.client.post(self.action,{'action':'join','password':'wrong'}).status_code,302)
        self.assertEqual(self.client.post(self.action,{'action':'join','password':'demo-cup-pass'}).status_code,429)
        client=Client(enforce_csrf_checks=True);client.force_login(self.friend)
        self.assertEqual(client.post(self.action,{'action':'join','password':'demo-cup-pass'}).status_code,403)

    def test_public_filters_and_pagination_are_bounded(self):
        Tournament.objects.bulk_create([Tournament(creator=self.owner,name='Discover '+str(i),visibility='public') for i in range(15)])
        active=Tournament.objects.create(creator=self.owner,name='Active public',visibility='public',status='active')
        response=self.client.get(reverse('tournaments'));self.assertEqual(len(response.context['public_tournaments']),12)
        response=self.client.get(reverse('tournaments'),{'page':2});self.assertEqual(len(response.context['public_tournaments']),3)
        response=self.client.get(reverse('tournaments'),{'status':'active'});self.assertContains(response,'Active public');self.assertNotContains(response,'Discover 1')
        response=self.client.get(reverse('tournaments'),{'status':'invalid'});self.assertEqual(response.context['public_status'],'lobby')

    def test_public_standings_visible_without_granting_game_access(self):
        self.cup.visibility='public';self.cup.password_hash='';self.cup.save()
        TournamentEntry.objects.create(tournament=self.cup,user=self.friend)
        self.client.force_login(self.owner);self.client.post(self.action,{'action':'start'})
        self.client.force_login(self.stranger)
        response=self.client.get(self.detail)
        self.assertTrue(response.context['table'])
        self.assertContains(response,self.friend.username)
        game=self.cup.matches.get(round_number=1).game
        self.assertNotContains(response,reverse('game_detail',args=[game.pk]))
        self.assertEqual(self.client.get(reverse('game_detail',args=[game.pk])).status_code,404)
