"""Unrated practice of verified alternatives from one owned saved review."""
import json
import chess
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404,render,redirect
from django.http import JsonResponse,HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.utils import timezone
from .models import GameReview
from .daily_training import candidates,explanation
from .daily_training_texts import TEXTS
from .first_steps import TEXTS as FLOW
from .i18n import current_language
from .views import rate_limit

def key(review):return 'review-practice-'+str(review.pk)
def state(review,plan,lang):
    index=next((i for i,p in enumerate(plan['progress']) if not p['resolved']),len(plan['tasks']))
    task=None
    if index<len(plan['tasks']):
        saved=plan['tasks'][index];board=chess.Board(saved['fen'])
        task=dict(fen=saved['fen'],legal_moves=[m.uci() for m in board.legal_moves],personal=False,source_url=None,turn=TEXTS[lang]['white' if board.turn else 'black'])
    return dict(id=review.pk,index=index,total=len(plan['tasks']),date=review.created_at.date().isoformat(),task=task,completed=index==len(plan['tasks']),independent=sum(p['resolved'] and p['correct'] and not p['helped'] and p['attempts']==1 for p in plan['progress']),helped=sum(p['resolved'] and (p['helped'] or not p['correct'] or p['attempts']>1) for p in plan['progress']))

@login_required
@require_POST
@rate_limit(15,60,'review-practice-start')
def start(request,review_id):
    review=get_object_or_404(GameReview,pk=review_id,user=request.user)
    tasks=candidates(request.user,review.pk)[:3]
    if not tasks:return redirect('review_practice',review_id=review.pk)
    session_key=key(review)
    if session_key not in request.session or request.POST.get('restart')=='1':
        stored=[k for k in request.session.keys() if k.startswith('review-practice-')]
        for old in stored[:-4]:del request.session[old]
        request.session[session_key]=dict(tasks=tasks,progress=[dict(attempts=0,helped=False,correct=False,resolved=False) for _ in tasks])
    return redirect('review_practice',review_id=review.pk)

@login_required
@never_cache
def play(request,review_id):
    review=get_object_or_404(GameReview,pk=review_id,user=request.user);lang=current_language(request)
    plan=request.session.get(key(review));texts=dict(TEXTS[lang]);flow=FLOW[lang]
    for target,source in [('finish','practice_finish'),('summary','practice_summary'),('independent','practice_first'),('helped','practice_helped'),('fallback','practice_title')]:texts[target]=flow[source]
    texts['goal_mate']=TEXTS[lang]['goal']
    return render(request,'games/review_practice.html',dict(review=review,dt=texts,session_data=state(review,plan,lang) if plan else None,has_positions=bool(candidates(request.user,review.pk))))

@login_required
@require_POST
@never_cache
@rate_limit(120,60,'review-practice-answer')
def answer(request):
    try:
        data=json.loads(request.body);review_id=int(data['id']);index=int(data['index']);action=data['action']
    except (ValueError,TypeError,KeyError,UnicodeDecodeError):return HttpResponseBadRequest()
    review=get_object_or_404(GameReview,pk=review_id,user=request.user)
    plan=request.session.get(key(review));lang=current_language(request);texts=TEXTS[lang]
    if not plan:return JsonResponse({'error':'not_started'},status=409)
    current=state(review,plan,lang)
    if index!=current['index'] or current['completed']:return JsonResponse({'state':current},status=409)
    saved=plan['tasks'][index];progress=plan['progress'][index];board=chess.Board(saved['fen']);best=chess.Move.from_uci(saved['solution'])
    result_fen=result_move=None;resolved=False
    if action=='hint':
        progress['helped']=True;piece=texts['piece_names'][board.piece_at(best.from_square).symbol().lower()]
        feedback=texts['hint_text'].format(piece=piece)
    elif action in ('try','reveal'):
        if action=='reveal':move=best;progress['helped']=True
        else:
            try:move=chess.Move.from_uci(data.get('move',''))
            except (ValueError,TypeError):return HttpResponseBadRequest()
            if move not in board.legal_moves:return HttpResponseBadRequest()
            progress['attempts']+=1
        after=board.copy();after.push(move);resolved=move==best or after.is_checkmate()
        if resolved:
            progress['resolved']=True;progress['correct']=action=='try'
            feedback=texts['correct' if action=='try' else 'shown']+' '+explanation(board,move,lang)
            result_fen=after.fen();result_move=move.uci()
        else:feedback=texts['retry']
    else:return HttpResponseBadRequest()
    request.session[key(review)]=plan
    if all(item['resolved'] for item in plan['progress']):
        GameReview.objects.filter(pk=review.pk,user=request.user,goal_completed_at__isnull=True).update(goal_completed_at=timezone.now())
    return JsonResponse(dict(state=state(review,plan,lang),feedback=feedback,resolved=resolved,result_fen=result_fen,result_move=result_move))
