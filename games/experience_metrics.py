"""First-party, server-verified milestones. No IP, message or browser fingerprint."""
from django.db.models import Count, Exists, OuterRef
from .models import ChessGame, GameExperienceEvent
from django.utils import timezone

def today():
    return timezone.localdate()


def record_game(game_id, kind):
    game = ChessGame.objects.filter(pk=game_id).select_related('white_user','black_user').first()
    if not game or not game.moves.exists() or (kind == "finished" and game.status != "finished"):
        return
    for user in (game.white_user, game.black_user):
        if not user or not user.is_active or user.is_staff:
            continue
        # Old finished games are never backfilled when viewed or saved again.
        if kind == 'finished' and not GameExperienceEvent.objects.filter(user=user,game=game,kind='started').exists():
            continue
        GameExperienceEvent.objects.get_or_create(user=user,game=game,kind=kind,defaults={'date':today()})


def record_review(review):
    if review.game_id and review.game.status == 'finished' and review.user_id in (review.game.white_user_id,review.game.black_user_id) and not review.user.is_staff:
        GameExperienceEvent.objects.get_or_create(user=review.user,game=review.game,kind='reviewed',defaults={'date':today()})


def retention_summary(start, end):
    events = GameExperienceEvent.objects.filter(date__gte=start,date__lte=end,user__is_active=True,user__is_staff=False)
    totals = {row['kind']:row for row in events.values('kind').annotate(players=Count('user_id',distinct=True),games=Count('game_id',distinct=True))}
    prior = GameExperienceEvent.objects.filter(user_id=OuterRef('user_id'),kind='finished',created_at__lt=OuterRef('created_at')).exclude(game_id=OuterRef('game_id'))
    again = events.filter(kind='started').annotate(previous_finish=Exists(prior)).filter(previous_finish=True).values('user_id').distinct().count()
    first = GameExperienceEvent.objects.order_by('created_at').values_list('date',flat=True).first()
    return dict(started=totals.get('started',{}).get('players',0),finished=totals.get('finished',{}).get('players',0),
        reviewed=totals.get('reviewed',{}).get('players',0),again=again,first_day=first,
        started_games=totals.get('started',{}).get('games',0),finished_games=totals.get('finished',{}).get('games',0))
