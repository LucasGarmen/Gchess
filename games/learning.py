"""Personal reviews reuse the existing engine analysis; no engine work during play."""
import hashlib
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from .i18n import current_language
from .learning_texts import LEARNING_TEXTS
from .models import ChessGame, GameInvitation, GameReview


def review_key(pgn, game=None):
    return hashlib.sha256(f'v1:{game.pk if game else "import"}:{pgn}'.encode()).hexdigest()


def cached_review(user, pgn, language, color, game=None):
    if not user.is_authenticated: return None
    return GameReview.objects.filter(user=user, fingerprint=review_key(pgn, game), language=language, player_color=color).first()


def save_review(user, pgn, language, color, moves, analysis, opening, game=None):
    if not user.is_authenticated or not analysis or len(moves) != len(analysis): return None
    if game and user.pk not in (game.white_user_id, game.black_user_id): return None
    review, _ = GameReview.objects.get_or_create(user=user, fingerprint=review_key(pgn, game), language=language,
        player_color=color, defaults=dict(game=game, pgn=pgn, payload=dict(moves=moves, analysis=analysis, opening=opening)))
    return review


def build_review_summary(moves, analysis, color, language):
    texts = LEARNING_TEXTS[language]
    own = []
    for move, item in zip(moves, analysis):
        if move.get('piece_color') == color:
            own.append(dict(item, fullmove=(item['move_number']+1)//2, black=color == 'black'))
    known = [row for row in own if isinstance(row.get('loss'), (int,float)) and row['loss'] >= 0]
    errors = [row for row in known if row.get('classification') in ('inaccuracy','mistake','blunder')]
    critical = sorted(errors, key=lambda row: row['loss'], reverse=True)[:3]
    phases = Counter(row.get('engine_context', {}).get('game_phase','middlegame') for row in errors)
    focus = phases.most_common(1)[0][0] if phases else 'general'
    if focus not in ('opening','middlegame','endgame'): focus='general'
    return dict(total=len(own), evaluated=len(known), errors=len(errors), serious=sum(row.get('classification') in ('mistake','blunder') for row in known),
        average_loss=round(sum(row['loss'] for row in known)/len(known)) if known else None,
        moments=critical, phase_errors=dict(phases), focus=focus, focus_name=texts[focus], recommendation=texts['recommend_'+focus],
        good=sum(row.get('classification') in ('best','book','good','normal') for row in known))


def summary_for(review, language):
    payload=review.payload
    return build_review_summary(payload.get('moves',[]), payload.get('analysis',[]), review.player_color, language)


def game_result_text(game, color, texts):
    if game.result == 'draw': return texts['draw']
    if game.result in ('white','black'):
        if color: return texts['won' if color == game.result else 'lost']
        return texts[game.result+'_won']
    return texts['finished']


def game_review(request, game_id):
    from .views import get_game_for_user, player_color_for_game
    game=get_game_for_user(game_id,request.user,request.session.get('guest_id'))
    if game.status != 'finished': return redirect('game_detail',game_id=game.pk)
    lang=current_language(request);texts=LEARNING_TEXTS[lang]
    color=player_color_for_game(game,request.user,request.session.get('guest_id'))
    review=GameReview.objects.filter(user=request.user,game=game,player_color=color).order_by('-created_at').first() if request.user.is_authenticated and color else None
    return render(request,'games/game_review.html',dict(source_game=game,review=review,summary=summary_for(review,lang) if review else None,
        learning=texts,result_text=game_result_text(game,color,texts),can_rematch=bool(color),
        analyzer_url=reverse('game_analyzer')+f'?game_id={game.pk}'))


@login_required
def review_detail(request, review_id):
    review=get_object_or_404(GameReview,user=request.user,pk=review_id)
    lang=current_language(request);texts=LEARNING_TEXTS[lang]
    return render(request,'games/game_review.html',dict(review=review,summary=summary_for(review,lang),source_game=review.game,
        learning=texts,can_rematch=bool(review.game),analyzer_url=reverse('game_analyzer')+f'?review_id={review.pk}',result_text=texts['your_review']))


@login_required
@never_cache
def learning_history(request):
    lang=current_language(request);texts=LEARNING_TEXTS[lang]
    reviews=[];seen=set()
    for review in GameReview.objects.filter(user=request.user).select_related('game').order_by('-created_at')[:200]:
        key=(review.fingerprint,review.player_color)
        if key in seen: continue
        seen.add(key);summary=summary_for(review,lang)
        reviews.append(dict(review=review,summary=summary))
    valid=[row for row in reviews if row['summary']['average_loss'] is not None]
    recent=valid[:5];previous=valid[5:10]
    recent_average=round(sum(row['summary']['average_loss'] for row in recent)/len(recent)) if recent else None
    previous_average=round(sum(row['summary']['average_loss'] for row in previous)/len(previous)) if previous else None
    trend=None
    if len(recent)>=3 and len(previous)>=3:
        delta=recent_average-previous_average
        trend=texts['trend_better' if delta < -10 else 'trend_worse' if delta > 10 else 'trend_stable']
    phases=Counter()
    for row in recent:
        summary=row['summary']
        phases.update({phase: count for phase, count in summary['phase_errors'].items() if phase in ('opening','middlegame','endgame')})
    focus=phases.most_common(1)[0][0] if phases else 'general'
    from .learning_progress import learning_progress
    progress=learning_progress(request.user,lang,reviews)
    return render(request,'games/learning.html',dict(learning=texts,progress=progress,reviews=reviews[:30],review_count=GameReview.objects.filter(user=request.user).values('fingerprint','player_color').distinct().count(),
        recent_average=recent_average,previous_average=previous_average,trend=trend,
        focus_name=texts[focus],recommendation=texts['recommend_'+focus]))


@require_POST
def rematch(request, game_id):
    from .views import get_game_for_user, player_color_for_game, rate_limit
    return rate_limit(10,60,'game-rematch')(_rematch)(request,game_id)


def _rematch(request,game_id):
    from .views import get_game_for_user, player_color_for_game
    game=get_game_for_user(game_id,request.user,request.session.get('guest_id'))
    color=player_color_for_game(game,request.user,request.session.get('guest_id'))
    if not color or game.status != 'finished': return HttpResponseBadRequest()
    with transaction.atomic():
        game=ChessGame.objects.select_for_update().get(pk=game.pk)
        if game.status != 'finished': return HttpResponseBadRequest()
        other=game.black_user if color == 'white' else game.white_user
        existing=GameInvitation.objects.filter(rematch_of=game,status='pending').first()
        if existing:
            creator_is_me=(request.user.is_authenticated and existing.creator_id==request.user.pk) or (not request.user.is_authenticated and existing.creator_guest_id==request.session.get('guest_id'))
            if creator_is_me: return redirect('game_invitation_wait',invitation_id=existing.pk)
            return render(request,'games/rematch_pending.html',dict(invitation=existing,learning=LEARNING_TEXTS[current_language(request)]))
        invitation=GameInvitation.objects.create(rematch_of=game,creator=request.user if request.user.is_authenticated else None,
            creator_guest_id='' if request.user.is_authenticated else request.session.get('guest_id',''),
            creator_guest_name='' if request.user.is_authenticated else (game.white_player if color=='white' else game.black_player),
            opponent=other,opponent_mode='direct' if request.user.is_authenticated and other else 'link',
            creator_color='black' if color=='white' else 'white',time_control_minutes=game.time_control_minutes,
            is_rated=bool(game.is_rated and request.user.is_authenticated and other))
    return redirect('game_invitation_wait',invitation_id=invitation.pk)


@login_required
@require_POST
def review_goal(request,review_id):
    from django.utils import timezone
    review=get_object_or_404(GameReview,user=request.user,pk=review_id)
    GameReview.objects.filter(pk=review.pk,goal_completed_at__isnull=True).update(goal_completed_at=timezone.now())
    return redirect('review_detail',review_id=review.pk)


@require_POST
def rematch_accept(request,invitation_id):
    import json
    from .views import get_game_for_user, player_color_for_game, accept_invitation, accept_invitation_link
    invitation=get_object_or_404(GameInvitation,pk=invitation_id,rematch_of__isnull=False)
    source = get_game_for_user(invitation.rematch_of_id,request.user,request.session.get('guest_id'))
    if not player_color_for_game(source,request.user,request.session.get('guest_id')):
        return HttpResponseBadRequest()
    if invitation.opponent_mode == 'link': return accept_invitation_link(request,invitation.token)
    response=accept_invitation(request,invitation.pk)
    if response.status_code == 200:
        data=json.loads(response.content)
        if data.get('game_url'): return redirect(data['game_url'])
    return response
