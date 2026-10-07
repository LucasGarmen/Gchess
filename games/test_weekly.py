import json
from datetime import timedelta
from unittest.mock import patch
import chess
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from .models import WeeklyChallenge, WeeklyChallengeEntry, Friendship
from .weekly import week_start, build_tasks, standings, state_for

class WeeklyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=User.objects.create_user('student')
        self.other=User.objects.create_user('friend')
        self.client.force_login(self.user)
    def begin(self):
        self.assertEqual(self.client.post(reverse('weekly_start')).status_code,302)
        return WeeklyChallengeEntry.objects.get(user=self.user,challenge__week_start=week_start())
    def answer(self,e,i,action='try',move=None,practice=False):
        return self.client.post(reverse('weekly_answer'),json.dumps(dict(id=e.pk,index=i,action=action,move=move,practice=practice)),content_type='application/json')
    def test_common_verified_positions_and_idempotence(self):
        e=self.begin();self.begin()
        self.client.force_login(self.other);other=self.begin()
        self.assertEqual(e.challenge_id,other.challenge_id)
        self.assertEqual(WeeklyChallenge.objects.count(),1)
        tasks=e.challenge.tasks
        self.assertEqual(tasks,build_tasks(week_start()))
        self.assertEqual(len({t['fen'] for t in tasks}),5)
        self.assertEqual(sum(chess.Board(t['fen']).turn for t in tasks),3)
        for t in tasks:
            b=chess.Board(t['fen']);self.assertTrue(b.is_valid());b.push_uci(t['solution']);self.assertTrue(b.is_checkmate())
        self.assertNotIn('solution',state_for(e,'es')['task'])
    def test_get_is_read_only_login_and_csrf(self):
        self.assertEqual(self.client.get(reverse('weekly_challenge')).status_code,200)
        self.assertFalse(WeeklyChallenge.objects.exists())
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.user)
        self.assertEqual(secure.post(reverse('weekly_start')).status_code,403)
        self.client.logout();self.assertEqual(self.client.get(reverse('weekly_challenge')).status_code,302)
    def test_correct_first_and_stale_replay(self):
        e=self.begin();m=e.challenge.tasks[0]['solution']
        self.assertEqual(self.answer(e,0,move=m).json()['state']['score'],10)
        self.assertEqual(self.answer(e,0,move=m).status_code,409)
        e.refresh_from_db();self.assertEqual(e.score,10)
    def test_wrong_legal_then_correct_never_rescores(self):
        e=self.begin();b=chess.Board(e.challenge.tasks[0]['fen'])
        wrong=next(m.uci() for m in b.legal_moves if not self.mates(b,m))
        self.assertFalse(self.answer(e,0,move=wrong).json()['resolved'])
        self.answer(e,0,move=e.challenge.tasks[0]['solution'])
        e.refresh_from_db();self.assertEqual(e.score,0);self.assertTrue(e.progress[0]['attempted'])
    @staticmethod
    def mates(board,move):
        b=board.copy();b.push(move);return b.is_checkmate()
    def test_illegal_and_forged_index_do_not_consume(self):
        e=self.begin()
        self.assertEqual(self.answer(e,0,move='a1a8').status_code,400)
        self.assertEqual(self.answer(e,3,action='reveal').status_code,409)
        e.refresh_from_db();self.assertFalse(e.progress[0]['attempted'])
    def test_hints_reveal_completion_and_practice_preserve_result(self):
        e=self.begin();self.answer(e,0,'hint');self.answer(e,0,move=e.challenge.tasks[0]['solution'])
        self.answer(e,1,'reveal')
        for i in range(2,5):self.answer(e,i,move=e.challenge.tasks[i]['solution'])
        e.refresh_from_db();self.assertEqual(e.score,30);self.assertIsNotNone(e.completed_at)
        original=(e.progress,e.score,e.completed_at)
        self.answer(e,0,'hint',practice=True)
        for i in range(5):
            response=self.answer(e,i,move=e.challenge.tasks[i]['solution'],practice=True)
            self.assertEqual(response.json()['state']['index'],i+1)
        self.assertTrue(response.json()['state']['completed'])
        e.refresh_from_db();self.assertEqual((e.progress,e.score,e.completed_at),original)
        self.assertEqual(self.client.get(reverse('weekly_play',args=[e.pk])+'?practice=1').context['session_data']['index'],0)
    def test_other_accounts_cannot_view_or_answer(self):
        e=self.begin();self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('weekly_play',args=[e.pk])).status_code,404)
        self.assertEqual(self.answer(e,0,'reveal').status_code,404)
    def test_rollover_closes_scoring_and_retains_history(self):
        e=self.begin();nextweek=week_start()+timedelta(days=7)
        with patch('games.weekly.week_start',return_value=nextweek):
            self.answer(e,0,move=e.challenge.tasks[0]['solution'])
            e.refresh_from_db();self.assertEqual(e.score,0)
            self.assertEqual(self.client.get(reverse('weekly_challenge')).context['history'].object_list[0],e)
            self.client.post(reverse('weekly_start'));new=WeeklyChallengeEntry.objects.get(user=self.user,challenge__week_start=nextweek);self.assertNotEqual(new.challenge_id,e.challenge_id)
    def test_private_friend_ranking_ties_and_pending(self):
        e=self.begin()
        third=User.objects.create_user('third');pending=User.objects.create_user('pending')
        for u,status in [(self.other,'accepted'),(third,'accepted'),(pending,'pending')]:
            Friendship.objects.create(low_user=self.user,high_user=u,requester=self.user,status=status)
        for u,score in [(self.user,20),(self.other,20),(third,10),(pending,50)]:
            WeeklyChallengeEntry.objects.update_or_create(challenge=e.challenge,user=u,defaults={'score':score,'progress':[dict(attempted=True,first_correct=False,resolved=True,helped=False)]*5})
        rows=standings(self.user,e.challenge)
        self.assertEqual([r['rank'] for r in rows],[1,1,3])
        self.assertNotIn(pending.pk,[r['user'].pk for r in rows])
        Friendship.objects.filter(high_user=third).delete()
        self.assertEqual(len(standings(self.user,e.challenge)),2)
    def test_languages_render_play_and_landing(self):
        e=self.begin()
        for lang in ['es','pt','en']:
            session=self.client.session;session['language']=lang;session.save()
            for name,args in [('weekly_challenge',[]),('weekly_play',[e.pk])]:
                self.assertEqual(self.client.get(reverse(name,args=args)).status_code,200)

    def test_practice_cannot_preview_unscored_solutions(self):
        e=self.begin()
        self.assertEqual(self.answer(e,0,'reveal',practice=True).status_code,409)
        page=self.client.get(reverse('weekly_play',args=[e.pk])+'?practice=1')
        self.assertFalse(page.context['session_data']['practice'])
        e.refresh_from_db();self.assertFalse(e.progress[0]['attempted'])
    def test_alternate_checkmate_is_accepted(self):
        from .weekly import verified_library
        task=next(t for t in verified_library() if sum(self.mates(chess.Board(t['fen']),m) for m in chess.Board(t['fen']).legal_moves)>1)
        e=self.begin();e.challenge.tasks[0]=dict(task);e.challenge.save(update_fields=['tasks'])
        b=chess.Board(task['fen']);alternative=next(m.uci() for m in b.legal_moves if m.uci()!=task['solution'] and self.mates(b,m))
        self.assertEqual(self.answer(e,0,move=alternative).json()['state']['score'],10)
