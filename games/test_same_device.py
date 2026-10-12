from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import ChessGame, LearningReward, GameExperienceEvent

class SameDeviceTests(TestCase):
    def test_guest_and_languages_do_not_create_a_server_game(self):
        for language, label in [('pt','No mesmo dispositivo'),('es','En el mismo dispositivo'),('en','On the same device')]:
            session=self.client.session;session['language']=language;session.save()
            response=self.client.get(reverse('same_device'))
            self.assertEqual(response.status_code,200)
            self.assertContains(response,label)
            self.assertContains(response,'const LOCAL_PLAY_MODE=true')
            self.assertContains(response,'const COMPUTER_MODE=false')
            self.assertContains(response,'id="game-finish-local-again"')
            self.assertNotContains(response,'id="trainer-chat-form"')
            self.assertNotContains(response,'game-finish-advice')
        self.assertFalse(ChessGame.objects.exists())
        self.assertFalse(LearningReward.objects.exists())
        self.assertFalse(GameExperienceEvent.objects.exists())

    def test_navigation_and_signed_in_users(self):
        self.assertContains(self.client.get(reverse('home')),reverse('same_device'))
        self.client.force_login(User.objects.create_user('same-device-player'))
        self.assertEqual(self.client.get(reverse('same_device')).status_code,200)
        self.assertEqual(self.client.post(reverse('same_device')).status_code,405)
        self.assertFalse(ChessGame.objects.exists())
