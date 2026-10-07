"""Private round-robin tournaments reuse the normal game and clock rules."""
from collections import defaultdict
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from .i18n import current_language
from .models import Tournament, TournamentEntry, TournamentMatch, ChessGame
from .tournament_texts import TEXTS
from .views import rate_limit


class TournamentForm(forms.Form):
    name = forms.CharField(max_length=80, strip=True)
    max_players = forms.TypedChoiceField(choices=[(n,str(n)) for n in (4,8,12,16)], coerce=int, initial=8)
    time_control_minutes = forms.TypedChoiceField(choices=[(n,str(n)) for n in (3,5,10,15,30)], coerce=int, initial=10)

    def __init__(self, *args, language='pt', **kwargs):
        super().__init__(*args, **kwargs)
        for key, field in self.fields.items():
            field.label = TEXTS[language][{'max_players':'capacity','time_control_minutes':'minutes'}.get(key,key)]


def round_robin(players):
    """Circle scheduling: no repeated opponents or double bookings in a round."""
    ring = list(players)
    if len(ring) % 2: ring.append(None)
    rounds = []
    for number in range(len(ring)-1):
        pairs = []
        for i in range(len(ring)//2):
            a,b = ring[i],ring[-1-i]
            if a is None: a,b = b,a
            elif b is not None and i == 0 and number % 2: a,b = b,a
            pairs.append((a,b))
        rounds.append(pairs)
        ring = [ring[0],ring[-1],*ring[1:-1]]
    return rounds


def open_round(tournament, number):
    from .views import build_initial_clock_settings
    for match in tournament.matches.filter(round_number=number, black__isnull=False, game__isnull=True).select_related('white','black'):
        match.game = ChessGame.objects.create(owner=match.white, white_user=match.white, black_user=match.black,
            white_player=match.white.username, black_player=match.black.username,
            title=f'{tournament.name} · {number}', category='casual', is_rated=False,
            time_control_minutes=tournament.time_control_minutes, **build_initial_clock_settings(tournament.time_control_minutes))
        match.save(update_fields=['game'])
    tournament.current_round = number
    tournament.save(update_fields=['current_round'])


@transaction.atomic
def advance_tournament(tournament_id):
    tournament = Tournament.objects.select_for_update().get(pk=tournament_id)
    if tournament.status != 'active': return
    matches = list(tournament.matches.filter(round_number=tournament.current_round,black__isnull=False).select_related('game'))
    if not matches or any(not m.game_id or m.game.status != 'finished' or m.game.result not in ('white','black','draw') for m in matches): return
    next_round = tournament.current_round+1
    if tournament.matches.filter(round_number=next_round).exists():
        open_round(tournament,next_round)
    else:
        tournament.status = 'finished'
        tournament.finished_at = timezone.now()
        tournament.save(update_fields=['status','finished_at'])


def settle_expired_clocks(tournament):
    """A player waiting on standings must still receive results for expired clocks."""
    from .views import finish_clock_if_expired
    ids=list(tournament.matches.filter(round_number=tournament.current_round,game__status='draft').values_list('game_id',flat=True))
    if not ids:return
    # Release game locks before the after-commit progression callback takes a tournament lock.
    with transaction.atomic():
        for game in ChessGame.objects.select_for_update().filter(pk__in=ids).order_by('pk'):
            finish_clock_if_expired(game)


def standings(tournament, entries, matches):
    rows = {entry.user_id:dict(user=entry.user,points=0,wins=0,draws=0,losses=0) for entry in entries}
    for match in matches:
        if match.round_number > tournament.current_round: continue
        if not match.black_id:
            rows[match.white_id]['points'] += 2
            continue
        if not match.game_id or match.game.status != 'finished': continue
        result = match.game.result
        if result == 'draw':
            for uid in (match.white_id,match.black_id): rows[uid]['points']+=1;rows[uid]['draws']+=1
        elif result in ('white','black'):
            winner,loser = (match.white_id,match.black_id) if result=='white' else (match.black_id,match.white_id)
            rows[winner]['points']+=2;rows[winner]['wins']+=1;rows[loser]['losses']+=1
    ordered = sorted(rows.values(),key=lambda row:(-row['points'],row['user'].username.casefold()))
    last = None
    rank = 0
    for index,row in enumerate(ordered,1):
        if row['points'] != last: rank=index
        last=row['points'];row['rank']=rank
        row['score']=str(row['points']//2)+('½' if row['points']%2 else '')
        if row['score']=='0½':row['score']='½'
    return ordered


def revision(tournament):
    return [tournament.status,tournament.current_round,tournament.entries.count(),list(tournament.matches.filter(round_number__lte=tournament.current_round).values_list('pk','game__status','game__result'))]


@login_required
def tournament_list(request):
    tournaments = Tournament.objects.filter(entries__user=request.user).select_related('creator').distinct()
    return render(request,'games/tournaments.html',{'tournaments':tournaments,'t':TEXTS[current_language(request)]})


@login_required
@rate_limit(20,60,'tournament-create')
def tournament_create(request):
    texts=TEXTS[current_language(request)]
    form=TournamentForm(request.POST or None,language=current_language(request))
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            tournament=Tournament.objects.create(creator=request.user,**form.cleaned_data)
            TournamentEntry.objects.create(tournament=tournament,user=request.user)
        return redirect('tournament_detail',token=tournament.token)
    return render(request,'games/tournament_create.html',{'form':form,'t':texts})


@login_required
@never_cache
def tournament_detail(request, token):
    tournament=get_object_or_404(Tournament.objects.select_related('creator'),token=token)
    entries=list(tournament.entries.select_related('user'))
    member=any(entry.user_id==request.user.pk for entry in entries)
    matches=list(tournament.matches.select_related('white','black','game')) if member else []
    own_match=next((match for match in matches if match.round_number==tournament.current_round and request.user.pk in (match.white_id,match.black_id)),None)
    rounds=defaultdict(list)
    for match in matches: rounds[match.round_number].append(match)
    return render(request,'games/tournament_detail.html',dict(tournament=tournament,t=TEXTS[current_language(request)],
        entries=entries,member=member,is_owner=tournament.creator_id==request.user.pk,own_match=own_match,
        table=standings(tournament,entries,matches) if member else [],rounds=sorted(rounds.items()),
        share_url=request.build_absolute_uri(reverse('tournament_detail',args=[token])),snapshot=revision(tournament),
        notice=TEXTS[current_language(request)].get(request.GET.get('notice'),'') ))


@login_required
@require_POST
@rate_limit(60,60,'tournament-action')
def tournament_action(request, token):
    action=request.POST.get('action')
    notice=''
    with transaction.atomic():
        tournament=get_object_or_404(Tournament.objects.select_for_update(),token=token)
        entries=tournament.entries
        owner=tournament.creator_id==request.user.pk
        if action=='join':
            if entries.filter(user=request.user).exists(): pass
            elif tournament.status!='lobby':notice='closed'
            elif entries.count()>=tournament.max_players:notice='full'
            else:TournamentEntry.objects.create(tournament=tournament,user=request.user)
        elif action=='leave':
            if tournament.status!='lobby':notice='closed'
            elif owner:notice='owner_only'
            else:entries.filter(user=request.user).delete()
        elif action in ('start','cancel'):
            if not owner:return HttpResponseForbidden()
            if tournament.status!='lobby':notice='closed'
            elif action=='cancel':
                tournament.status='cancelled';tournament.save(update_fields=['status'])
            elif entries.count()<2:notice='min_players'
            else:
                players=list(entries.values_list('user_id',flat=True))
                schedule=round_robin(players)
                TournamentMatch.objects.bulk_create([TournamentMatch(tournament=tournament,round_number=number,board_number=board,white_id=a,black_id=b) for number,pairs in enumerate(schedule,1) for board,(a,b) in enumerate(pairs,1)])
                tournament.status='active';tournament.started_at=timezone.now()
                tournament.save(update_fields=['status','started_at'])
                open_round(tournament,1)
        else:return HttpResponseBadRequest()
    url=reverse('tournament_detail',args=[token])
    return redirect(url+('?notice='+notice if notice else ''))


@login_required
@require_GET
@never_cache
def tournament_state(request, token):
    tournament=get_object_or_404(Tournament,token=token)
    if not tournament.entries.filter(user=request.user).exists(): return HttpResponseForbidden()
    if tournament.status == 'active':settle_expired_clocks(tournament)
    # Recover safely if a previous after-commit callback was interrupted.
    advance_tournament(tournament.pk)
    tournament.refresh_from_db()
    return JsonResponse({'revision':revision(tournament)})
