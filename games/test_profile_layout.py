from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import ChessGame


class ProfileLayoutTests(TestCase):
    def test_results_count_only_completed_games_played_by_user(self):
        user = User.objects.create_user(username="profile-player", password="test-password")
        rival = User.objects.create_user(username="profile-rival")
        for result in ["white", "black", "draw"]:
            ChessGame.objects.create(white_user=user, black_user=rival, white_player="Player", black_player="Rival", status="finished", result=result)
        ChessGame.objects.create(owner=user, white_player="Imported", black_player="Game", status="finished", result="white")
        ChessGame.objects.create(white_user=user, black_user=rival, white_player="Player", black_player="Rival", status="draft")
        ChessGame.objects.create(white_user=user, white_player="Player", black_player="Coach", status="finished", result="black", category="training")
        ChessGame.objects.create(white_user=user, white_player="Player", black_player="Coach", status="finished", result="black", category="casual")
        self.client.force_login(user)
        response = self.client.get(reverse("profile_stats"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["match_stats"], {"total": 3, "wins": 1, "draws": 1, "losses": 1, "win_rate": 33})
        self.assertContains(response, 'id="profile-games" checked')
        self.assertContains(response, 'id="profile-learning"')

    def test_empty_profile_has_zero_win_rate(self):
        user = User.objects.create_user(username="empty-profile")
        self.client.force_login(user)
        response = self.client.get(reverse("profile_stats"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["match_stats"]["win_rate"], 0)
