"""Short daily plans from saved, engine-verified reviews; no live AI calls."""
import json
import random
import math
from datetime import timedelta
import chess
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .models import DailyTraining, GameReview
from .daily_training_texts import TEXTS
from .i18n import current_language
from .views import rate_limit, friendly_move_name, friendly_opening_fact


def candidates(user,review_id=None):
    found={}
    reviews=GameReview.objects.filter(user=user)
    if review_id is not None:reviews=reviews.filter(pk=review_id)
    for review in reviews.order_by('-created_at')[:60]:
        payload=review.payload
        if not isinstance(payload,dict):continue
        moves,analysis=payload.get('moves',[]),payload.get('analysis',[])
        if not isinstance(moves,list) or not isinstance(analysis,list):continue
        for move,item in zip(moves,analysis):
            if not isinstance(move,dict) or not isinstance(item,dict):continue
            loss=item.get('loss')
            if move.get('piece_color')!=review.player_color or item.get('classification') not in ('inaccuracy','mistake','blunder') or not isinstance(loss,(int,float)) or not math.isfinite(loss) or loss<=0:continue
            context=item.get('engine_context') or {}
            if not isinstance(context,dict):continue
            try:
                board=chess.Board(context['fen_before']);best=chess.Move.from_uci(context['best_move_uci']);played=chess.Move.from_uci(context['played_move_uci'])
                if not board.is_valid() or board.is_game_over() or best not in board.legal_moves or played not in board.legal_moves or best==played:continue
                if ('white' if board.turn else 'black')!=review.player_color:continue
            except (ValueError,TypeError,KeyError):continue
            key=board.fen()
            if key not in found:
                found[key]=dict(fen=key,solution=best.uci(),source=review.pk,phase=context.get('game_phase','general'),loss=loss)
    return sorted(found.values(),key=lambda task:-task['loss'])


def build_plan(user,date):
    from .personal_sessions import personal_selection
    tasks=personal_selection(user,date)
    rng=random.Random(f'{user.pk}:{date.isoformat()}')
    from .puzzles import PRACTICE_PUZZLES
    fallback=[]
    for puzzle in PRACTICE_PUZZLES:
        if puzzle.get('mate_in')!=1:continue
        board=chess.Board(puzzle['fen'])
        if not board.is_valid():continue
        for move in list(board.legal_moves):
            after=board.copy();after.push(move)
            if after.is_checkmate():
                fallback.append(dict(fen=board.fen(),solution=move.uci(),source=None,phase='general'));break
    rng.shuffle(fallback)
    existing={task['fen'] for task in tasks}
    for task in fallback:
        if task['fen'] not in existing:
            tasks.append(task);existing.add(task['fen'])
    return tasks[:3]


def session_data(plan,language):
    texts=TEXTS[language]
    index=next((i for i,p in enumerate(plan.progress) if not p['resolved']),len(plan.tasks))
    task=None
    if index<len(plan.tasks):
        saved=plan.tasks[index];board=chess.Board(saved['fen'])
        task=dict(fen=saved['fen'],legal_moves=[move.uci() for move in board.legal_moves],
            personal=bool(saved['source']),revisit=bool(saved.get('revisit')),phase=texts.get(saved['phase'],texts['general']),
            source_url=reverse('review_detail',args=[saved['source']]) if saved['source'] and GameReview.objects.filter(pk=saved['source'],user=plan.user).exists() else None,
            turn=texts['white' if board.turn else 'black'])
    from .personal_session_texts import TEXTS as SESSION_TEXTS
    return_texts=SESSION_TEXTS[language]
    if task and saved.get('source'):
        from .personal_sessions import theme_for
        theme=theme_for(saved)
        task['practice_label']=return_texts['repeat' if saved.get('revisit') else 'new_position']
        task['focus']=return_texts[theme]
        task['tip']=return_texts['tip_'+theme]
    recent_count=DailyTraining.objects.filter(user=plan.user,date__gte=timezone.localdate()-timedelta(days=6),completed_at__isnull=False).count()
    return dict(recent_count=recent_count,id=plan.pk,date=plan.date.isoformat(),index=index,total=len(plan.tasks),completed=bool(plan.completed_at),task=task,
        independent=sum(p['resolved'] and p['correct'] and not p['helped'] and p['attempts']==1 for p in plan.progress),
        helped=sum(p['resolved'] and (p['helped'] or not p['correct'] or p['attempts']>1) for p in plan.progress))


@login_required
@never_cache
def daily_training(request):
    plan=DailyTraining.objects.filter(user=request.user,date=timezone.localdate()).first()
    from .personal_sessions import next_session
    return render(request,'games/daily_training.html',dict(next_session=next_session(request.user,current_language(request),plan),dt=TEXTS[current_language(request)],plan=plan,
        session_data=session_data(plan,current_language(request)) if plan else None,has_personal=bool(candidates(request.user)) if not plan else False,
        recent_count=DailyTraining.objects.filter(user=request.user,date__gte=timezone.localdate()-timedelta(days=6),completed_at__isnull=False).count()))


@login_required
@require_POST
@rate_limit(15,60,'daily-training-start')
def daily_training_start(request):
    with transaction.atomic():
        User.objects.select_for_update().get(pk=request.user.pk)
        plan=DailyTraining.objects.filter(user=request.user,date=timezone.localdate()).first()
        if not plan:
            tasks=build_plan(request.user,timezone.localdate())
            if not tasks:return HttpResponseBadRequest()
            DailyTraining.objects.create(user=request.user,date=timezone.localdate(),tasks=tasks,
                progress=[dict(attempts=0,helped=False,correct=False,resolved=False) for task in tasks])
    return redirect('daily_training')


def explanation(board,move,language):
    texts=TEXTS[language];after=board.copy();after.push(move)
    fact='mate_fact' if after.is_checkmate() else 'castle_fact' if board.is_castling(move) else 'capture_fact' if board.is_capture(move) else 'check_fact' if after.is_check() else 'move_fact'
    detail=friendly_opening_fact(board,move,language) if fact=='move_fact' else ''
    return texts['solution'].format(move=friendly_move_name(board,move,language))+' '+(detail or texts[fact])


@login_required
@require_POST
@never_cache
@rate_limit(120,60,'daily-training-answer')
def daily_training_answer(request):
    try:
        data=json.loads(request.body);plan_id=int(data['id']);index=int(data['index']);action=data['action']
    except (ValueError,TypeError,KeyError):return HttpResponseBadRequest()
    language=current_language(request);texts=TEXTS[language]
    with transaction.atomic():
        plan=DailyTraining.objects.select_for_update().filter(pk=plan_id,user=request.user).first()
        if not plan:return JsonResponse({'error':'not_found'},status=404)
        current=next((i for i,p in enumerate(plan.progress) if not p['resolved']),len(plan.tasks))
        if index!=current or current>=len(plan.tasks):return JsonResponse({'state':session_data(plan,language)},status=409)
        task=plan.tasks[index];progress=plan.progress[index];board=chess.Board(task['fen']);best=chess.Move.from_uci(task['solution'])
        feedback='';result_fen=None;result_move=None;resolved=False
        if action=='hint':
            progress['helped']=True
            name=chess.piece_name(board.piece_at(best.from_square).piece_type)
            name={'es':{'pawn':'peón','knight':'caballo','bishop':'alfil','rook':'torre','queen':'dama','king':'rey'},'pt':{'pawn':'peão','knight':'cavalo','bishop':'bispo','rook':'torre','queen':'dama','king':'rei'}}.get(language,{}).get(name,name)
            feedback=texts['hint_text'].format(piece=name)
        elif action in ('try','reveal'):
            if action=='reveal':move=best;progress['helped']=True
            else:
                try:move=chess.Move.from_uci(data.get('move',''))
                except (ValueError,TypeError):return HttpResponseBadRequest()
                if move not in board.legal_moves:return HttpResponseBadRequest()
                progress['attempts']+=1
            after=board.copy();after.push(move)
            # Accept every checkmate, rather than rejecting another equally final move.
            correct=move==best or after.is_checkmate()
            if correct:
                progress['correct']=action=='try';progress['resolved']=True;progress['resolved_on']=timezone.localdate().isoformat();resolved=True
                feedback=texts['correct' if action=='try' else 'shown']+' '+explanation(board,move,language)
                result_fen=after.fen();result_move=move.uci()
            else:feedback=texts['legal'] if task['source'] else texts['retry']
        else:return HttpResponseBadRequest()
        if all(p['resolved'] for p in plan.progress):plan.completed_at=timezone.now()
        plan.save(update_fields=['progress','completed_at'])
        return JsonResponse(dict(state=session_data(plan,language),feedback=feedback,resolved=resolved,result_fen=result_fen,result_move=result_move))
