from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.test import TestCase, RequestFactory
from django.utils import timezone
from .models import ChessGame, Move, GameReview, GameExperienceEvent, PlayerActivityDay, DailyVisit
from .experience_metrics import record_game, retention_summary
from .middleware import DailyVisitMiddleware, PlayerActivityMiddleware

class OptimizationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=User.objects.create_user('metrics-one')
        self.other=User.objects.create_user('metrics-two')
        self.factory=RequestFactory()

    def start_game(self):
        with self.captureOnCommitCallbacks(execute=True):
            game=ChessGame.objects.create(white_user=self.user,black_user=self.other,white_player='A',black_player='B')
            Move.objects.create(game=game,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')
        return game

    def test_verified_start_finish_review_and_next_game(self):
        game=self.start_game()
        self.assertEqual(GameExperienceEvent.objects.filter(kind='started').count(),2)
        with self.captureOnCommitCallbacks(execute=True):
            game.status='finished';game.result='draw';game.save(update_fields=['status','result'])
            game.save(update_fields=['result'])
        self.assertEqual(GameExperienceEvent.objects.filter(kind='finished').count(),2)
        with self.captureOnCommitCallbacks(execute=True):
            for language in ('pt','es'):
                GameReview.objects.create(user=self.user,game=game,fingerprint='review',language=language,player_color='white',pgn='1. e4 *',payload={})
        self.assertEqual(GameExperienceEvent.objects.filter(kind='reviewed').count(),1)
        self.start_game()
        totals=retention_summary(timezone.localdate(),timezone.localdate())
        self.assertEqual((totals['started'],totals['finished'],totals['reviewed'],totals['again']),(2,2,1,2))
        self.assertEqual((totals['started_games'],totals['finished_games']),(2,1))

    def test_no_history_backfill_or_staff_tracking(self):
        game=ChessGame.objects.create(white_user=self.user,white_player='A',black_player='B',status='finished',result='draw')
        Move.objects.bulk_create([Move(game=game,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')])
        with self.captureOnCommitCallbacks(execute=True):game.save()
        self.assertFalse(GameExperienceEvent.objects.exists())
        self.other.is_staff=True;self.other.save()
        live=self.start_game()
        self.assertEqual(GameExperienceEvent.objects.filter(game=live).count(),1)
        record_game(live.pk,'started')
        self.assertEqual(GameExperienceEvent.objects.filter(game=live).count(),1)

    def test_rolled_back_game_does_not_record_metrics(self):
        from django.db import transaction
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    game=ChessGame.objects.create(white_user=self.user,white_player='A',black_player='B')
                    Move.objects.create(game=game,move_number=1,from_square='e2',to_square='e4',piece_type='pawn',piece_color='white')
                    raise ValueError('rollback')
            except ValueError:pass
        self.assertFalse(GameExperienceEvent.objects.exists())

    def test_json_polling_does_not_inflate_page_visits(self):
        request=self.factory.get('/rewards/progress/')
        middleware=DailyVisitMiddleware(lambda request:JsonResponse({'total':0}))
        middleware(request)
        self.assertFalse(DailyVisit.objects.exists())
        middleware=DailyVisitMiddleware(lambda request:HttpResponse('Page'))
        middleware(request)
        self.assertEqual(DailyVisit.objects.get().visits,1)

    def test_activity_cache_avoids_repeated_database_lookup(self):
        request=self.factory.get('/training/');request.user=self.user
        middleware=PlayerActivityMiddleware(lambda request:HttpResponse('Page'))
        with patch('games.views.touch_presence'):
            middleware(request)
            with self.assertNumQueries(0):middleware(request)
        self.assertEqual(PlayerActivityDay.objects.filter(user=self.user).count(),1)
