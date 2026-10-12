import json
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from .models import ChessGame, GameChatMessage

class OnlineChatTests(TestCase):
    def setUp(self):
        cache.clear()
        self.white=User.objects.create_user('chat_white')
        self.black=User.objects.create_user('chat_black')
        self.game=ChessGame.objects.create(owner=self.white,white_user=self.white,black_user=self.black,white_player='White',black_player='Black')
        self.url=f'/games/{self.game.pk}/chat/'
        self.client.force_login(self.white)
    def test_confirmed_send_and_opponent_reads_message(self):
        response=self.client.post(self.url,json.dumps({'text':'Hola rival'}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['messages'][-1]['mine'])
        opponent=Client();opponent.force_login(self.black)
        data=opponent.get(self.url).json()
        self.assertEqual(data['messages'][-1]['text'],'Hola rival')
        self.assertFalse(data['messages'][-1]['mine'])
        self.assertEqual(data['unread_count'],1)
        self.assertEqual(opponent.get(self.url+'?mark_read=1').json()['unread_count'],0)
    def test_latest_messages_after_one_hundred(self):
        for i in range(105):
            GameChatMessage.objects.create(game=self.game,sender=self.black,text=f'message {i}')
        data=self.client.get(self.url+'?mark_read=1').json()
        self.assertEqual(len(data['messages']),100)
        self.assertEqual(data['messages'][0]['text'],'message 5')
        self.assertEqual(data['messages'][-1]['text'],'message 104')
        self.assertEqual(data['unread_count'],0)
    def test_guest_can_chat_with_registered_opponent(self):
        self.game.black_user=None;self.game.black_guest_id='guest-chat';self.game.save()
        guest=Client();session=guest.session;session['guest_id']='guest-chat';session.save()
        response=guest.post(self.url,json.dumps({'text':'Guest hello'}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['messages'][-1]['mine'])
        self.assertFalse(self.client.get(self.url).json()['messages'][-1]['mine'])
    def test_non_participant_cannot_send(self):
        self.client.force_login(User.objects.create_user('chat_other'))
        response=self.client.post(self.url,json.dumps({'text':'no'}),content_type='application/json')
        self.assertIn(response.status_code,(403,404))
        self.assertFalse(GameChatMessage.objects.exists())
