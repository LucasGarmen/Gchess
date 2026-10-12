from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChessGame
from .rewards import reward_game

@receiver(post_save, sender=ChessGame, dispatch_uid='gchess_finished_game_xp')
def finished_game_xp(sender, instance, raw=False, **kwargs):
    if not raw and instance.status == 'finished':
        transaction.on_commit(lambda game_id=instance.pk: reward_game(game_id))
