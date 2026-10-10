from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import PlayerProfile


class EditProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Original', password='pass12345', email='original@example.com')
        self.client.force_login(self.user)

    def change(self, name, password='pass12345', **extra):
        return self.client.post(reverse('edit_profile'), {'username': name, 'current_password': password, **extra})

    def test_rename_keeps_login_and_blocks_another_change(self):
        self.assertEqual(self.change('NewName').status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'NewName')
        self.assertIsNotNone(self.user.player_profile.username_changed_at)
        self.assertEqual(self.client.get(reverse('edit_profile')).status_code, 200)
        response = self.change('AnotherName')
        self.assertIn('username', response.context['form'].errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'NewName')

    def test_name_available_after_thirty_days(self):
        profile, _ = PlayerProfile.objects.get_or_create(user=self.user)
        profile.username_changed_at = timezone.now() - timedelta(days=30, seconds=1)
        profile.save()
        self.assertEqual(self.change('AllowedName').status_code, 302)

    def test_wrong_password_duplicate_and_email_are_protected(self):
        User.objects.create_user(username='Occupied')
        self.assertIn('username', self.change('occupied').context['form'].errors)
        self.assertIn('current_password', self.change('NewName', password='wrong').context['form'].errors)
        self.change('Original', email='changed@example.com')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.com')
        self.assertEqual(self.user.username, 'Original')

    def test_anonymous_user_must_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('edit_profile')).status_code, 302)
