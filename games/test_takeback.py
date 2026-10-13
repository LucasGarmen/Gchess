import json
from datetime import timedelta
import chess
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase,Client
from django.utils import timezone
from .models import ChessGame,Move
from .views import board_from_game_moves,piece_type_name

class TakebackTests(TestCase):
    def setUp(self):
        cache.clear()
        self.white=User.objects.create_user('undo_white');self.black=User.objects.create_user('undo_black')
        self.game=ChessGame.objects.create(owner=self.white,white_user=self.white,black_user=self.black,white_player='W',black_player='B')
        self.client.force_login(self.white);self.other=Client();self.other.force_login(self.black)
        self.url=f'/games/{self.game.pk}/takeback/'
        self.add_moves(['e2e4'])
    def add_moves(self,ucis):
        board,_=board_from_game_moves(self.game)
        for uci in ucis:
            move=chess.Move.from_uci(uci);piece=board.piece_at(move.from_square)
            Move.objects.create(game=self.game,move_number=self.game.moves.count()+1,from_square=uci[:2],to_square=uci[2:4],piece_type=piece_type_name(piece),piece_color='white' if piece.color else 'black',promotion='queen' if len(uci)>4 else None)
            board.push(move)
    def post(self,client,action,move_id=None):
        if action=='request' and move_id is None: move_id=self.game.moves.order_by('-move_number','-id').first().pk
        return client.post(self.url,json.dumps({'action':action,'move_id':move_id}),content_type='application/json')
    def test_only_opponent_can_accept_and_only_once(self):
        offer=self.post(self.client,'request').json()
        self.assertEqual(self.game.moves.count(),1)
        self.assertEqual(self.post(self.client,'accept',offer['move_id']).status_code,403)
        response=self.post(self.other,'accept',offer['move_id'])
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['state']['move_count'],0)
        self.assertEqual(response.json()['state']['turn'],'white')
        self.assertEqual(self.post(self.other,'accept',offer['move_id']).status_code,409)
    def test_rejection_preserves_board(self):
        offer=self.post(self.client,'request').json()
        self.assertEqual(self.post(self.other,'reject',offer['move_id']).status_code,200)
        self.assertEqual(self.game.moves.count(),1)
        self.assertEqual(self.post(self.other,'accept',offer['move_id']).status_code,409)
    def test_new_move_invalidates_request(self):
        offer=self.post(self.client,'request').json();self.add_moves(['e7e5'])
        self.assertFalse(self.other.get(self.url).json()['pending'])
        self.assertEqual(self.post(self.other,'accept',offer['move_id']).status_code,409)
        self.assertEqual(self.game.moves.count(),2)
    def test_outsider_and_finished_game(self):
        outsider=Client();outsider.force_login(User.objects.create_user('undo_outsider'))
        self.assertEqual(self.post(outsider,'request').status_code,404)
        self.game.status='finished';self.game.save()
        self.assertEqual(self.post(self.client,'request').status_code,409)
        self.assertEqual(self.game.moves.count(),1)
    def test_guest_accepts(self):
        self.game.black_user=None;self.game.black_guest_id='undo_guest';self.game.save()
        guest=Client();session=guest.session;session['guest_id']='undo_guest';session.save()
        offer=self.post(self.client,'request').json()
        self.assertEqual(self.post(guest,'accept',offer['move_id']).status_code,200)
    def test_clock_time_is_not_refunded(self):
        self.game.time_control_minutes=5;self.game.white_time_seconds=300;self.game.black_time_seconds=300
        self.game.active_clock_color='black';self.game.clock_started_at=timezone.now()-timedelta(seconds=10);self.game.save()
        offer=self.post(self.client,'request').json();self.post(self.other,'accept',offer['move_id'])
        self.game.refresh_from_db();self.assertLessEqual(self.game.black_time_seconds,290)
        self.assertEqual(self.game.active_clock_color,'white')
    def test_castling_is_rebuilt_correctly(self):
        self.add_moves(['e7e5','g1f3','b8c6','f1c4','g8f6','e1g1'])
        offer=self.post(self.client,'request').json();self.post(self.other,'accept',offer['move_id'])
        board,_=board_from_game_moves(self.game)
        self.assertEqual(board.piece_at(chess.E1).piece_type,chess.KING)
        self.assertEqual(board.piece_at(chess.H1).piece_type,chess.ROOK)
        self.assertTrue(board.has_kingside_castling_rights(chess.WHITE))
    def test_en_passant_is_rebuilt_correctly(self):
        self.add_moves(['a7a6','e4e5','d7d5','e5d6'])
        offer=self.post(self.client,'request').json();self.post(self.other,'accept',offer['move_id'])
        board,_=board_from_game_moves(self.game)
        self.assertEqual(board.piece_at(chess.E5).piece_type,chess.PAWN)
        self.assertEqual(board.piece_at(chess.D5).piece_type,chess.PAWN)
        self.assertEqual(board.ep_square,chess.D6)
