"""Idempotent XP, serialized on the user's existing puzzle-stat row."""
import hashlib
import io
from datetime import timedelta
from zoneinfo import ZoneInfo
import chess.pgn
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from accounts.models import UserPuzzleStats, XP_PER_LEVEL, unlock_achievements_for_stats
from .models import LearningReward


def today():
    return timezone.localdate(timezone.now(), ZoneInfo('America/Fortaleza'))


@transaction.atomic
def grant(user, key, kind, xp, *, cap=None, peer='', add_to_stats=True):
    if not user or not user.is_authenticated:
        return 0
    stats, _ = UserPuzzleStats.objects.select_for_update().get_or_create(user=user)
    if LearningReward.objects.filter(user=user, key=key).exists():
        return 0
    rows = LearningReward.objects.filter(user=user, date=today(), kind=kind)
    amount = max(0, int(xp))
    if cap is not None:
        amount = min(amount, max(0, cap - (rows.aggregate(total=Sum('xp'))['total'] or 0)))
    if peer and rows.filter(peer=peer, xp__gt=0).exists():
        amount = 0
    LearningReward.objects.create(user=user, key=key, kind=kind, xp=amount, date=today(), peer=peer)
    if amount and add_to_stats:
        stats.xp_total += amount
        stats.nivel = stats.xp_total // XP_PER_LEVEL + 1
        stats.xp_del_nivel_actual = stats.xp_total % XP_PER_LEVEL
        stats.save(update_fields=['xp_total', 'nivel', 'xp_del_nivel_actual', 'updated_at'])
        unlock_achievements_for_stats(stats)
    return amount


def reward_session(plan):
    if plan.completed_at and any(p.get('correct') for p in plan.progress):
        return grant(plan.user, 'daily:'+plan.date.isoformat(), 'daily', 20, cap=20)
    return 0


def reward_weekly(entry):
    if entry.completed_at and any(p.get('first_correct') for p in entry.progress):
        return grant(entry.user, 'weekly:'+str(entry.challenge_id), 'weekly', 25, cap=25)
    return 0


def review_reward_key(review):
    try:
        parsed = chess.pgn.read_game(io.StringIO(review.pgn))
        if parsed is None or parsed.errors:
            return None
        moves = list(parsed.mainline_moves())
        if len(moves) < 4:
            return None
        canonical = parsed.board().fen() + ':' + ' '.join(m.uci() for m in moves)
    except (ValueError, TypeError):
        return None
    return 'review:' + hashlib.sha256(canonical.encode()).hexdigest()


def reward_review(review):
    key = review_reward_key(review)
    return grant(review.user, key, 'review', 10, cap=20) if key else 0


def reward_game(game_id):
    from .models import ChessGame
    game = ChessGame.objects.filter(pk=game_id, status='finished', result__in=['white','black','draw']).select_related('white_user','black_user').first()
    if not game or not game.white_user_id or not game.black_user_id or game.white_user_id == game.black_user_id or game.moves.count() < 12:
        return
    for user, peer in ((game.white_user, game.black_user_id), (game.black_user, game.white_user_id)):
        grant(user, 'game:'+str(game.pk), 'game', 5, cap=15, peer=str(peer))


def summary(user):
    stats = UserPuzzleStats.objects.filter(user=user).first()
    total = stats.xp_total if stats else 0
    dates = set(LearningReward.objects.filter(user=user, xp__gt=0).values_list('date', flat=True).distinct())
    cursor = today() if today() in dates else today()-timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return dict(total=total, level=total//XP_PER_LEVEL+1, progress=total%XP_PER_LEVEL, remaining=XP_PER_LEVEL-total%XP_PER_LEVEL,
        streak=streak, days=[dict(active=today()-timedelta(days=i) in dates) for i in range(6,-1,-1)],
        daily_done=LearningReward.objects.filter(user=user,key='daily:'+today().isoformat(),xp__gt=0).exists())
