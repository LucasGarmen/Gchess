import json
from datetime import timedelta
from unittest.mock import patch
import chess
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import DailyTraining, GameReview
from .daily_training import candidates, build_plan, session_data


class DailyTrainingTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('daily_student')
        self.other=User.objects.create_user('daily_other')
        self.client.force_login(self.user)
        session=self.client.session;session['language']='es';session.save()
        self.url=reverse('daily_training');self.start=reverse('daily_training_start');self.answer=reverse('daily_training_answer')

    def saved_review(self,user=None,best='d2d4',color='white',loss=250):
        return GameReview.objects.create(user=user or self.user,fingerprint='review-'+str(GameReview.objects.count()),language='es',player_color=color,pgn='1. e4',payload={
            'moves':[{'piece_color':color}],
            'analysis':[{'loss':loss,'classification':'mistake','engine_context':{'fen_before':chess.STARTING_FEN,'best_move_uci':best,'played_move_uci':'e2e4','game_phase':'opening'}}]})

    def begin(self):
        self.client.post(self.start);return DailyTraining.objects.get(user=self.user,date=timezone.localdate())

    def post(self,plan,index,action,move=None):
        return self.client.post(self.answer,data=json.dumps(dict(id=plan.pk,index=index,action=action,move=move)),content_type='application/json')

    def test_read_only_landing_and_hub_and_login_required(self):
        self.assertEqual(self.client.get(self.url).status_code,200)
        self.client.get(reverse('training'));self.assertFalse(DailyTraining.objects.exists())
        self.client.logout();self.assertEqual(self.client.get(self.url).status_code,302)
        self.assertEqual(self.client.post(self.start).status_code,302)

    def test_start_is_idempotent_and_solutions_are_hidden(self):
        plan=self.begin();self.client.post(self.start)
        self.assertEqual(DailyTraining.objects.count(),1);self.assertEqual(len(plan.tasks),3)
        self.assertEqual(len({t['fen'] for t in plan.tasks}),3)
        response=self.client.get(self.url)
        self.assertNotIn('solution',response.context['session_data']['task'])
        self.assertNotIn('progress',response.context['session_data'])
        self.assertNotIn('tasks',response.context['session_data'])
        for task in plan.tasks:
            board=chess.Board(task['fen']);self.assertTrue(board.is_valid());board.push_uci(task['solution']);self.assertTrue(board.is_checkmate())

    def test_only_own_valid_verified_errors_are_candidates_and_no_live_engine(self):
        review=self.saved_review();self.saved_review(self.other);self.saved_review(best='a1a8');self.saved_review(color='black');self.saved_review(loss=None)
        with patch('games.views.open_stockfish_engine') as engine:
            tasks=build_plan(self.user,timezone.localdate())
        engine.assert_not_called()
        personal=[task for task in tasks if task['source']]
        self.assertEqual(len(personal),1);self.assertEqual(personal[0]['source'],review.pk)
        self.assertEqual(len(candidates(self.user)),1)

    def test_legal_wrong_move_then_correct_persists_attempts_and_resume(self):
        self.saved_review();plan=self.begin();index=next(i for i,t in enumerate(plan.tasks) if t['source'])
        self.assertEqual(index,0)
        response=self.post(plan,0,'try','e2e4');self.assertFalse(response.json()['resolved']);self.assertEqual(response.json()['state']['index'],0)
        response=self.post(plan,0,'try','d2d4');self.assertTrue(response.json()['resolved'])
        self.assertEqual(response.json()['state']['helped'],1)
        self.assertEqual(self.client.get(self.url).context['session_data']['index'],1)
        plan.refresh_from_db();self.assertEqual(plan.progress[0]['attempts'],2)

    def test_illegal_move_and_forged_index_do_not_mutate_state(self):
        self.saved_review();plan=self.begin()
        self.assertEqual(self.post(plan,0,'try','a1a8').status_code,400)
        self.assertEqual(self.post(plan,2,'reveal').status_code,409)
        self.assertEqual(self.post(plan,0,'invalid').status_code,400)
        plan.refresh_from_db();self.assertEqual(plan.progress[0]['attempts'],0);self.assertFalse(plan.completed_at)

    def test_hints_reveal_and_completion_saved_once(self):
        plan=self.begin()
        self.post(plan,0,'hint');self.post(plan,0,'try',plan.tasks[0]['solution'])
        self.post(plan,1,'reveal');response=self.post(plan,2,'try',plan.tasks[2]['solution'])
        state=response.json()['state'];self.assertTrue(state['completed']);self.assertEqual(state['independent'],1);self.assertEqual(state['helped'],2);self.assertEqual(state['recent_count'],1)
        plan.refresh_from_db();finished=plan.completed_at
        self.assertEqual(self.post(plan,2,'try',plan.tasks[2]['solution']).status_code,409)
        plan.refresh_from_db();self.assertEqual(plan.completed_at,finished)
        self.assertTrue(self.client.get(self.url).context['session_data']['completed'])

    def test_other_users_cannot_answer_or_view_source(self):
        self.saved_review();plan=self.begin();self.client.force_login(self.other)
        self.assertEqual(self.post(plan,0,'reveal').status_code,404)
        self.assertIsNone(self.client.get(self.url).context['plan'])

    def test_all_checkmates_are_accepted_and_black_orientation_data(self):
        board=chess.Board('7k/5K2/8/5Q2/8/8/8/8 w - - 0 1')
        mates=[]
        for move in board.legal_moves:
            after=board.copy();after.push(move)
            if after.is_checkmate():mates.append(move.uci())
        self.assertGreater(len(mates),1)
        plan=DailyTraining.objects.create(user=self.user,date=timezone.localdate(),tasks=[dict(fen=board.fen(),solution=mates[0],source=None,phase='general')],progress=[dict(attempts=0,helped=False,correct=False,resolved=False)])
        self.assertTrue(self.post(plan,0,'try',mates[1]).json()['resolved'])
        plan.tasks=[dict(fen='rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2',solution='d8h4',source=None,phase='general')];plan.progress=[dict(attempts=0,helped=False,correct=False,resolved=False)];plan.completed_at=None;plan.save()
        self.assertEqual(session_data(plan,'es')['task']['turn'],'Juegan negras')

    def test_next_day_has_new_plan_and_previous_progress_is_preserved(self):
        plan=self.begin();self.post(plan,0,'reveal')
        tomorrow=timezone.localdate()+timedelta(days=1)
        with patch('games.daily_training.timezone.localdate',return_value=tomorrow):self.client.post(self.start)
        self.assertEqual(DailyTraining.objects.count(),2)
        plan.refresh_from_db();self.assertTrue(plan.progress[0]['resolved'])

    def test_deleted_review_does_not_break_existing_training(self):
        review=self.saved_review();plan=self.begin();review.delete()
        data=session_data(plan,'es');self.assertIsNone(data['task']['source_url'])
        self.assertTrue(self.post(plan,0,'try','d2d4').json()['resolved'])

    def test_csrf_is_required_and_all_languages_render(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post(self.start).status_code,403)
        self.begin()
        for language in ('es','pt','en'):
            session=self.client.session;session['language']=language;session.save()
            self.assertEqual(self.client.get(self.url).status_code,200)
