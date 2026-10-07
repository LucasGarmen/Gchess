from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from games.models import ChessGame, Move

class WorkspaceTests(TestCase):
    def test_multiple_games_private_and_read_only(self):
        user=User.objects.create_user('workspace-owner')
        rival=User.objects.create_user('workspace-rival')
        outsider=User.objects.create_user('workspace-outsider')
        first=ChessGame.objects.create(white_user=user, black_user=rival,white_player=user.username,black_player=rival.username)
        second=ChessGame.objects.create(white_user=rival,black_user=user,white_player=rival.username,black_player=user.username)
        ChessGame.objects.create(owner=user,white_user=rival,black_user=outsider,white_player='other',black_player='other')
        ChessGame.objects.create(white_user=user,status='finished',white_player='done',black_player='done')
        Move.objects.create(game=second,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')
        self.client.force_login(user)
        response=self.client.get(reverse('active_games'))
        self.assertEqual(response.status_code,200)
        games={g['id']:g for g in response.json()['games']}
        self.assertEqual(set(games),{first.pk,second.pk})
        self.assertTrue(games[first.pk]['yourTurn'])
        self.assertTrue(games[second.pk]['yourTurn'])
        self.assertIn('no-store',response['Cache-Control'])
        self.assertEqual(self.client.post(reverse('active_games')).status_code,405)
        self.assertEqual(ChessGame.objects.filter(status='draft').count(),3)

    def test_guests_only_see_their_own_games(self):
        a,b=Client(),Client()
        actor=a.get(reverse('active_games')).json()['actor']
        guest=actor.split(':',1)[1]
        game=ChessGame.objects.create(white_guest_id=guest,black_guest_id='unrelated',white_player='guest',black_player='rival')
        self.assertEqual([g['id'] for g in a.get(reverse('active_games')).json()['games']],[game.pk])
        self.assertEqual(b.get(reverse('active_games')).json()['games'],[])
        page=a.get(reverse('home'))
        self.assertContains(page,'game-workspace-config')
        self.assertContains(page,'workspace-new-bot')


class CoachStorageNoticeTests(TestCase):
    def test_temporary_storage_notice_translated_for_guests_and_accounts(self):
        from games.workspace import EXIT_TEXTS
        user=User.objects.create_user('coach-storage-owner')
        for authenticated in (False,True):
            if authenticated: self.client.force_login(user)
            for language in ('es','pt','en'):
                session=self.client.session;session['language']=language;session.save()
                response=self.client.get(reverse('home'))
                self.assertContains(response,EXIT_TEXTS[language]['storage'])
                self.assertContains(response,'logoutWarning')
                self.assertContains(response,'workspace.js')
            self.assertFalse(ChessGame.objects.exists())
