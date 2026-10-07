import json
import chess
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from .blindfold import parse_move, local_san
from .models import ChessGame, GameInvitation, Move, UserPresence
from .views import create_game_from_invitation


class BlindfoldNotationTests(SimpleTestCase):
    def test_coordinates_and_local_knight_names(self):
        for text, language in [('e4','es'), ('e2e4','pt'), ('Cf3','es'), ('Cf3','pt'), ('Nf3','en')]:
            expected='g1f3' if 'f3' in text else 'e2e4'
            self.assertEqual(parse_move(chess.Board(),text,language).uci(),expected)
        self.assertEqual(local_san('Nf3','es'),'Cf3')
        self.assertEqual(local_san('Bb5','pt'),'Bb5')
        self.assertEqual(local_san('Rae1','es'),'Tae1')

    def test_castling_en_passant_and_promotion(self):
        board=chess.Board('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
        self.assertEqual(parse_move(board,'0-0','es').uci(),'e1g1')
        board=chess.Board('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1')
        self.assertEqual(parse_move(board,'exd6','es').uci(),'e5d6')
        board=chess.Board('4k3/P7/8/8/8/8/8/4K3 w - - 0 1')
        for text in ('a8=D+', 'a7a8q'):
            self.assertEqual(parse_move(board,text,'es').uci(),'a7a8q')
        self.assertEqual(local_san('a8=Q+','pt'),'a8=D+')

    def test_ambiguous_illegal_and_null_moves_are_rejected(self):
        board=chess.Board('4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1')
        with self.assertRaises(ValueError): parse_move(board,'Cd2','es')
        self.assertEqual(parse_move(board,'Cbd2','es').uci(),'b1d2')
        for text in ('e2e5','--','0000','', 'a'*33):
            with self.subTest(text=text), self.assertRaises(ValueError): parse_move(chess.Board(),text,'es')


class BlindfoldGameTests(TestCase):
    def setUp(self):
        cache.clear()
        self.white=User.objects.create_user('blind-white')
        self.black=User.objects.create_user('blind-black')
        self.other=User.objects.create_user('blind-other')
        self.client.force_login(self.white)
        session=self.client.session; session['language']='es'; session.save()
        self.game=ChessGame.objects.create(owner=self.white,white_user=self.white,black_user=self.black,
            white_player=self.white.username,black_player=self.black.username,blindfold_only=True)

    def post(self,data):
        return self.client.post(reverse('blindfold_position'),json.dumps(data),content_type='application/json')

    def test_coach_parser_uses_saved_moves_and_returns_history(self):
        response=self.post({'moves':['e2e4','e7e5'],'notation':'Cf3'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['history'],['e4','e5'])
        self.assertEqual(response.json()['move']['from'],'g1')
        self.assertEqual(response.json()['move_count'],2)
        self.assertEqual(Move.objects.count(),0)

    def test_human_move_reuses_authoritative_save_and_turn_checks(self):
        response=self.post({'game_id':self.game.pk,'notation':'e4','moves':['a2a4']})
        self.assertEqual(response.status_code,200)
        data=response.json()['move']
        saved=self.client.post(reverse('save_move',args=[self.game.pk]),json.dumps(data),content_type='application/json')
        self.assertEqual(saved.status_code,200)
        self.assertEqual(self.game.moves.count(),1)
        # Even with valid notation, white cannot submit black's response.
        response=self.post({'game_id':self.game.pk,'notation':'e5'})
        saved=self.client.post(reverse('save_move',args=[self.game.pk]),json.dumps(response.json()['move']),content_type='application/json')
        self.assertEqual(saved.status_code,403)
        self.client.force_login(self.black)
        saved=self.client.post(reverse('save_move',args=[self.game.pk]),json.dumps(response.json()['move']),content_type='application/json')
        self.assertEqual(saved.status_code,200)
        self.assertEqual(self.game.moves.count(),2)

    def test_private_game_position_does_not_accept_unrelated_users(self):
        self.client.force_login(self.other)
        self.assertEqual(self.post({'game_id':self.game.pk,'notation':'e4'}).status_code,404)

    def test_invalid_notation_returns_translated_error_without_writing(self):
        response=self.post({'game_id':self.game.pk,'notation':'e2e5'})
        self.assertEqual(response.status_code,400)
        self.assertIn('jugada legal',response.json()['error'])
        self.assertEqual(self.game.moves.count(),0)
        self.game.status='finished'; self.game.save()
        self.assertEqual(self.post({'game_id':self.game.pk,'notation':'e4'}).status_code,409)

    def test_exclusive_link_invitation_carries_mode_to_both_players(self):
        response=self.client.post(reverse('game_create'),{'opponent_mode':'link','game_type':'casual','color_choice':'white','blindfold_only':'on'})
        self.assertEqual(response.status_code,302)
        invitation=GameInvitation.objects.get(creator=self.white)
        self.assertTrue(invitation.blindfold_only)
        game=create_game_from_invitation(invitation,self.black)
        self.assertTrue(game.blindfold_only)
        self.assertContains(self.client.get(reverse('game_detail',args=[game.pk])), 'data-exclusive="true"')
        self.client.force_login(self.black)
        self.assertContains(self.client.get(reverse('game_detail',args=[game.pk])), 'data-exclusive="true"')
        self.assertTrue(self.client.get(reverse('active_games')).json()['games'][0]['blindfoldOnly'])

    def test_normal_invitation_and_exclusive_entry_form(self):
        response=self.client.post(reverse('game_create'),{'opponent_mode':'link','game_type':'casual','color_choice':'white'})
        self.assertEqual(response.status_code,302)
        invitation=GameInvitation.objects.get(creator=self.white)
        self.assertFalse(invitation.blindfold_only)
        self.assertFalse(create_game_from_invitation(invitation,self.black).blindfold_only)
        response=self.client.get(reverse('game_create')+'?blindfold=exclusive')
        self.assertTrue(response.context['form']['blindfold_only'].value())
        self.assertContains(self.client.get(reverse('blindfold')), 'blindfold=exclusive')

    def test_random_and_direct_invitations_keep_exclusive_mode(self):
        UserPresence.objects.create(user=self.black)
        for mode in ('random','choose'):
            response=self.client.post(reverse('game_create'),{'opponent_mode':mode,'opponent_name':self.black.username,
                'game_type':'casual','color_choice':'white','blindfold_only':'on'})
            self.assertEqual(response.status_code,302)
        self.assertEqual(GameInvitation.objects.filter(blindfold_only=True).count(),2)
        self.client.force_login(self.black)
        invitations=self.client.get(reverse('game_notifications')).json()['invitations']
        self.assertTrue(all(item['blindfold_only'] for item in invitations))

    def test_rematch_keeps_exclusive_mode(self):
        self.game.status='finished'; self.game.save()
        response=self.client.post(reverse('game_rematch',args=[self.game.pk]))
        self.assertEqual(response.status_code,302)
        self.assertTrue(GameInvitation.objects.get(rematch_of=self.game).blindfold_only)
