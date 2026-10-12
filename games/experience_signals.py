from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import ChessGame, Move, GameReview
from .experience_metrics import record_game, record_review

@receiver(post_save, sender=Move, dispatch_uid='gchess_experience_first_move')
def first_move(sender, instance, created=False, raw=False, **kwargs):
    if created and not raw and instance.move_number == 1:
        transaction.on_commit(lambda game_id=instance.game_id: record_game(game_id,'started'))

@receiver(pre_save, sender=ChessGame, dispatch_uid='gchess_experience_prior_status')
def prior_status(sender, instance, raw=False, update_fields=None, **kwargs):
    instance._experience_finishing = False
    if raw or instance.status != 'finished' or not instance.pk or (update_fields and 'status' not in update_fields):
        return
    previous = ChessGame.objects.filter(pk=instance.pk).values_list('status',flat=True).first()
    instance._experience_finishing = previous is not None and previous != 'finished'

@receiver(post_save, sender=ChessGame, dispatch_uid='gchess_experience_finished')
def finished(sender, instance, raw=False, **kwargs):
    if not raw and getattr(instance,'_experience_finishing',False):
        transaction.on_commit(lambda game_id=instance.pk: record_game(game_id,'finished'))

@receiver(post_save, sender=GameReview, dispatch_uid='gchess_experience_reviewed')
def reviewed(sender, instance, created=False, raw=False, **kwargs):
    if created and not raw and instance.game_id:
        transaction.on_commit(lambda review=instance: record_review(review))
