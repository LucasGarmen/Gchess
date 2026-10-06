from datetime import timedelta
from unittest.mock import patch
import chess
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError,transaction
from django.test import Client,TestCase,SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from .models import ChessGame,GameInvitation,GameReview,Move
from .learning import build_review_summary,save_review
from .tests import FakeAnalysisEngine


def payload():
    moves=[dict(move_number=1,piece_color='white',san='e4'),dict(move_number=2,piece_color='black',san='e5'),dict(move_number=3,piece_color='white',san='Nf3')]
    analysis=[dict(move_number=1,san='e4',loss=0,classification='good',comment='Stable',engine_context={'game_phase':'opening'}),dict(move_number=2,san='e5',loss=900,classification='blunder',comment='Opponent error',engine_context={'game_phase':'opening'}),dict(move_number=3,san='Nf3',loss=130,classification='mistake',comment='Own error',engine_context={'game_phase':'middlegame'})]
    return moves,analysis


class ReviewSummaryTests(SimpleTestCase):
    def test_only_own_color_and_valid_data_are_measured(self):
        moves,analysis=payload();summary=build_review_summary(moves,analysis,'white','es')
        self.assertEqual(summary['evaluated'],2);self.assertEqual(summary['average_loss'],65)
        self.assertEqual(summary['serious'],1);self.assertEqual(summary['moments'][0]['san'],'Nf3')
        self.assertEqual(summary['focus'],'middlegame')
        analysis[2]['loss']=None
        summary=build_review_summary(moves,analysis,'white','es');self.assertEqual(summary['evaluated'],1);self.assertEqual(summary['errors'],0)

    def test_black_move_number_is_real_fullmove(self):
        moves,analysis=payload();summary=build_review_summary(moves,analysis,'black','en')
        self.assertEqual(summary['moments'][0]['fullmove'],1);self.assertTrue(summary['moments'][0]['black'])

    def test_missing_data_never_fabricates_zero_loss(self):
        moves,analysis=payload()
        for item in analysis:item['loss']=None
        self.assertIsNone(build_review_summary(moves,analysis,'white','pt')['average_loss'])


class LearningTests(TestCase):
    def setUp(self):
        cache.clear();self.a=User.objects.create_user('learn_alice',password='test-pass');self.b=User.objects.create_user('learn_bob',password='test-pass');self.c=User.objects.create_user('stranger',password='test-pass')
        self.client.force_login(self.a);session=self.client.session;session['language']='es';session.save()
        self.game=ChessGame.objects.create(owner=self.a,white_user=self.a,black_user=self.b,white_player=self.a.username,black_player=self.b.username,status='finished',result='white',time_control_minutes=5,is_rated=True)

    def saved(self,game=None,pgn='1. e4 e5 2. Nf3',color='white'):
        moves,analysis=payload();return save_review(self.a,pgn,'es',color,moves,analysis,'',game)

    def add_moves(self):
        for i,(frm,to,piece,color) in enumerate([('e2','e4','pawn','white'),('e7','e5','pawn','black'),('g1','f3','horse','white')],1):
            Move.objects.create(game=self.game,move_number=i,from_square=frm,to_square=to,piece_type=piece,piece_color=color)

    def test_persistence_is_idempotent_and_separates_color(self):
        self.saved();self.saved();self.assertEqual(GameReview.objects.count(),1)
        self.saved(color='black');self.assertEqual(GameReview.objects.count(),2)

    def test_anonymous_analysis_not_persisted(self):
        from django.contrib.auth.models import AnonymousUser
        moves,analysis=payload();self.assertIsNone(save_review(AnonymousUser(),'x','es','white',moves,analysis,''))
        self.assertFalse(GameReview.objects.exists())

    def test_partial_or_failed_analysis_not_persisted(self):
        moves,analysis=payload();self.assertIsNone(save_review(self.a,'x','es','white',moves,analysis[:1],''))
        self.assertIsNone(save_review(self.a,'x','es','white',[],[],''))

    def test_cached_review_reopens_without_engine(self):
        review=self.saved()
        with patch('games.views.open_stockfish_engine') as engine:
            response=self.client.get(reverse('game_analyzer'),{'review_id':review.pk})
        self.assertEqual(response.status_code,200);engine.assert_not_called()
        self.assertEqual(response.context['review_summary']['average_loss'],65)

    def test_other_user_cannot_read_review_or_mark_goal(self):
        review=self.saved();self.client.force_login(self.c)
        self.assertEqual(self.client.get(reverse('review_detail',args=[review.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('game_analyzer'),{'review_id':review.pk}).status_code,404)
        self.assertEqual(self.client.post(reverse('review_goal',args=[review.pk])).status_code,404)
        self.assertNotContains(self.client.get(reverse('learning')),'learn_alice')

    def test_goal_completion_idempotent_does_not_change_ratings(self):
        review=self.saved(self.game);url=reverse('review_goal',args=[review.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        self.client.post(url);review.refresh_from_db();first=review.goal_completed_at
        self.client.post(url);review.refresh_from_db();self.assertEqual(review.goal_completed_at,first)
        self.game.refresh_from_db();self.assertFalse(self.game.rating_applied)

    def test_summary_waits_for_explicit_analysis(self):
        self.add_moves()
        with patch('games.views.open_stockfish_engine') as engine:
            response=self.client.get(reverse('game_review',args=[self.game.pk]))
        self.assertContains(response,'Ganaste');self.assertContains(response,'Analizar mis jugadas');engine.assert_not_called()
        self.assertFalse(GameReview.objects.exists())

    def test_active_game_cannot_be_reviewed_and_stranger_denied(self):
        self.game.status='draft';self.game.save()
        self.assertRedirects(self.client.get(reverse('game_review',args=[self.game.pk])),reverse('game_detail',args=[self.game.pk]))
        self.client.force_login(self.c);self.assertEqual(self.client.get(reverse('game_review',args=[self.game.pk])).status_code,404)

    def test_full_analyzer_saves_review_and_second_visit_uses_saved_data(self):
        self.add_moves()
        with patch('games.views.configured_stockfish_path',return_value=('fake','')),patch('games.views.open_stockfish_engine',return_value=FakeAnalysisEngine({})) as engine:
            response=self.client.get(reverse('game_analyzer'),{'game_id':self.game.pk})
            self.assertEqual(response.status_code,200);self.assertEqual(GameReview.objects.count(),1)
            second=self.client.get(reverse('game_analyzer'),{'game_id':self.game.pk})
            self.assertEqual(second.status_code,200);self.assertEqual(engine.call_count,1)

    def test_history_deduplicates_languages_and_requires_enough_data_for_trend(self):
        review=self.saved()
        GameReview.objects.create(user=self.a,fingerprint=review.fingerprint,language='en',player_color='white',pgn=review.pgn,payload=review.payload)
        response=self.client.get(reverse('learning'));self.assertEqual(response.context['review_count'],1);self.assertIsNone(response.context['trend'])

    def test_rematch_swaps_colors_keeps_clock_and_reuses_request(self):
        url=reverse('game_rematch',args=[self.game.pk]);self.assertEqual(self.client.get(url).status_code,405)
        self.client.post(url);self.client.post(url);self.assertEqual(GameInvitation.objects.count(),1)
        invitation=GameInvitation.objects.get();self.assertEqual(invitation.creator_color,'black');self.assertEqual(invitation.time_control_minutes,5);self.assertTrue(invitation.is_rated)
        self.client.force_login(self.b);response=self.client.post(url)
        self.assertEqual(response.context['invitation'].pk, invitation.pk);self.assertEqual(GameInvitation.objects.count(),1)
        response=self.client.post(reverse('rematch_accept',args=[invitation.pk]));self.assertEqual(response.status_code,302)
        invitation.refresh_from_db();self.assertEqual(invitation.game.white_user,self.b);self.assertEqual(invitation.game.black_user,self.a);self.assertIsNone(invitation.game.clock_started_at)

    def test_rematch_cannot_start_for_stranger_or_active_game(self):
        self.game.status='draft';self.game.save();self.assertEqual(self.client.post(reverse('game_rematch',args=[self.game.pk])).status_code,400)
        self.client.force_login(self.c);self.assertEqual(self.client.post(reverse('game_rematch',args=[self.game.pk])).status_code,404)

    def test_guest_rematch_uses_link_and_accepts_with_swapped_colors(self):
        guestgame=ChessGame.objects.create(white_guest_id='guest-a',black_guest_id='guest-b',white_player='A',black_player='B',status='finished',result='draw',time_control_minutes=10)
        self.client.logout();session=self.client.session;session['guest_id']='guest-a';session.save()
        self.assertEqual(self.client.post(reverse('game_rematch',args=[guestgame.pk])).status_code,302)
        invitation=GameInvitation.objects.get();self.assertEqual(invitation.opponent_mode,'link');self.assertFalse(invitation.is_rated)
        other=Client();session=other.session;session['guest_id']='guest-b';session.save()
        self.assertEqual(other.post(reverse('rematch_accept',args=[invitation.pk])).status_code,302)
        invitation.refresh_from_db();self.assertEqual(invitation.game.black_guest_id,'guest-a');self.assertEqual(invitation.game.white_guest_id,'guest-b')

    def test_csrf_blocks_rematch_and_goal_changes(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.a)
        self.assertEqual(client.post(reverse('game_rematch',args=[self.game.pk])).status_code,403)
        review=self.saved();self.assertEqual(client.post(reverse('review_goal',args=[review.pk])).status_code,403)

    def test_post_with_game_query_does_not_attach_import_to_unrelated_saved_game(self):
        with patch('games.views.configured_stockfish_path',return_value=('fake','')),patch('games.views.open_stockfish_engine',return_value=FakeAnalysisEngine({})):
            self.client.post(reverse('game_analyzer')+f'?game_id={self.game.pk}',{'pgn':'1. e4 e5','player_color':'black'})
        review=GameReview.objects.get();self.assertIsNone(review.game_id);self.assertEqual(review.player_color,'black')

    def test_invalid_review_query_returns_404(self):
        self.assertEqual(self.client.get(reverse('game_analyzer'), {'review_id':'invalid'}).status_code,404)

    def test_spectator_owner_cannot_save_learning_or_accept_guest_rematch(self):
        game=ChessGame.objects.create(owner=self.a,white_guest_id='ga',black_guest_id='gb',white_player='A',black_player='B',status='finished',result='draw')
        moves,analysis=payload()
        self.assertIsNone(save_review(self.a,'x','es','white',moves,analysis,'',game))
        invitation=GameInvitation.objects.create(rematch_of=game,creator_guest_id='ga',creator_guest_name='A',opponent_mode='link',creator_color='black')
        self.assertEqual(self.client.post(reverse('rematch_accept',args=[invitation.pk])).status_code,400)

    def test_learning_focus_counts_actual_error_phases_across_reviews(self):
        for index, phases in enumerate([['opening','opening','endgame'],['endgame','endgame']]):
            moves=[dict(move_number=i+1,piece_color='white',san='e4') for i in range(len(phases))]
            analysis=[dict(move_number=i+1,san='e4',loss=100,classification='mistake',engine_context={'game_phase':phase}) for i,phase in enumerate(phases)]
            save_review(self.a,str(index),'es','white',moves,analysis,'')
        response=self.client.get(reverse('learning'))
        self.assertEqual(response.context['focus_name'],'Final')
