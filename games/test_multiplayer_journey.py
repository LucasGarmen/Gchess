"""Two independent Django clients exercising the casual multiplayer journey.

These checks do not claim to cover two browsers, native keyboard or real network loss.
"""
import json
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from .models import ChessGame, GameInvitation


class MultiplayerJourneyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.white=User.objects.create_user('journey_white')
        self.black=User.objects.create_user('journey_black_with_long_name')
        self.a=Client();self.a.force_login(self.white)
        self.b=Client();self.b.force_login(self.black)
        invitation=GameInvitation.objects.create(creator=self.white,opponent_mode='link',creator_color='white')
        url=reverse('accept_invitation_link',args=[invitation.token])
        self.assertEqual(self.b.get(url).status_code,200)
        self.b.post(url)
        invitation.refresh_from_db()
        self.game=invitation.game
        self.base=f'/games/{self.game.pk}/'

    def post(self,client,path,data):
        return client.post(self.base+path,json.dumps(data),content_type='application/json')

    def move(self,client,origin,destination,color,piece='pawn'):
        return self.post(client,'save-move/',{'from':origin,'to':destination,'piece_color':color,'piece_type':piece})

    def test_invitation_moves_chat_presence_reload_and_finish(self):
        for client,color in [(self.a,'white'),(self.b,'black')]:
            page=client.get(self.base)
            self.assertEqual(page.status_code,200)
            self.assertContains(page,f'data-viewer-color="{color}"')
            self.assertContains(page,'multiplayer_polish.css')
        self.assertEqual(self.a.post(self.base+'presence/').json(),{'white':True,'black':False})
        self.assertEqual(self.b.post(self.base+'presence/').json(),{'white':True,'black':True})
        self.assertNotEqual(self.move(self.b,'e7','e5','black').status_code,200)
        self.assertNotEqual(self.move(self.a,'e2','e5','white').status_code,200)
        self.assertEqual(self.move(self.a,'e2','e4','white').status_code,200)
        self.assertEqual(self.b.get(self.base+'state/').json()['turn'],'black')
        self.assertEqual(self.move(self.b,'e7','e5','black').status_code,200)
        self.assertEqual(self.a.get(self.base+'state/').json()['turn'],'white')
        for sender,receiver,text in [(self.a,self.b,'Hola 👋'),(self.b,self.a,'Boa partida! 🤝')]:
            self.assertEqual(self.post(sender,'chat/',{'text':text}).status_code,200)
            messages=receiver.get(self.base+'chat/').json()['messages']
            self.assertEqual(messages[-1]['text'],text)
            self.assertFalse(messages[-1]['mine'])
        # Re-authentication in a fresh client must recover the same server state.
        reconnect=Client();reconnect.force_login(self.white)
        self.assertEqual(reconnect.get(self.base+'state/').json()['fen'],self.b.get(self.base+'state/').json()['fen'])
        self.assertEqual(reconnect.get(self.base+'state/').json()['move_count'],2)
        cache.delete(f'game-presence:{self.game.pk}:black')
        self.assertFalse(self.a.post(self.base+'presence/').json()['black'])
        self.assertTrue(self.b.post(self.base+'presence/').json()['black'])
        self.assertEqual(self.post(self.b,'resign/',{}).status_code,200)
        self.game.refresh_from_db();self.assertEqual(self.game.status,'finished')
        self.assertNotEqual(self.move(self.a,'g1','f3','white','horse').status_code,200)
        page=self.a.get(self.base)
        self.assertContains(page,'id="game-closing-panel"')
        self.assertContains(page,reverse('game_rematch',args=[self.game.pk]))
        self.assertFalse(self.game.rating_applied,'Casual game must not change Elo')
