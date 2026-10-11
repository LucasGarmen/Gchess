from django.test import SimpleTestCase
from django.template.loader import render_to_string
from games.result_texts import TEXTS, KEYS

class ResultPanelTests(SimpleTestCase):
    def test_words_cover_all_outcomes_in_supported_languages(self):
        for lang in ('pt','es','en'):
            self.assertEqual(set(TEXTS[lang]),set(KEYS))
            self.assertTrue(all(TEXTS[lang].values()))

    def test_coach_actions_reuse_existing_analysis_and_play_again(self):
        html=render_to_string('games/_game_finish_notice.html',{'current_language':'pt'})
        self.assertIn('Jogar novamente',html)
        self.assertIn('id="game-finish-analyze"',html)
        self.assertIn('aria-labelledby="game-finish-title"',html)
        self.assertNotIn('PrecisÃ£o',html)
        self.assertNotIn('XP',html)

    def test_online_rematch_uses_real_native_post(self):
        html=render_to_string('games/_game_finish_notice.html',{'current_language':'pt','game':{'pk':42},'player_color':'white'})
        self.assertIn('action="/games/42/rematch/"',html)
        self.assertIn('method="post"',html)
        self.assertIn('href="/analyze/?game_id=42"',html)
        self.assertIn('Pedir revanche',html)
        self.assertNotIn('id="game-finish-again"',html)


from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, AsyncMock
from asgiref.sync import async_to_sync
from games.models import ChessGame
from games.views import finish_game
from games.consumers import GameConsumer

class ResultDeliveryTests(TestCase):
    def setUp(self):
        self.game=ChessGame.objects.create(white_player='White',black_player='Black',white_guest_id='white-guest',black_guest_id='black-guest')

    def test_result_is_broadcast_only_after_commit(self):
        with patch('games.views.broadcast_game_state') as notify:
            with self.captureOnCommitCallbacks(execute=True):
                finish_game(self.game,'draw')
                notify.assert_not_called()
            notify.assert_called_once_with(self.game.pk)
        self.game.refresh_from_db()
        self.assertEqual((self.game.status,self.game.result),('finished','draw'))

    def test_consumer_never_sends_a_result_to_unrelated_actor(self):
        consumer=GameConsumer();consumer.user=AnonymousUser();consumer.guest_id='other-guest';consumer.game_id=self.game.pk
        self.assertIsNone(GameConsumer.__dict__['result_state'].func(consumer))
        consumer.guest_id='white-guest'
        self.game.status='finished';self.game.result='white';self.game.save()
        state=GameConsumer.__dict__['result_state'].func(consumer)
        self.assertTrue(state['game_finished']);self.assertEqual(state['winner'],'white')

    def test_result_event_is_separate_from_move_acknowledgements(self):
        consumer=GameConsumer();consumer.result_state=AsyncMock(return_value={'game_finished':True,'result':'draw'});consumer.send_json=AsyncMock()
        async_to_sync(consumer.game_state_changed)({})
        consumer.send_json.assert_awaited_once_with({'type':'game.state','state':{'game_finished':True,'result':'draw'}})
