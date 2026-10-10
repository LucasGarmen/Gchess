from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .checkin import today
from .models import DailyCheckin

class DailyCheckinTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='checkin_player',password='local-test')
        self.client.force_login(self.user)
    def test_one_reward_per_day_and_next_day(self):
        day=today()
        with patch('games.checkin.today',return_value=day):
            for _ in range(3): self.client.post(reverse('daily_checkin'),{'points':999})
        self.assertEqual(DailyCheckin.objects.filter(user=self.user).count(),1)
        with patch('games.checkin.today',return_value=day+timedelta(days=1)):
            self.client.post(reverse('daily_checkin'))
        response=self.client.get(reverse('shop'))
        self.assertEqual(response.context['checkin_balance'],20)
    def test_login_and_post_required(self):
        self.assertEqual(self.client.get(reverse('daily_checkin')).status_code,405)
        self.client.logout()
        self.assertEqual(self.client.post(reverse('daily_checkin')).status_code,302)
        self.assertFalse(DailyCheckin.objects.exists())
    def test_read_does_not_award_and_accounts_are_independent(self):
        self.client.get(reverse('shop'))
        self.assertFalse(DailyCheckin.objects.exists())
        self.client.post(reverse('daily_checkin'))
        other=User.objects.create_user(username='other_checkin')
        self.client.force_login(other)
        response=self.client.get(reverse('shop'))
        self.assertEqual(response.context['checkin_balance'],0)
        self.assertFalse(response.context['checkin_claimed'])
