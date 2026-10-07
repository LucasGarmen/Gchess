import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChessGame, TournamentMatch

logger=logging.getLogger(__name__)

@receiver(post_save,sender=ChessGame,dispatch_uid='gchess_tournament_result')
def game_finished(sender, instance, update_fields=None, **kwargs):
    if instance.status!='finished' or (update_fields and not {'status','result'}.intersection(update_fields)): return
    tournament_id=TournamentMatch.objects.filter(game_id=instance.pk).values_list('tournament_id',flat=True).first()
    if not tournament_id:return
    def advance():
        from .tournaments import advance_tournament
        try:advance_tournament(tournament_id)
        except Exception:logger.exception('Tournament progression could not be refreshed; the tournament page will retry.')
    transaction.on_commit(advance)
