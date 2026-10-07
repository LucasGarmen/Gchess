from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib import admin
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.oath import totp
from axes.models import AccessAttempt

@override_settings(AXES_ENABLED=True)
class AdminSecurityTests(TestCase):
    password='LocalTest-Admin-Password-2026'
    def setUp(self):
        self.staff=User.objects.create_superuser('security-admin','admin@example.invalid',self.password)
        self.player=User.objects.create_user('security-player',password=self.password)
        self.login_url=reverse('two_factor:login')+'?next='+reverse('admin:index')
    def begin_login(self,user=None):
        response=self.client.get(self.login_url)
        prefix=response.context['wizard']['management_form'].prefix
        return self.client.post(self.login_url,{prefix+'-current_step':'auth','auth-username':(user or self.staff).username,'auth-password':self.password})
    def submit_token(self,response,token,step='token'):
        prefix=response.context['wizard']['management_form'].prefix
        return self.client.post(self.login_url,{prefix+'-current_step':step,step+'-otp_token':token})
    def test_anonymous_admin_uses_mfa_login_and_models_still_registered(self):
        response=self.client.get(reverse('admin:index'),follow=True)
        self.assertEqual(response.request['PATH_INFO'],reverse('two_factor:login'))
        from games.models import ChessGame
        self.assertTrue(admin.site.is_registered(ChessGame))
    def test_password_only_site_login_cannot_open_admin_or_change_user(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
        self.assertEqual(self.client.get(reverse('admin:auth_user_change',args=[self.player.pk])).status_code,302)
        self.assertEqual(self.client.post(reverse('admin:auth_user_change',args=[self.player.pk]),{}).status_code,302)
    def test_no_device_bootstrap_goes_to_setup_without_admin_access(self):
        response=self.begin_login()
        self.assertRedirects(response,reverse('two_factor:setup'),fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
        self.assertEqual(self.client.get(reverse('two_factor:setup')).status_code,200)
    def test_regular_player_cannot_use_staff_login_or_setup(self):
        response=self.begin_login(self.player)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('_auth_user_id',self.client.session)
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(reverse('two_factor:setup')).status_code,403)
    def test_existing_device_cannot_be_replaced_with_password_only_session(self):
        TOTPDevice.objects.create(user=self.staff,name='default',confirmed=True)
        self.client.force_login(self.staff)
        response=self.client.get(reverse('two_factor:setup'))
        self.assertEqual(response.status_code,302)
        self.assertIn(reverse('two_factor:login'),response.url)
    def test_totp_login_grants_admin_and_rejects_replayed_code(self):
        device=TOTPDevice.objects.create(user=self.staff,name='default',confirmed=True)
        response=self.begin_login()
        self.assertEqual(response.context['wizard']['steps'].current,'token')
        code=str(totp(device.bin_key,step=device.step,t0=device.t0,digits=device.digits)).zfill(device.digits)
        response=self.submit_token(response,code)
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,200)
        self.client.logout()
        response=self.begin_login()
        response=self.submit_token(response,code)
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
    def test_bad_totp_never_grants_admin(self):
        TOTPDevice.objects.create(user=self.staff,name='default',confirmed=True)
        response=self.begin_login()
        response=self.submit_token(response,'not-a-code')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
    def test_backup_token_works_once(self):
        TOTPDevice.objects.create(user=self.staff,name='default',confirmed=True)
        backup=StaticDevice.objects.create(user=self.staff,name='backup')
        StaticToken.objects.create(device=backup,token='local-backup-test')
        response=self.begin_login()
        response=self.client.post(self.login_url,{'wizard_goto_step':'backup'})
        response=self.submit_token(response,'local-backup-test',step='backup')
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,200)
        self.assertFalse(StaticToken.objects.filter(device=backup).exists())
    def test_other_users_device_session_cannot_verify_staff(self):
        device=TOTPDevice.objects.create(user=self.player,name='default',confirmed=True)
        self.client.force_login(self.staff)
        session=self.client.session;session[DEVICE_ID_SESSION_KEY]=device.persistent_id;session.save()
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
    def test_verified_nonstaff_still_cannot_open_admin(self):
        device=TOTPDevice.objects.create(user=self.player,name='default',confirmed=True)
        self.client.force_login(self.player)
        session=self.client.session;session[DEVICE_ID_SESSION_KEY]=device.persistent_id;session.save()
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,302)
    def test_five_password_failures_lock_username_across_ip_and_correct_password(self):
        url=reverse('login')
        for n in range(5):
            self.client.post(url,{'username':self.staff.username,'password':'wrong'},REMOTE_ADDR='192.0.2.1',HTTP_USER_AGENT='attempt'+str(n))
        response=self.client.post(url,{'username':self.staff.username,'password':self.password},REMOTE_ADDR='192.0.2.99')
        self.assertEqual(response.status_code,429)
        self.assertNotIn('_auth_user_id',self.client.session)
        self.assertEqual(self.client.post(url,{'username':self.player.username,'password':self.password},REMOTE_ADDR='192.0.2.1').status_code,302)
    def test_cooloff_expires_and_success_clears_failures(self):
        url=reverse('login')
        for n in range(5):self.client.post(url,{'username':self.staff.username,'password':'wrong'})
        AccessAttempt.objects.filter(username=self.staff.username).update(attempt_time=timezone.now()-timedelta(minutes=16))
        self.assertEqual(self.client.post(url,{'username':self.staff.username,'password':self.password}).status_code,302)
        self.assertFalse(AccessAttempt.objects.filter(username=self.staff.username).exists())
    def test_mfa_pages_private_no_cache_and_csrf_protected(self):
        response=self.client.get(self.login_url)
        self.assertIn('no-store',response['Cache-Control'])
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.login_url,{'staff_login_view-current_step':'auth','auth-username':self.staff.username,'auth-password':self.password}).status_code,403)

    def test_complete_enrollment_and_private_qr(self):
        from base64 import b32decode
        self.begin_login()
        url=reverse('two_factor:setup')
        response=self.client.get(url)
        prefix=response.context['wizard']['management_form'].prefix
        response=self.client.post(url,{prefix+'-current_step':'welcome'})
        self.assertEqual(response.context['wizard']['steps'].current,'generator')
        qr=self.client.get(reverse('two_factor:qr'))
        self.assertEqual(qr.status_code,200)
        self.assertIn('no-store',qr['Cache-Control'])
        raw_key=b32decode(response.context['secret_key'])
        code=totp(raw_key)
        response=self.client.post(url,{prefix+'-current_step':'generator','generator-token':code})
        self.assertEqual(response.status_code,302)
        self.assertTrue(TOTPDevice.objects.filter(user=self.staff,confirmed=True,name='default').exists())
        self.assertEqual(self.client.get(reverse('admin:index')).status_code,200)
