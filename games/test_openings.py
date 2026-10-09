import json
import chess
from django.test import TestCase, Client
from .openings import LINES, TEXTS, lesson

class OpeningTests(TestCase):
    def test_catalog_and_all_moves_are_legal_in_three_languages(self):
        for lang in TEXTS:
            self.assertEqual(len(TEXTS[lang]),len(TEXTS['es']))
            for row in LINES:
                data=lesson(row[0],lang);board=chess.Board()
                for move in data['moves']:
                    board.push_uci(move['uci'])
                    self.assertTrue(move['explanation'])
        self.assertEqual(self.client.get('/training/openings/').status_code,200)

    def test_memory_mode_auto_replies_and_reaches_end_for_both_colors(self):
        for row in LINES:
            data=lesson(row[0],'es');index=0 if data['color']=='white' else 1
            while index<len(data['moves']):
                response=self.client.post('/training/openings/'+row[0]+'/step/',json.dumps(dict(index=index,mode='practice',move=data['moves'][index]['uci'])),content_type='application/json')
                result=response.json();self.assertTrue(result['correct']);self.assertGreater(result['index'],index);index=result['index']
                chess.Board(result['fen'])
            self.assertTrue(result['finished'])

    def test_wrong_move_keeps_position_and_invalid_indexes_are_rejected(self):
        url='/training/openings/italian/step/'
        response=self.client.post(url,json.dumps(dict(index=0,mode='practice',move='d2d4')),content_type='application/json')
        self.assertFalse(response.json()['correct']);self.assertEqual(response.json()['fen'],chess.STARTING_FEN)
        for index in (-1,99,True,1):
            response=self.client.post(url,json.dumps(dict(index=index,mode='practice',move='e2e4')),content_type='application/json');self.assertEqual(response.status_code,400)

    def test_learning_advances_one_ply_and_csrf_is_required(self):
        response=self.client.post('/training/openings/italian/step/',json.dumps(dict(index=0,mode='learn')),content_type='application/json')
        self.assertEqual(response.json()['index'],1)
        client=Client(enforce_csrf_checks=True)
        page=client.get('/training/openings/italian/')
        self.assertEqual(page.status_code,200);self.assertIn('csrftoken',page.cookies)
        self.assertEqual(client.post('/training/openings/italian/step/',json.dumps(dict(index=0,mode='learn')),content_type='application/json').status_code,403)
        self.assertEqual(self.client.get('/training/openings/missing/').status_code,404)
