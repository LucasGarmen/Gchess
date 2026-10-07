from itertools import combinations
from django.test import TestCase, SimpleTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Tournament, TournamentEntry, TournamentMatch, ChessGame
from .tournaments import round_robin, advance_tournament, standings


class SchedulingTests(SimpleTestCase):
    def test_every_pair_plays_once_and_players_never_have_two_games_in_a_round(self):
        for n in range(2,17):
            players=list(range(1,n+1))
            rounds=round_robin(players)
            pairs=[];byes=[];colors={p:[0,0] for p in players}
            for round_matches in rounds:
                booked=[]
                for a,b in round_matches:
                    booked.append(a)
                    if b is not None:booked.append(b);pairs.append(tuple(sorted((a,b))));colors[a][0]+=1;colors[b][1]+=1
                    else:byes.append(a)
                self.assertEqual(sorted(booked),players)
            self.assertEqual(sorted(pairs),list(combinations(players,2)))
            self.assertEqual(sorted(byes),players if n%2 else [])
            self.assertTrue(all(abs(white-black)<=1 for white,black in colors.values()))


class TournamentTests(TestCase):
    def setUp(self):
        self.players=[User.objects.create_user(username='tour'+str(i)) for i in range(4)]
        self.host=self.players[0]
        self.tournament=Tournament.objects.create(creator=self.host,name='Friends cup',max_players=4)
        TournamentEntry.objects.create(tournament=self.tournament,user=self.host)
        self.action=reverse('tournament_action',args=[self.tournament.token])
        self.client.force_login(self.host)

    def enroll(self,count=4):
        for user in self.players[1:count]:TournamentEntry.objects.create(tournament=self.tournament,user=user)

    def start(self):
        self.client.post(self.action,{'action':'start'})
        self.tournament.refresh_from_db()

    def test_join_duplicate_capacity_and_only_host_can_start(self):
        self.client.force_login(self.players[1])
        self.client.post(self.action,{'action':'join'});self.client.post(self.action,{'action':'join'})
        self.assertEqual(self.tournament.entries.count(),2)
        self.assertEqual(self.client.post(self.action,{'action':'start'}).status_code,403)
        self.assertEqual(ChessGame.objects.count(),0)
        self.enroll_other=self.players[2:]
        for user in self.enroll_other:TournamentEntry.objects.create(tournament=self.tournament,user=user)
        stranger=User.objects.create_user('outsider')
        self.client.force_login(stranger)
        response=self.client.post(self.action,{'action':'join'})
        self.assertIn('notice=full',response.url)
        self.assertFalse(self.tournament.entries.filter(user=stranger).exists())

    def test_start_creates_only_first_round_and_initial_clocks_do_not_run(self):
        self.enroll();self.start();self.start()
        self.assertEqual(self.tournament.status,'active')
        self.assertEqual(self.tournament.matches.count(),6)
        self.assertEqual(ChessGame.objects.count(),2)
        for game in ChessGame.objects.all():
            self.assertFalse(game.is_rated)
            self.assertEqual(game.white_time_seconds,600)
            self.assertIsNone(game.clock_started_at)
        self.assertContains(self.client.get(reverse('tournament_detail',args=[self.tournament.token])),'Jogar minha partida')

    def test_results_advance_once_and_completion_sums_all_games(self):
        self.enroll();self.start()
        for number in (1,2,3):
            matches=list(self.tournament.matches.filter(round_number=number,black__isnull=False).select_related('game'))
            for index,match in enumerate(matches):
                with self.captureOnCommitCallbacks(execute=True):
                    match.game.status='finished';match.game.result='draw' if number==2 else 'white'
                    match.game.save(update_fields=['status','result'])
                self.tournament.refresh_from_db()
                if index==0:self.assertEqual(self.tournament.current_round,number)
            advance_tournament(self.tournament.pk)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status,'finished')
        self.assertEqual(ChessGame.objects.count(),6)
        table=standings(self.tournament,list(self.tournament.entries.select_related('user')),list(self.tournament.matches.select_related('game')))
        self.assertEqual(sum(row['points'] for row in table),12)
        self.assertEqual(sum(row['draws'] for row in table),4)

    def test_unknown_results_do_not_start_another_round(self):
        self.enroll();self.start()
        ChessGame.objects.update(status='finished',result='unknown')
        advance_tournament(self.tournament.pk)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.current_round,1)

    def test_nonmembers_cannot_poll_or_access_games_and_cannot_join_after_start(self):
        self.enroll(2);self.start()
        self.client.force_login(self.players[2])
        self.assertEqual(self.client.get(reverse('tournament_state',args=[self.tournament.token])).status_code,403)
        response=self.client.post(self.action,{'action':'join'})
        self.assertIn('notice=closed',response.url)
        game=ChessGame.objects.first()
        self.assertEqual(self.client.get(reverse('game_detail',args=[game.pk])).status_code,404)
        self.assertNotContains(self.client.get(reverse('tournament_detail',args=[self.tournament.token])),'tournament-live')

    def test_odd_players_bye_is_scored_once_and_all_share_place_on_equal_points(self):
        self.enroll(3);self.start()
        for number in (1,2,3):
            game=ChessGame.objects.get(tournament_match__tournament=self.tournament,tournament_match__round_number=number)
            with self.captureOnCommitCallbacks(execute=True):
                game.status='finished';game.result='draw';game.save(update_fields=['status','result'])
        self.tournament.refresh_from_db()
        table=standings(self.tournament,list(self.tournament.entries.select_related('user')),list(self.tournament.matches.select_related('game')))
        self.assertEqual([row['points'] for row in table],[4,4,4])
        self.assertEqual([row['rank'] for row in table],[1,1,1])
        self.assertEqual(ChessGame.objects.count(),3)

    def test_cancel_and_leave_are_allowed_only_before_start(self):
        self.enroll(2)
        self.client.force_login(self.players[1]);self.client.post(self.action,{'action':'leave'})
        self.assertEqual(self.tournament.entries.count(),1)
        self.client.force_login(self.host);self.client.post(self.action,{'action':'start'})
        self.tournament.refresh_from_db();self.assertEqual(self.tournament.status,'lobby')
        self.client.post(self.action,{'action':'cancel'})
        self.tournament.refresh_from_db();self.assertEqual(self.tournament.status,'cancelled')
        self.assertEqual(ChessGame.objects.count(),0)

    def test_private_list_and_form_validation(self):
        other=Tournament.objects.create(creator=self.players[1],name='Other private cup')
        TournamentEntry.objects.create(tournament=other,user=self.players[1])
        self.assertNotContains(self.client.get(reverse('tournaments')),'Other private cup')
        self.client.post(reverse('tournament_create'),{'name':'Bad','max_players':999,'time_control_minutes':999})
        self.assertEqual(Tournament.objects.count(),2)
        self.client.post(reverse('tournament_create'),{'name':'New cup','max_players':8,'time_control_minutes':5})
        self.assertTrue(TournamentEntry.objects.filter(tournament__name='New cup',user=self.host).exists())

    def test_resigning_the_normal_game_finishes_the_tournament(self):
        self.enroll(2);self.start()
        game=ChessGame.objects.first()
        with self.captureOnCommitCallbacks(execute=True):
            response=self.client.post(reverse('resign_game',args=[game.pk]),data='{}',content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status,'finished')
        game.refresh_from_db();self.assertEqual(game.result,'black')

    def test_actions_reject_missing_csrf_tokens(self):
        from django.test import Client
        protected=Client(enforce_csrf_checks=True)
        protected.force_login(self.host)
        self.assertEqual(protected.post(self.action,{'action':'cancel'}).status_code,403)
        self.tournament.refresh_from_db();self.assertEqual(self.tournament.status,'lobby')

    def test_clock_expiry_is_resolved_while_players_wait_on_standings(self):
        from django.utils import timezone
        self.enroll(2);self.start()
        game=ChessGame.objects.first()
        game.white_time_seconds=1;game.active_clock_color='white';game.clock_started_at=timezone.now()-timezone.timedelta(seconds=3)
        game.save(update_fields=['white_time_seconds','active_clock_color','clock_started_at'])
        with self.captureOnCommitCallbacks(execute=True):
            response=self.client.get(reverse('tournament_state',args=[self.tournament.token]))
        self.assertEqual(response.status_code,200)
        game.refresh_from_db();self.assertEqual(game.status,'finished');self.assertEqual(game.result,'black')
        self.tournament.refresh_from_db();self.assertEqual(self.tournament.status,'finished')


class TournamentNoticeTests(TournamentTests):
    def test_friend_invitation_permissions_and_private_notifications(self):
        from .models import Friendship, TournamentNotice
        friend=self.players[1]
        self.assertEqual(self.client.post(self.action,{'action':'invite','friend_id':friend.pk}).status_code,403)
        Friendship.objects.create(low_user=self.host,high_user=friend,requester=self.host,status='accepted')
        for _ in range(2):self.client.post(self.action,{'action':'invite','friend_id':friend.pk})
        self.assertEqual(TournamentNotice.objects.count(),1)
        self.assertEqual(self.client.get(reverse('game_notifications')).json()['tournament_notices'],[])
        self.client.force_login(friend)
        self.assertEqual(self.client.post(self.action,{'action':'invite','friend_id':self.host.pk}).status_code,403)
        notices=self.client.get(reverse('game_notifications')).json()['tournament_notices']
        self.assertEqual(len(notices),1)
        self.client.get(notices[0]['url'])
        self.assertEqual(len(self.client.get(reverse('game_notifications')).json()['tournament_notices']),1)
        self.client.post(self.action,{'action':'join'})
        self.client.get(notices[0]['url'])
        self.assertEqual(self.client.get(reverse('game_notifications')).json()['tournament_notices'],[])

    def test_round_notifications_are_unique_and_dismiss_is_recipient_only(self):
        from .models import TournamentNotice
        self.enroll();self.start();self.start()
        self.assertEqual(TournamentNotice.objects.filter(kind='round').count(),4)
        notice=TournamentNotice.objects.get(user=self.players[1],kind='round')
        url=reverse('tournament_notice_read',args=[notice.pk])
        self.assertEqual(self.client.post(url).status_code,404)
        self.client.force_login(self.players[1])
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url).status_code,200)
        self.assertEqual(self.client.get(reverse('game_notifications')).json()['tournament_notices'],[])

    def test_started_tournament_does_not_offer_old_invitation(self):
        from .models import TournamentNotice
        TournamentNotice.objects.create(tournament=self.tournament,user=self.players[3],kind='invite')
        self.enroll(2);self.start()
        self.client.force_login(self.players[3])
        self.assertEqual(self.client.get(reverse('game_notifications')).json()['tournament_notices'],[])
