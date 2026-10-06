from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .i18n import current_language
from .models import ChessGame, Friendship, GameInvitation
from .social_texts import SOCIAL_TEXTS
from .views import rate_limit, touch_presence


def pair_query(user, other):
    return dict(low_user_id=min(user.pk, other.pk), high_user_id=max(user.pk, other.pk))


@login_required
def friends(request):
    touch_presence(request.user)
    texts = SOCIAL_TEXTS[current_language(request)]
    relations = list(Friendship.objects.filter(Q(low_user=request.user) | Q(high_user=request.user))
                     .select_related('low_user', 'high_user', 'requester'))
    by_user = {(r.high_user_id if r.low_user_id == request.user.pk else r.low_user_id): r for r in relations}
    friend_ids = [uid for uid, r in by_user.items() if r.status == 'accepted']
    people = list(User.objects.filter(pk__in=friend_ids, is_active=True).select_related('presence', 'player_profile', 'puzzle_stats', 'blitz_best_result', 'streak_best_result'))
    finished = ChessGame.objects.filter(status='finished').filter(
        Q(white_user=request.user, black_user_id__in=friend_ids) | Q(black_user=request.user, white_user_id__in=friend_ids))
    history = {uid: dict(wins=0, losses=0, draws=0) for uid in friend_ids}
    for game in finished.only('white_user_id', 'black_user_id', 'result'):
        own_white = game.white_user_id == request.user.pk
        uid = game.black_user_id if own_white else game.white_user_id
        if game.result == 'draw': history[uid]['draws'] += 1
        elif game.result in ('white', 'black'):
            history[uid]['wins' if (game.result == 'white') == own_white else 'losses'] += 1
    def row(person):
        presence = getattr(person, 'presence', None)
        return dict(user=person, online=bool(presence and presence.last_seen >= timezone.now()-timezone.timedelta(seconds=60)),
                    elo=getattr(getattr(person, 'player_profile', None), 'elo', None),
                    puzzles=getattr(getattr(person, 'puzzle_stats', None), 'puzzle_rating', None),
                    blitz=getattr(getattr(person, 'blitz_best_result', None), 'score', None),
                    streak=getattr(getattr(person, 'streak_best_result', None), 'mejor_racha', None),
                    history=history.get(person.pk))
    rows = [row(person) for person in people]
    me = User.objects.select_related('player_profile','puzzle_stats','blitz_best_result','streak_best_result').get(pk=request.user.pk)
    metric = request.GET.get('metric', 'puzzles')
    if metric not in ('puzzles', 'elo', 'blitz', 'streak'): metric = 'puzzles'
    ranking = sorted(rows + [row(me)], key=lambda r: (-(r[metric] if r[metric] is not None else -1), r['user'].username.casefold()))
    for r in ranking: r['value'] = r[metric]
    query = request.GET.get('q', '').strip()[:150]
    results = []
    if len(query) >= 2:
        for person in User.objects.filter(is_active=True, username__icontains=query).exclude(pk=request.user.pk).order_by('username')[:20]:
            relation = by_user.get(person.pk)
            results.append(dict(user=person, state=relation.status if relation else '', incoming=bool(relation and relation.requester_id != request.user.pk)))
    incoming = [r for r in relations if r.status == 'pending' and r.requester_id != request.user.pk]
    outgoing = [dict(relation=r, user=r.high_user if r.low_user_id == request.user.pk else r.low_user) for r in relations if r.status == 'pending' and r.requester_id == request.user.pk]
    return render(request, 'games/friends.html', dict(s=texts, friends=rows, incoming=incoming, outgoing=outgoing,
                  results=results, query=query, ranking=ranking, metric=metric, feedback=texts.get(request.GET.get('notice',''), '')))


@login_required
@require_POST
@rate_limit(20, 60, 'friend-action')
def friend_action(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)
    if other == request.user: return HttpResponseBadRequest()
    action = request.POST.get('action')
    notice = 'updated'
    with transaction.atomic():
        # Serialize opposite requests and transitions on the same canonical pair.
        list(User.objects.select_for_update().filter(pk__in=[request.user.pk, other.pk]).order_by('pk'))
        relation = Friendship.objects.filter(**pair_query(request.user, other)).first()
        if action == 'send':
            if not relation:
                Friendship.objects.create(**pair_query(request.user, other), requester=request.user)
                notice = 'sent'
        elif action == 'accept':
            if not relation or relation.status != 'pending' or relation.requester_id == request.user.pk:
                return HttpResponseBadRequest()
            relation.status = 'accepted'
            relation.save(update_fields=['status'])
        elif action in ('decline', 'cancel', 'remove'):
            valid = relation and ((action == 'remove' and relation.status == 'accepted') or
                (relation.status == 'pending' and ((action == 'cancel') == (relation.requester_id == request.user.pk))))
            if not valid: return HttpResponseBadRequest()
            relation.delete()
        else: return HttpResponseBadRequest()
    return redirect('/friends/?' + urlencode({'notice': notice}))


@login_required
@require_POST
@rate_limit(10, 60, 'friend-challenge')
def friend_challenge(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)
    if other == request.user: return HttpResponseBadRequest()
    if not Friendship.objects.filter(**pair_query(request.user, other), status='accepted').exists():
        return HttpResponseBadRequest()
    minutes = request.POST.get('minutes', '10')
    if minutes not in ('3', '5', '10', '15'): return HttpResponseBadRequest()
    kind = request.POST.get('kind', 'casual')
    if kind not in ('casual', 'ranked'): return HttpResponseBadRequest()
    with transaction.atomic():
        list(User.objects.select_for_update().filter(pk__in=[request.user.pk, other.pk]).order_by('pk'))
        if not Friendship.objects.filter(**pair_query(request.user, other), status='accepted').exists():
            return HttpResponseBadRequest()
        invitation = GameInvitation.objects.filter(creator=request.user, opponent=other, status='pending', opponent_mode='direct', time_control_minutes=int(minutes), is_rated=kind == 'ranked').first()
        if not invitation:
            invitation = GameInvitation.objects.create(creator=request.user, opponent=other, opponent_mode='direct', creator_color='random', is_rated=kind == 'ranked', time_control_minutes=int(minutes))
    return redirect('game_invitation_wait', invitation_id=invitation.pk)
