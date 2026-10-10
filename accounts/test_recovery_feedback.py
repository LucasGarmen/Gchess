from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RecoveryFeedbackTests(TestCase):
    @patch('accounts.views.send_password_reset_confirmation_email')
    def test_missing_email_shows_error_and_is_not_sent(self, send):
        response = self.client.post(reverse('password_reset'), {'email': 'missing@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        send.assert_not_called()

    @patch('accounts.views.send_password_reset_confirmation_email')
    def test_success_only_after_sending(self, send):
        User.objects.create_user(username='recovery', email='registered@example.com')
        response = self.client.post(reverse('password_reset'), {'email': 'registered@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        send.assert_called_once()

    @patch('accounts.views.send_password_reset_confirmation_email', side_effect=RuntimeError('SMTP unavailable'))
    def test_delivery_failure_does_not_show_success(self, send):
        User.objects.create_user(username='recovery', email='registered@example.com')
        response = self.client.post(reverse('password_reset'), {'email': 'registered@example.com'})
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertNotIn('password_reset_email_sent', self.client.session)

    def test_direct_success_page_requires_previous_send(self):
        self.assertRedirects(self.client.get(reverse('password_reset_done')), reverse('password_reset'))
