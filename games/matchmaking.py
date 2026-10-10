"""Match only active searches with identical rules; invitations remain authoritative."""
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Value, Q, Case, When, IntegerField
from django.db.models.functions import Abs, Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import GameInvitation
from .views import rate_limit

LIVE_SECONDS = 45

def start_search(user, *, color, rated, blindfold, minutes, guest_id='', guest_name=''):
    authenticated = user.is_authenticated
    if not authenticated and (not guest_id or rated):
        raise ValueError("Guests require a session and unrated games")
    with transaction.atomic():
        # Serialize repeated submissions by the same account.
        if authenticated:
            User.objects.select_for_update().get(pk=user.pk)
        owner = Q(creator=user) if authenticated else Q(creator__isnull=True, creator_guest_id=guest_id)
        own = GameInvitation.objects.filter(owner, status='pending', opponent_mode='random', search_seen_at__isnull=False).order_by('-pk')
        invitation = own.filter(creator_color=color, is_rated=rated, blindfold_only=blindfold, time_control_minutes=minutes).first()
        if invitation is None:
            own.update(status='cancelled', responded_at=timezone.now())
            invitation = GameInvitation.objects.create(creator=user if authenticated else None, creator_guest_id='' if authenticated else guest_id, creator_guest_name='' if authenticated else guest_name, opponent_mode='random', creator_color=color, is_rated=rated, blindfold_only=blindfold, time_control_minutes=minutes, search_seen_at=timezone.now())
        return invitation

def match_search(user, invitation_id, guest_id='', guest_name=''):
    authenticated = user.is_authenticated
    owner = Q(creator=user) if authenticated else (Q(creator__isnull=True, creator_guest_id=guest_id) if guest_id else Q(pk__in=[]))
    from .views import create_game_from_invitation
    with transaction.atomic():
        own = get_object_or_404(GameInvitation.objects.select_for_update(), owner, pk=invitation_id, opponent_mode='random', search_seen_at__isnull=False)
        if own.status != 'pending':
            return own
        now = timezone.now()
        own.search_seen_at = now
        own.save(update_fields=['search_seen_at'])
        # Only lock older searches: simultaneous polls cannot form a lock cycle.
        peers = GameInvitation.objects.select_for_update(of=('self',)).filter(pk__lt=own.pk, status='pending', opponent_mode='random', opponent__isnull=True,  search_seen_at__gte=now-timedelta(seconds=LIVE_SECONDS), is_rated=own.is_rated, blindfold_only=own.blindfold_only, time_control_minutes=own.time_control_minutes).filter(Q(creator__is_active=True) | Q(creator__isnull=True, creator_guest_id__gt=''))
        peers = peers.exclude(creator=user) if authenticated else peers.exclude(creator_guest_id=guest_id)
        if own.creator_color != 'random':
            peers = peers.filter(creator_color__in=['random', 'black' if own.creator_color == 'white' else 'white'])
        from accounts.models import PlayerProfile
        rating = (PlayerProfile.objects.filter(user=user).values_list('elo', flat=True).first() or 1200) if authenticated else 800
        peer = peers.annotate(rating_gap=Abs(Case(When(creator__isnull=True, then=Value(800)), default=Coalesce(F('creator__player_profile__elo'), Value(1200)), output_field=IntegerField()) - Value(rating))).order_by('rating_gap', 'pk').first()
        if peer is None:
            return own
        # A random preference must respect the other player's explicit color.
        if peer.creator_color == 'random' and own.creator_color != 'random':
            peer.creator_color = 'black' if own.creator_color == 'white' else 'white'
        peer.opponent = user if authenticated else None
        peer.status = 'accepted'
        peer.responded_at = now
        peer.save(update_fields=['creator_color', 'opponent', 'status', 'responded_at'])
        game = create_game_from_invitation(peer, user if authenticated else None, guest_id if not authenticated else '', guest_name)
        peer.game = game
        peer.save(update_fields=['game'])
        own.opponent = peer.creator
        own.game = game
        own.status = 'accepted'
        own.responded_at = now
        own.save(update_fields=['opponent', 'game', 'status', 'responded_at'])
        return own

@require_POST
@rate_limit(40, 60, "search-tick")
def search_tick(request, invitation_id):
    invitation = match_search(request.user, invitation_id, request.session.get('guest_id', ''), request.session.get('guest_name', ''))
    response = JsonResponse({'status':invitation.status, 'game_url':reverse('game_detail',args=[invitation.game_id]) if invitation.game_id else None})
    response['Cache-Control'] = 'private, no-store'
    return response

@require_POST
@rate_limit(10, 60, "quick-play")
def quick_play(request):
    from django.shortcuts import redirect
    from .views import guest_id_for_request, guest_name_for_request
    guest_id = '' if request.user.is_authenticated else guest_id_for_request(request)
    guest_name = '' if request.user.is_authenticated else guest_name_for_request(request)
    invitation = start_search(request.user, color='random', rated=False, blindfold=False, minutes=5, guest_id=guest_id, guest_name=guest_name)
    invitation = match_search(request.user, invitation.pk, guest_id, guest_name)
    if invitation.game_id:
        return redirect('game_detail', game_id=invitation.game_id)
    return redirect('game_invitation_wait', invitation_id=invitation.pk)
