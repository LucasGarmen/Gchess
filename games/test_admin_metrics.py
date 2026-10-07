import csv
import io
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import PlayerActivityDay, UserPresence
from .views import PRESENCE_TOUCH_CACHE

class AdminMetricsTests(TestCase):
    def setUp(self):
        PRESENCE_TOUCH_CACHE.clear()
        self.admin=User.objects.create_superuser('metrics-owner','owner@example.invalid','test-only-password')
        self.player=User.objects.create_user('metrics-player')
        self.url=reverse('admin:player_activity')
    def verified(self,user):
        self.client.force_login(user)
        device=TOTPDevice.objects.create(user=user,name='default',confirmed=True)
        session=self.client.session;session[DEVICE_ID_SESSION_KEY]=device.persistent_id;session.save()
    def test_statistics_require_superuser_and_otp_including_csv(self):
        self.assertEqual(self.client.get(self.url).status_code,302)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url+'?export=csv').status_code,302)
        staff=User.objects.create_user('metrics-staff',is_staff=True)
        self.verified(staff)
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.assertEqual(self.client.get(self.url+'?export=csv').status_code,403)
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(self.url).status_code,302)
    def test_online_count_excludes_stale_and_staff_and_inactive(self):
        self.verified(self.admin)
        UserPresence.objects.create(user=self.player)
        UserPresence.objects.create(user=self.admin)
        stale=User.objects.create_user('metrics-stale');presence=UserPresence.objects.create(user=stale)
        UserPresence.objects.filter(pk=presence.pk).update(last_seen=timezone.now()-timedelta(seconds=61))
        inactive=User.objects.create_user('metrics-disabled',is_active=False);UserPresence.objects.create(user=inactive)
        response=self.client.get(self.url)
        self.assertEqual(response.context_data['online_count'],1)
        self.assertEqual(response.context_data['online_players'][0].user,self.player)
        self.assertIn('no-store',response['Cache-Control'])
    def test_new_active_and_returning_counts_and_csv(self):
        self.verified(self.admin);today=timezone.localdate()
        PlayerActivityDay.objects.create(user=self.player,date=today-timedelta(days=1))
        PlayerActivityDay.objects.create(user=self.player,date=today)
        new=User.objects.create_user('metrics-new');PlayerActivityDay.objects.create(user=new,date=today)
        response=self.client.get(self.url)
        self.assertEqual(response.context_data['active_today'],2)
        self.assertEqual(response.context_data['returning_today'],1)
        self.assertEqual(response.context_data['new_today'],2)
        self.assertContains(response,'Sin registro')
        export=self.client.get(self.url+'?export=csv')
        rows=list(csv.reader(io.StringIO(export.content.decode())))
        self.assertEqual(len(rows),31)
        self.assertEqual(rows[-1],[today.isoformat(),'2','2','1'])
        self.assertEqual(rows[1][2:],['',''])
    def test_activity_is_deduplicated_and_admin_guest_requests_excluded(self):
        self.client.get(reverse('home'));self.assertFalse(PlayerActivityDay.objects.exists())
        self.client.force_login(self.player)
        self.client.get(reverse('home'));self.client.get(reverse('home'))
        self.assertEqual(PlayerActivityDay.objects.filter(user=self.player).count(),1)
        self.verified(self.admin);self.client.get(self.url)
        self.assertFalse(PlayerActivityDay.objects.filter(user=self.admin).exists())
    def test_panel_does_not_create_fake_history(self):
        self.verified(self.admin);response=self.client.get(self.url)
        self.assertEqual(response.context_data['active_today'],0)
        self.assertFalse(PlayerActivityDay.objects.exists())
        self.assertContains(response,'El historial de actividad empieza')
    def test_index_has_private_panel_link(self):
        self.verified(self.admin)
        self.assertContains(self.client.get(reverse('admin:index')),self.url)
