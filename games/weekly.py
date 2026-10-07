"""A frozen common weekly set; only the first attempt earns points."""
import json
import random
from datetime import datetime,time,timedelta,timezone as dt_timezone
from functools import lru_cache
import chess
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest,JsonResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .models import WeeklyChallenge,WeeklyChallengeEntry,Friendship
from .weekly_texts import TEXTS
from .daily_training_texts import TEXTS as BOARD_TEXTS
from .daily_training import explanation
from .i18n import current_language
from .views import rate_limit


def week_start(date=None):
    date=date or timezone.now().astimezone(dt_timezone.utc).date()
    return date-timedelta(days=date.weekday())


def end_time(challenge):
    return datetime.combine(challenge.week_start+timedelta(days=7),time.min,tzinfo=dt_timezone.utc)


@lru_cache(maxsize=1)
def verified_library():
    from .puzzles import PRACTICE_PUZZLES
    positions={}
    for puzzle in PRACTICE_PUZZLES:
        if puzzle.get('mate_in')!=1:continue
        original=chess.Board(puzzle['fen'])
        for board in (original,original.mirror(),original.transform(chess.flip_horizontal),original.mirror().transform(chess.flip_horizontal)):
            board.castling_rights=chess.BB_EMPTY
            if not board.is_valid() or board.is_game_over():continue
            for move in list(board.legal_moves):
                after=board.copy();after.push(move)
                if after.is_checkmate():
                    positions[board.fen()]=dict(fen=board.fen(),solution=move.uci());break
    return tuple(positions[key] for key in sorted(positions))


def build_tasks(start):
    rng=random.Random('gchess-weekly-v1:'+start.isoformat())
    white=[dict(task) for task in verified_library() if chess.Board(task['fen']).turn]
    black=[dict(task) for task in verified_library() if not chess.Board(task['fen']).turn]
    rng.shuffle(white);rng.shuffle(black)
    tasks=white[:3]+black[:2];rng.shuffle(tasks)
    if len(tasks)!=5:raise ValueError('Insufficient verified weekly positions')
    return tasks


def attempt_count(entry):return sum(p['attempted'] for p in entry.progress)


def standings(user,challenge):
    ids={user.pk}
    for pair in Friendship.objects.filter(Q(low_user=user)|Q(high_user=user),status='accepted'):
        ids.add(pair.high_user_id if pair.low_user_id==user.pk else pair.low_user_id)
    entries={e.user_id:e for e in WeeklyChallengeEntry.objects.filter(challenge=challenge,user_id__in=ids)} if challenge else {}
    rows=[]
    for person in User.objects.filter(pk__in=ids,is_active=True):
        entry=entries.get(person.pk);attempts=attempt_count(entry) if entry else 0
        rows.append(dict(user=person,score=entry.score if entry else 0,attempts=attempts,participating=bool(attempts),rank=None))
    rows.sort(key=lambda row:(not row['participating'],-row['score'],row['user'].username.casefold()))
    last=None;rank=0
    for index,row in enumerate(rows,1):
        if not row['participating']:continue
        if row['score']!=last:rank=index
        row['rank']=rank;last=row['score']
    return rows


@login_required
@never_cache
def weekly_challenge(request):
    start=week_start();challenge=WeeklyChallenge.objects.filter(week_start=start).first()
    entry=WeeklyChallengeEntry.objects.filter(challenge=challenge,user=request.user).first() if challenge else None
    history=WeeklyChallengeEntry.objects.filter(user=request.user,challenge__week_start__lt=start).select_related('challenge').order_by('-challenge__week_start')
    past=Paginator(history,12).get_page(request.GET.get('history_page'))
    return render(request,'games/weekly.html',dict(weekly=TEXTS[current_language(request)],start=start,
        end=datetime.combine(start+timedelta(days=7),time.min,tzinfo=dt_timezone.utc),entry=entry,
        attempts=attempt_count(entry) if entry else 0,rows=standings(request.user,challenge),history=past))


@login_required
@require_POST
@rate_limit(15,60,'weekly-start')
def weekly_start(request):
    start=week_start()
    challenge=WeeklyChallenge.objects.filter(week_start=start).first()
    if not challenge:
        tasks=build_tasks(start)
        challenge,_=WeeklyChallenge.objects.get_or_create(week_start=start,defaults={'tasks':tasks})
    with transaction.atomic():
        User.objects.select_for_update().get(pk=request.user.pk)
        entry,_=WeeklyChallengeEntry.objects.get_or_create(challenge=challenge,user=request.user,
            defaults={'progress':[dict(attempted=False,first_correct=False,resolved=False,helped=False) for task in challenge.tasks]})
    return redirect('weekly_play',entry_id=entry.pk)


def board_texts(language):
    texts=dict(BOARD_TEXTS[language]);weekly=TEXTS[language]
    for key in ('title','intro','hint','reveal','finish','summary','independent','helped'):texts[key]=weekly[key]
    texts['fallback']=weekly['origin'];texts['goal_mate']=weekly['goal'];texts['review_help']=weekly['rules']
    return texts


def state_for(entry,language,practice=False,practice_index=0):
    index=practice_index if practice else next((i for i,p in enumerate(entry.progress) if not p['resolved']),len(entry.progress))
    texts=BOARD_TEXTS[language];task=None
    if index<len(entry.challenge.tasks):
        saved=entry.challenge.tasks[index];board=chess.Board(saved['fen'])
        task=dict(fen=board.fen(),legal_moves=[move.uci() for move in board.legal_moves],personal=False,source_url=None,
            turn=texts['white' if board.turn else 'black'])
    return dict(id=entry.pk,index=index,total=len(entry.progress),date=entry.challenge.week_start.isoformat(),
        task=task,practice=practice,completed=index==len(entry.progress),score=entry.score,attempted=attempt_count(entry),
        scoring_open=entry.challenge.week_start==week_start(),independent=sum(p['first_correct'] for p in entry.progress),
        helped=sum(p['attempted'] and not p['first_correct'] for p in entry.progress))


@login_required
@never_cache
def weekly_play(request,entry_id):
    entry=get_object_or_404(WeeklyChallengeEntry.objects.select_related('challenge'),pk=entry_id,user=request.user)
    language=current_language(request)
    practice=request.GET.get('practice')=='1' and (attempt_count(entry)==len(entry.progress) or entry.challenge.week_start!=week_start())
    return render(request,'games/weekly_play.html',dict(entry=entry,dt=board_texts(language),weekly=TEXTS[language],
        session_data=state_for(entry,language,practice),practice=practice,end=end_time(entry.challenge),closed=entry.challenge.week_start!=week_start()))


@login_required
@require_POST
@never_cache
@rate_limit(120,60,'weekly-answer')
def weekly_answer(request):
    try:
        data=json.loads(request.body);entry_id=int(data['id']);index=int(data['index']);action=data['action']
    except (ValueError,TypeError,KeyError,AttributeError):return HttpResponseBadRequest()
    language=current_language(request);texts=TEXTS[language]
    with transaction.atomic():
        entry=WeeklyChallengeEntry.objects.select_for_update().select_related('challenge').filter(pk=entry_id,user=request.user).first()
        if not entry:return JsonResponse({'error':'not_found'},status=404)
        practice=data.get('practice') is True
        if practice and attempt_count(entry)<len(entry.progress) and entry.challenge.week_start==week_start():
            return JsonResponse({'state':state_for(entry,language)},status=409)
        if not 0<=index<len(entry.progress):return JsonResponse({'state':state_for(entry,language)},status=409)
        state=state_for(entry,language,practice,index)
        if index!=state['index']:return JsonResponse({'state':state},status=409)
        saved=entry.challenge.tasks[index];p=dict(entry.progress[index]) if practice else entry.progress[index];board=chess.Board(saved['fen']);best=chess.Move.from_uci(saved['solution'])
        scored_first=not practice and state['scoring_open'] and not p['attempted']
        result_fen=result_move=None;resolved=False
        if action in ('hint','reveal'):
            p['helped']=True
            if scored_first:p['attempted']=True
        if action=='hint':
            piece=BOARD_TEXTS[language]['piece_names'][board.piece_at(best.from_square).symbol().lower()]
            feedback=texts['hint_feedback' if scored_first else 'practice_hint'].format(piece=piece)
        elif action in ('try','reveal'):
            if action=='reveal':move=best
            else:
                try:move=chess.Move.from_uci(data.get('move',''))
                except (ValueError,TypeError):return HttpResponseBadRequest()
                if move not in board.legal_moves:return HttpResponseBadRequest()
            after=board.copy();after.push(move);correct=after.is_checkmate()
            if action=='try' and scored_first:
                p['attempted']=True;p['first_correct']=correct
                if correct:entry.score+=10
                feedback=texts['correct' if correct else 'wrong']
            else:feedback=texts['shown' if scored_first else 'practice_shown'] if action=='reveal' else texts['practice_correct' if correct else 'practice_wrong']
            if correct:
                p['resolved']=True;resolved=True;result_fen=after.fen();result_move=move.uci()
                feedback+=' '+explanation(board,move,language)
        else:return HttpResponseBadRequest()
        if not practice and state['scoring_open'] and all(p['attempted'] for p in entry.progress) and not entry.completed_at:entry.completed_at=timezone.now()
        if not practice:entry.save(update_fields=['progress','score','completed_at'])
        return JsonResponse(dict(state=state_for(entry,language,practice,index+1 if resolved else index),feedback=feedback,resolved=resolved,result_fen=result_fen,result_move=result_move))
