from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase,Client
from .models import ChessGame

class GamePresenceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.white=User.objects.create_user('presence_white');self.black=User.objects.create_user('presence_black')
        self.game=ChessGame.objects.create(owner=self.white,white_user=self.white,black_user=self.black,white_player='W',black_player='B')
        self.url=f'/games/{self.game.pk}/presence/'
        self.client.force_login(self.white)
    def test_presence_is_scoped_and_expires(self):
        self.assertEqual(self.client.post(self.url).json(),{'white':True,'black':False})
        rival=Client();rival.force_login(self.black)
        self.assertEqual(rival.post(self.url).json(),{'white':True,'black':True})
        cache.delete(f'game-presence:{self.game.pk}:black')
        self.assertFalse(self.client.post(self.url).json()['black'])
        other=ChessGame.objects.create(owner=self.white,white_user=self.white,black_user=self.black,white_player='W',black_player='B')
        self.assertFalse(self.client.post(f'/games/{other.pk}/presence/').json()['black'])
    def test_outsider_has_no_presence_access(self):
        self.client.force_login(User.objects.create_user('presence_other'))
        self.assertIn(self.client.post(self.url).status_code,(403,404))
        self.assertIsNone(cache.get(f'game-presence:{self.game.pk}:white'))
    def test_guest_is_supported(self):
        self.game.black_user=None;self.game.black_guest_id='presence_guest';self.game.save()
        guest=Client();session=guest.session;session['guest_id']='presence_guest';session.save()
        self.assertEqual(guest.post(self.url).json(),{'white':False,'black':True})
