import json
from unittest.mock import patch

import chess
from django.test import TestCase
from games import test_trainer


class CoachReliabilityTests(TestCase):
    def test_invalid_payloads_return_client_error(self):
        for payload in ([], {"moves":[None]}, {"moves":[3]}, {"moves":[{"from":"a1"}]}):
            with self.subTest(payload=payload):
                response=self.client.post('/coach-analysis/',json.dumps(payload),content_type='application/json')
                self.assertEqual(response.status_code,400)

    def test_shutdown_error_does_not_erase_success(self):
        engine=test_trainer.TrainerTests.engine(self)
        engine.quit.side_effect=chess.engine.EngineError('private cleanup details')
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine):
            response=self.client.post('/coach-analysis/',json.dumps({'moves':[{'from':'e2','to':'e4'}]}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertNotIn('private cleanup details',response.content.decode())

    def test_engine_error_is_retryable_without_private_details(self):
        engine=test_trainer.TrainerTests.engine(self)
        engine.analyse.side_effect=chess.engine.EngineError('private analysis details')
        with patch('games.views.configured_stockfish_path',return_value=('stockfish','')),patch('games.views.open_stockfish_engine',return_value=engine):
            response=self.client.post('/coach-analysis/',json.dumps({'moves':[{'from':'e2','to':'e4'}]}),content_type='application/json')
        self.assertEqual(response.status_code,500)
        self.assertTrue(response.json()['retryable'])
        self.assertNotIn('private analysis details',response.content.decode())
