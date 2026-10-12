from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from .models import GameInvitation

class InvitationEntryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.creator=User.objects.create_user('invite_creator')
        self.invitation=GameInvitation.objects.create(creator=self.creator,opponent_mode='link',creator_color='white')
        self.url=reverse('accept_invitation_link',args=[self.invitation.token])
    def test_preview_does_not_take_opponent_slot(self):
        self.assertEqual(Client().get(self.url).status_code,200)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status,'pending')
        opponent=Client()
        response=opponent.post(self.url)
        self.invitation.refresh_from_db()
        self.assertRedirects(response,reverse('game_detail',args=[self.invitation.game_id]))
        creator=Client();creator.force_login(self.creator)
        self.assertEqual(creator.get(reverse('invitation_status',args=[self.invitation.pk])).json()['game_id'],self.invitation.game_id)
        self.assertRedirects(opponent.get(self.url),reverse('game_detail',args=[self.invitation.game_id]))
    def test_used_link_explains_problem_instead_of_list_redirect(self):
        Client().post(self.url)
        response=Client().get(self.url)
        self.assertEqual(response.status_code,409)
        self.assertContains(response,'invitation',status_code=409)
    def test_rated_login_preserves_invitation(self):
        self.invitation.is_rated=True;self.invitation.save()
        response=self.client.get(self.url)
        self.assertEqual(response.status_code,302)
        self.assertIn('next=',response.url)
        self.assertIn(self.url,response.url)
