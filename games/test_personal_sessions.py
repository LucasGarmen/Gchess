from datetime import timedelta
from unittest.mock import patch
import chess
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import DailyTraining, GameReview
from .daily_training import build_plan, session_data
from .personal_sessions import practice_memory, next_session, position_key, personal_selection, theme_for


class PersonalSessionTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('session_student')
        self.other=User.objects.create_user('session_other')
        self.client.force_login(self.user)
        session=self.client.session;session['language']='es';session.save()
        self.today=timezone.localdate()

    def review(self, moves=(), best='d2d4', played='e2e4', user=None, phase='opening'):
        board=chess.Board()
        for move in moves:board.push_uci(move)
        return GameReview.objects.create(user=user or self.user,fingerprint=str(GameReview.objects.count()),language='es',player_color='white',pgn='1. e4',payload=dict(moves=[dict(piece_color='white')],analysis=[dict(move_number=1,loss=250,classification='mistake',engine_context=dict(fen_before=board.fen(),best_move_uci=best,played_move_uci=played,game_phase=phase))]))

    def task(self, review):
        from .daily_training import candidates
        return candidates(review.user,review.pk)[0]

    def practice(self, task, offset, independent=True, **extra):
        answer=dict(resolved=True,correct=True,helped=not independent,attempts=1,**extra)
        return DailyTraining.objects.create(user=self.user,date=self.today-timedelta(days=offset),tasks=[task],progress=[answer],completed_at=timezone.now())

    def test_owned_verified_patterns_only_and_read_only_dashboard(self):
        self.review();self.review(user=self.other)
        with patch('games.views.open_stockfish_engine') as engine:
            response=self.client.get(reverse('learning'))
        self.assertEqual(response.status_code,200);engine.assert_not_called()
        data=response.context['next_session']
        self.assertEqual(data['fresh'],1);self.assertEqual(data['themes'],[dict(label='Desarrollar las piezas',count=1)])
        self.assertFalse(DailyTraining.objects.exists());self.assertContains(response,'Tu próxima sesión')

    def test_new_users_get_honest_fallback_and_legal_exercises(self):
        data=next_session(self.user,'es')
        self.assertFalse(data['has_personal']);self.assertFalse(data['personal_focus'])
        self.assertEqual(data['focus'],'Encontrar el mate')
        self.assertEqual(len(build_plan(self.user,self.today)),3)

    def test_success_returns_after_three_days_and_is_not_repeated_early(self):
        task=self.task(self.review());self.practice(task,0)
        memory=practice_memory(self.user,self.today)[position_key(task['fen'])]
        self.assertEqual(memory['due'],self.today+timedelta(days=3))
        self.assertFalse(personal_selection(self.user,self.today+timedelta(days=2)))
        selection=personal_selection(self.user,self.today+timedelta(days=3))
        self.assertEqual(len(selection),1);self.assertTrue(selection[0]['revisit'])
        self.assertTrue(all(t['source'] is None for t in build_plan(self.user,self.today+timedelta(days=1))))

    def test_help_retries_and_reveal_require_an_earlier_revisit(self):
        task=self.task(self.review());plan=self.practice(task,0,False)
        key=position_key(task['fen'])
        for answer in [dict(resolved=True,correct=True,helped=True,attempts=1),dict(resolved=True,correct=True,helped=False,attempts=2),dict(resolved=True,correct=False,helped=True,attempts=0)]:
            plan.progress=[answer];plan.save()
            memory=practice_memory(self.user,self.today)[key]
            self.assertEqual(memory['due'],self.today+timedelta(days=1));self.assertEqual(memory['streak'],0)

    def test_two_distinct_successful_days_confirm_and_lengthen_review(self):
        task=self.task(self.review());self.practice(task,10);self.practice(task,7)
        data=next_session(self.user,'es');memory=practice_memory(self.user,self.today)[position_key(task['fen'])]
        self.assertEqual(data['confirmed'],1);self.assertEqual(data['due'],1)
        self.assertEqual(memory['streak'],2);self.assertEqual(memory['due'],self.today)
        self.practice(task,0,False)
        self.assertEqual(next_session(self.user,'es')['confirmed'],0)

    def test_due_review_plus_new_positions_without_duplicates(self):
        task=self.task(self.review());self.practice(task,5,False)
        self.review(('e2e4','e7e5'),'g1f3','d2d4')
        self.review(('d2d4','d7d5'),'c2c4','g1f3')
        tasks=build_plan(self.user,self.today)
        self.assertEqual(len(tasks),3);self.assertTrue(tasks[0]['revisit'])
        self.assertTrue(all(t['source'] for t in tasks));self.assertEqual(len({position_key(t['fen']) for t in tasks}),3)

    def test_same_position_in_another_review_cannot_fake_a_new_exercise(self):
        review=self.review();task=self.task(review);self.practice(task,0)
        copy=self.review();payload=copy.payload
        payload['analysis'][0]['engine_context']['fen_before']=chess.STARTING_FEN.replace('0 1','4 8')
        copy.payload=payload;copy.save()
        data=next_session(self.user,'es')
        self.assertEqual(data['fresh'],0);self.assertEqual(data['practiced'],1)
        self.assertEqual(data['themes'][0]['count'],1)

    def test_resume_does_not_rebuild_plan_and_completion_opens_fresh_coach(self):
        self.review();self.client.post(reverse('daily_training_start'))
        plan=DailyTraining.objects.get(user=self.user,date=self.today)
        before=plan.tasks
        self.client.post(reverse('daily_training_start'));plan.refresh_from_db();self.assertEqual(plan.tasks,before)
        data=next_session(self.user,'es',plan);self.assertEqual(data['status'],'resume')
        self.assertEqual(data['url'],reverse('daily_training'))
        plan.completed_at=timezone.now();plan.save()
        data=next_session(self.user,'es',plan);self.assertEqual(data['status'],'finished')
        self.assertIn('?bot=session-',data['url'])
        response=self.client.get(reverse('daily_training'));self.assertContains(response,data['texts']['play'])

    def test_answer_date_saved_once_and_hidden_solution(self):
        self.review();self.client.post(reverse('daily_training_start'))
        plan=DailyTraining.objects.get(user=self.user,date=self.today)
        data=dict(id=plan.pk,index=0,action='try',move=plan.tasks[0]['solution'])
        response=self.client.post(reverse('daily_training_answer'),data=data,content_type='application/json')
        self.assertEqual(response.status_code,200)
        plan.refresh_from_db();self.assertEqual(plan.progress[0]['resolved_on'],self.today.isoformat())
        self.assertEqual(self.client.post(reverse('daily_training_answer'),data=data,content_type='application/json').status_code,409)
        state=session_data(plan,'es');self.assertNotIn('solution',state['task'])
        self.assertNotIn('tasks',state)

    def test_future_and_other_account_history_do_not_confirm_progress(self):
        task=self.task(self.review());self.practice(task,-1)
        DailyTraining.objects.create(user=self.other,date=self.today,tasks=[task],progress=[dict(resolved=True,correct=True,helped=False,attempts=1)])
        self.assertEqual(next_session(self.user,'es')['practiced'],0)

    def test_delayed_completion_uses_actual_practice_date(self):
        task=self.task(self.review());self.practice(task,10,resolved_on=self.today.isoformat())
        memory=practice_memory(self.user,self.today)[position_key(task['fen'])]
        self.assertEqual(memory['due'],self.today+timedelta(days=3))

    def test_no_return_marketing_copy_in_daily_card_and_three_languages(self):
        from .training import MODE_CONTENT
        for lang in ('es','pt','en'):
            self.assertNotIn('motivo',MODE_CONTENT[lang][1][1]);self.assertNotIn('reason',MODE_CONTENT[lang][1][1])
            session=self.client.session;session['language']=lang;session.save()
            response=self.client.get(reverse('learning'))
            self.assertContains(response,next_session(self.user,lang)['texts']['title'])

    def test_late_answers_are_processed_in_answer_date_order(self):
        task=self.task(self.review())
        self.practice(task,10,resolved_on=self.today.isoformat())
        self.practice(task,4,resolved_on=(self.today-timedelta(days=4)).isoformat())
        memory=practice_memory(self.user,self.today)[position_key(task['fen'])]
        self.assertEqual(memory['streak'],2)
        self.assertEqual(memory['due'],self.today+timedelta(days=7))

    def test_themes_describe_proven_board_facts(self):
        self.assertEqual(theme_for(dict(fen='4k3/8/8/8/8/8/4p3/4K3 w - - 0 1',solution='e1e2',phase='endgame')),'material')
        self.assertEqual(theme_for(dict(fen='4k3/8/8/8/8/8/4r3/4K3 w - - 0 1',solution='e1e2',phase='endgame')),'king')
