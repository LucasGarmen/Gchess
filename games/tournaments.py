"""Round-robin tournaments reuse the normal game and clock rules."""
from collections import defaultdict
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from .i18n import current_language
from .models import Tournament, TournamentEntry, TournamentMatch, ChessGame, TournamentNotice, Friendship
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password
from .tournament_texts import TEXTS
from .views import rate_limit


class TournamentForm(forms.Form):
    name = forms.CharField(max_length=80, strip=True)
    visibility = forms.ChoiceField(choices=[('private','Private'),('public','Public')], initial='private')
    password = forms.CharField(required=False, max_length=128, strip=False, widget=forms.PasswordInput(attrs={'autocomplete':'new-password','minlength':6}))
    max_players = forms.TypedChoiceField(choices=[(n,str(n)) for n in (4,8,12,16)], coerce=int, initial=8)
    time_control_minutes = forms.TypedChoiceField(choices=[(n,str(n)) for n in (3,5,10,15,30)], coerce=int, initial=10)

    def __init__(self, *args, language='pt', **kwargs):
        super().__init__(*args, **kwargs)
        for key, field in self.fields.items():
            field.label = TEXTS[language][{'max_players':'capacity','time_control_minutes':'minutes'}.get(key,key)]
        self.texts=TEXTS[language]
        self.fields['visibility'].choices=[(key,self.texts[key]) for key in ('private','public')]
        self.fields['visibility'].help_text=self.texts['visibility_help']
        self.fields['password'].help_text=self.texts['password_help']

    def clean(self):
        data=super().clean()
        if data.get('visibility')=='private' and (not data.get('password','').strip() or len(data.get('password',''))<6):
            self.add_error('password',self.texts['password_required'])
        return data


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
    TournamentNotice.objects.bulk_create([TournamentNotice(tournament=tournament,user_id=uid,kind='round',round_number=number) for uid in tournament.entries.values_list('user_id',flat=True)], ignore_conflicts=True)
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


@never_cache
def tournament_list(request):
    # Count every player, not just the current account's matching join row.
    mine_ids=TournamentEntry.objects.filter(user=request.user).values_list('tournament_id',flat=True) if request.user.is_authenticated else []
    tournaments=Tournament.objects.filter(pk__in=mine_ids).select_related('creator').annotate(player_count=Count('entries')).order_by('-created_at','-pk')
    status=request.GET.get('status','lobby')
    if status not in ('lobby','active','finished'):status='lobby'
    public=Tournament.objects.filter(visibility='public',status=status).select_related('creator').annotate(player_count=Count('entries')).order_by('-created_at')
    return render(request,'games/tournaments.html',{'tournaments':Paginator(tournaments,12).get_page(request.GET.get('mine_page')),'public_tournaments':Paginator(public,12).get_page(request.GET.get('page')),'public_status':status,'t':TEXTS[current_language(request)]})


@login_required
@rate_limit(20,60,'tournament-create')
def tournament_create(request):
    texts=TEXTS[current_language(request)]
    form=TournamentForm(request.POST or None,language=current_language(request))
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            data=dict(form.cleaned_data);password=data.pop('password','')
            tournament=Tournament.objects.create(creator=request.user,password_hash=make_password(password) if data['visibility']=='private' else '',**data)
            TournamentEntry.objects.create(tournament=tournament,user=request.user)
        return redirect('tournament_detail',token=tournament.token)
    return render(request,'games/tournament_create.html',{'form':form,'t':texts})


@never_cache
def tournament_detail(request, token):
    tournament=get_object_or_404(Tournament.objects.select_related('creator'),token=token)
    texts=TEXTS[current_language(request)]
    if not request.user.is_authenticated and tournament.visibility != 'public':
        return redirect_to_login(request.get_full_path())
    member=request.user.is_authenticated and tournament.entries.filter(user=request.user).exists()
    if tournament.visibility=='private' and not member and tournament.creator_id!=request.user.pk:
        return render(request,'games/tournament_locked.html',dict(tournament=tournament,t=texts,player_count=tournament.entries.count(),notice=texts.get(request.GET.get('notice'),'')))
    entries=list(tournament.entries.select_related('user'))
    friends=[]
    if tournament.creator_id==request.user.pk and tournament.status=='lobby':
        invited=set(tournament.notices.filter(kind='invite').values_list('user_id',flat=True))
        joined={entry.user_id for entry in entries}
        for pair in Friendship.objects.filter(Q(low_user=request.user)|Q(high_user=request.user),status='accepted').select_related('low_user','high_user'):
            friend=pair.high_user if pair.low_user_id==request.user.pk else pair.low_user
            if friend.pk not in joined:friends.append(dict(user=friend,invited=friend.pk in invited))
        friends.sort(key=lambda row:row['user'].username.casefold())
    if request.user.is_authenticated:
        TournamentNotice.objects.filter(tournament=tournament,user=request.user,kind='round',round_number__lte=tournament.current_round).update(read=True)
    if any(entry.user_id==request.user.pk for entry in entries):
        TournamentNotice.objects.filter(tournament=tournament,user=request.user,kind='invite').update(read=True)
    member=any(entry.user_id==request.user.pk for entry in entries)
    matches=list(tournament.matches.select_related('white','black','game')) if member or tournament.visibility=='public' else []
    own_match=next((match for match in matches if request.user.is_authenticated and match.round_number==tournament.current_round and request.user.pk in (match.white_id,match.black_id)),None)
    rounds=defaultdict(list)
    for match in matches: rounds[match.round_number].append(match)
    return render(request,'games/tournament_detail.html',dict(tournament=tournament,t=TEXTS[current_language(request)],
        friends=friends,entries=entries,member=member,is_owner=tournament.creator_id==request.user.pk,own_match=own_match,
        table=standings(tournament,entries,matches) if matches else [],rounds=sorted(rounds.items()),
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
        if action=='invite':
            if not owner:return HttpResponseForbidden()
            if tournament.status!='lobby':notice='closed'
            elif entries.count()>=tournament.max_players:notice='full'
            else:
                try:uid=int(request.POST.get('friend_id',''))
                except ValueError:return HttpResponseBadRequest()
                low,high=sorted((request.user.pk,uid))
                if not Friendship.objects.filter(low_user_id=low,high_user_id=high,status='accepted').exists():return HttpResponseForbidden()
                if not entries.filter(user_id=uid).exists():
                    TournamentNotice.objects.get_or_create(tournament=tournament,user_id=uid,kind='invite')
                notice='sent'
        elif action=='password':
            if not owner:return HttpResponseForbidden()
            if tournament.status!='lobby' or tournament.visibility!='private':notice='closed'
            else:
                password=request.POST.get('password','')
                if not password.strip() or not 6<=len(password)<=128:notice='password_required'
                else:
                    tournament.password_hash=make_password(password);tournament.save(update_fields=['password_hash']);notice='password_saved'
        elif action=='join':
            if entries.filter(user=request.user).exists(): pass
            elif tournament.status!='lobby':notice='closed'
            elif entries.count()>=tournament.max_players:notice='full'
            else:
                if tournament.visibility=='private':
                    response=verify_tournament_password(request,tournament)
                    if response is not None:return response
                TournamentEntry.objects.create(tournament=tournament,user=request.user)
        elif action=='leave':
            if tournament.status!='lobby':notice='closed'
            elif owner:notice='owner_only'
            else:entries.filter(user=request.user).delete()
        elif action in ('start','cancel'):
            if not owner:return HttpResponseForbidden()
            if tournament.status!='lobby':notice='closed'
            elif action=='cancel':
                tournament.status='cancelled';tournament.save(update_fields=['status'])
            elif tournament.visibility=='private' and not tournament.password_hash:notice='password_required'
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


def notification_items(user,language):
    texts=TEXTS[language]
    notices=TournamentNotice.objects.filter(user=user,read=False).filter(
        Q(kind='invite',tournament__status='lobby') | Q(kind='round',tournament__status='active',round_number=F('tournament__current_round'))
    ).select_related('tournament').order_by('-created_at')[:16]
    return [dict(id=n.pk,label=(texts['invite_notice'] if n.kind=='invite' else texts['round_notice']).format(name=n.tournament.name,round=n.round_number),url=reverse('tournament_detail',args=[n.tournament.token]),dismiss_url=reverse('tournament_notice_read',args=[n.pk]),open_label=texts['view'],dismiss_label=texts['dismiss']) for n in notices]

@login_required
@require_POST
def tournament_notice_read(request,notice_id):
    notice=get_object_or_404(TournamentNotice,pk=notice_id,user=request.user)
    notice.read=True;notice.save(update_fields=['read'])
    return JsonResponse({'ok':True})


@rate_limit(8,60,'tournament-password-check')
def verify_tournament_password(request,tournament):
    raw=request.POST.get('password','')
    if not tournament.password_hash or not raw or len(raw)>128 or not check_password(raw,tournament.password_hash):
        return redirect(reverse('tournament_detail',args=[tournament.token])+'?notice=wrong_password')
    return None
