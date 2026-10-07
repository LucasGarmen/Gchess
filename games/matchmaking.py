"""Match only active searches with identical rules; invitations remain authoritative."""
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import GameInvitation
from .views import rate_limit

LIVE_SECONDS = 45

def start_search(user, *, color, rated, blindfold, minutes):
    with transaction.atomic():
        # Serialize repeated submissions by the same account.
        User.objects.select_for_update().get(pk=user.pk)
        own = GameInvitation.objects.filter(creator=user, status='pending', opponent_mode='random', search_seen_at__isnull=False).order_by('-pk')
        invitation = own.filter(creator_color=color, is_rated=rated, blindfold_only=blindfold, time_control_minutes=minutes).first()
        if invitation is None:
            own.update(status='cancelled', responded_at=timezone.now())
            invitation = GameInvitation.objects.create(creator=user, opponent_mode='random', creator_color=color, is_rated=rated, blindfold_only=blindfold, time_control_minutes=minutes, search_seen_at=timezone.now())
        return invitation

def match_search(user, invitation_id):
    from .views import create_game_from_invitation
    with transaction.atomic():
        own = get_object_or_404(GameInvitation.objects.select_for_update(), pk=invitation_id, creator=user, opponent_mode='random', search_seen_at__isnull=False)
        if own.status != 'pending':
            return own
        now = timezone.now()
        own.search_seen_at = now
        own.save(update_fields=['search_seen_at'])
        # Only lock older searches: simultaneous polls cannot form a lock cycle.
        peers = GameInvitation.objects.select_for_update().filter(pk__lt=own.pk, status='pending', opponent_mode='random', opponent__isnull=True, creator__isnull=False, creator__is_active=True, search_seen_at__gte=now-timedelta(seconds=LIVE_SECONDS), is_rated=own.is_rated, blindfold_only=own.blindfold_only, time_control_minutes=own.time_control_minutes).exclude(creator=user)
        if own.creator_color != 'random':
            peers = peers.filter(creator_color__in=['random', 'black' if own.creator_color == 'white' else 'white'])
        peer = peers.order_by('pk').first()
        if peer is None:
            return own
        # A random preference must respect the other player's explicit color.
        if peer.creator_color == 'random' and own.creator_color != 'random':
            peer.creator_color = 'black' if own.creator_color == 'white' else 'white'
        peer.opponent = user
        peer.status = 'accepted'
        peer.responded_at = now
        peer.save(update_fields=['creator_color', 'opponent', 'status', 'responded_at'])
        game = create_game_from_invitation(peer, user)
        peer.game = game
        peer.save(update_fields=['game'])
        own.opponent = peer.creator
        own.game = game
        own.status = 'accepted'
        own.responded_at = now
        own.save(update_fields=['opponent', 'game', 'status', 'responded_at'])
        return own

@login_required
@require_POST
@rate_limit(40, 60, "search-tick")
def search_tick(request, invitation_id):
    invitation = match_search(request.user, invitation_id)
    response = JsonResponse({'status':invitation.status, 'game_url':reverse('game_detail',args=[invitation.game_id]) if invitation.game_id else None})
    response['Cache-Control'] = 'private, no-store'
    return response
