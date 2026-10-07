from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PlayerProfile


@override_settings(AXES_ENABLED=True)
class RegistrationTests(TestCase):
    def payload(self, **changes):
        data = {"username": "new-player", "email": "player@example.com",
                "password": "SignupPassword2026", "password_confirm": "SignupPassword2026"}
        data.update(changes)
        return data

    def test_registration_logs_in_with_multiple_authentication_backends(self):
        session = self.client.session
        session["language"] = "es"
        session.save()
        response = self.client.post(reverse("register"), self.payload(), follow=True)
        user = User.objects.get(username="new-player")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse("home"), 302)])
        self.assertEqual(response.wsgi_request.user.pk, user.pk)
        self.assertEqual(self.client.session[SESSION_KEY], str(user.pk))
        self.assertEqual(self.client.session[BACKEND_SESSION_KEY], "django.contrib.auth.backends.ModelBackend")
        self.assertEqual(self.client.session["language"], "es")
        self.assertTrue(user.check_password("SignupPassword2026"))
        self.assertTrue(PlayerProfile.objects.filter(user=user).exists())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # A later authenticated page must also recognize the new session.
        self.assertEqual(self.client.get(reverse("profile_stats")).wsgi_request.user.pk, user.pk)

    def test_invalid_registration_does_not_create_or_log_in_a_user(self):
        response = self.client.post(reverse("register"), self.payload(password_confirm="OtherPassword2026"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new-player").exists())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_existing_account_cannot_be_logged_in_through_registration(self):
        user = User.objects.create_user("new-player", email="existing@example.com", password="Original2026")
        response = self.client.post(reverse("register"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="new-player").count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Original2026"))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_player_session_has_finite_two_week_duration(self):
        self.client.post(reverse("register"), self.payload())
        self.assertEqual(settings.SESSION_COOKIE_AGE, 14 * 24 * 60 * 60)
        self.assertEqual(self.client.session.get_expiry_age(), 14 * 24 * 60 * 60)
        self.assertFalse(self.client.session.get_expire_at_browser_close())
