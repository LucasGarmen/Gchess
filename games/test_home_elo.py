from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PlayerProfile
from .models import ChessGame


class HomeEloTests(TestCase):
    def test_ranking_orders_active_rated_players_and_excludes_unplayed_accounts(self):
        a = User.objects.create_user(username='RatedA')
        b = User.objects.create_user(username='RatedB')
        c = User.objects.create_user(username='Unplayed')
        for user, elo in [(a, 1500), (b, 1700), (c, 2500)]:
            PlayerProfile.objects.update_or_create(user=user, defaults={'elo': elo})
        ChessGame.objects.create(white_user=a, black_user=b, white_player=a.username, black_player=b.username, status='finished', result='draw', is_rated=True, rating_applied=True)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p.user_id for p in response.context['elo_leaders']], [b.pk, a.pk])
        self.assertContains(response, 'home-elo-ranking')
        self.assertNotContains(response, 'Unplayed')
        b.is_active = False
        b.save()
        self.assertEqual([p.user_id for p in self.client.get('/').context['elo_leaders']], [a.pk])

    def test_empty_ranking_is_rendered_for_visitors(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'home-elo-empty')
