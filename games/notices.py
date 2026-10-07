"""Private action reminders. Reading never creates training or changes games."""
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import ChessGame, Move, Friendship, DailyTraining, WeeklyChallengeEntry, DismissedNotice, GameInvitation
from .i18n import current_language

TEXTS = {
 'es': dict(actions='Partidas y amigos', tournaments='Torneos', training='Para seguir aprendiendo', open='Abrir', dismiss='Descartar aviso', turn='Te toca jugar contra {name}.', friend='{name} quiere ser tu amigo.', daily='Tu entrenamiento de hoy quedó pendiente. Podés retomarlo.', weekly='El desafío semanal está disponible. Tenés hasta el domingo para participar.', resume='Te quedan posiciones del desafío semanal por resolver.', error='No se pudo completar la acción. Intentá de nuevo.', note='Descartar un aviso lo oculta; la partida o invitación sigue disponible.'),
 'pt': dict(actions='Partidas e amigos', tournaments='Torneios', training='Para continuar aprendendo', open='Abrir', dismiss='Dispensar aviso', turn='Sua vez de jogar contra {name}.', friend='{name} quer ser seu amigo.', daily='Seu treino de hoje ficou pendente. Você pode continuar.', weekly='O desafio semanal está disponível. Você tem até domingo para participar.', resume='Ainda há posições do desafio semanal para resolver.', error='Não foi possível concluir a ação. Tente novamente.', note='Dispensar um aviso o oculta; a partida ou convite continua disponível.'),
 'en': dict(actions='Games and friends', tournaments='Tournaments', training='Keep learning', open='Open', dismiss='Dismiss notice', turn='Your turn against {name}.', friend='{name} wants to be your friend.', daily='Your daily training is unfinished. You can resume it.', weekly='The weekly challenge is available. You have until Sunday to participate.', resume='You still have weekly challenge positions to solve.', error='Could not complete the action. Please try again.', note='Dismissing a notice hides it; the game or invitation remains available.'),
}

def items(user, language, include_dismissed=False):
    from .weekly import week_start
    words=TEXTS.get(language,TEXTS['pt'])
    actions=[]; training=[]
    def add(target,key,label,url):
        target.append(dict(key=key,label=label,url=url,open_label=words['open'],dismiss_label=words['dismiss'],dismiss_url=reverse('notice_dismiss',args=[key])))
    last=Move.objects.filter(game_id=OuterRef('pk')).order_by('-move_number','-id')
    games=ChessGame.objects.filter(Q(white_user=user)|Q(black_user=user),status='draft').annotate(last_color=Subquery(last.values('piece_color')[:1]),last_id=Subquery(last.values('pk')[:1])).order_by('-created_at')[:32]
    for game in games:
        white=game.white_user_id==user.pk
        turn='black' if game.last_color=='white' else 'white'
        if turn==('white' if white else 'black'):
            add(actions,f'game:{game.pk}:{game.last_id or 0}',words['turn'].format(name=game.black_player if white else game.white_player),reverse('game_detail',args=[game.pk]))
    requests=Friendship.objects.filter(Q(low_user=user)|Q(high_user=user),status='pending').exclude(requester=user).select_related('requester').order_by('-created_at')[:16]
    for friendship in requests:
        add(actions,f'friend:{friendship.pk}',words['friend'].format(name=friendship.requester.username),reverse('friends'))
    today=timezone.localdate()
    plan=DailyTraining.objects.filter(user=user,date=today,completed_at__isnull=True).first()
    if plan:
        add(training,f'daily:{today.isoformat()}',words['daily'],reverse('daily_training'))
    week=week_start()
    entry=WeeklyChallengeEntry.objects.filter(user=user,challenge__week_start=week).first()
    if not entry or not entry.completed_at:
        add(training,f'weekly:{week.isoformat()}',words['resume'] if entry else words['weekly'],reverse('weekly_challenge'))
    if not include_dismissed:
        keys=[n['key'] for n in actions+training]
        hidden=set(DismissedNotice.objects.filter(user=user,key__in=keys).values_list('key',flat=True))
        actions=[n for n in actions if n['key'] not in hidden]
        training=[n for n in training if n['key'] not in hidden]
    return dict(action_notices=actions,training_notices=training,notice_texts=words)

@login_required
@require_POST
def dismiss(request,key):
    if len(key)>100:
        return JsonResponse({'error':'Unknown notice'},status=404)
    data=items(request.user,current_language(request),include_dismissed=True)
    valid={n['key'] for n in data['action_notices']+data['training_notices']}
    if key.startswith('invite:') and key[7:].isdigit():
        eligible=GameInvitation.objects.filter(pk=int(key[7:]),status='pending').filter(Q(opponent=request.user)|Q(opponent_mode='random',opponent__isnull=True)).exclude(creator=request.user).exists()
        if eligible: valid.add(key)
    # Repeating a previously successful dismissal is harmless, even after completion.
    if key not in valid and not DismissedNotice.objects.filter(user=request.user,key=key).exists():
        return JsonResponse({'error':'Unknown notice'},status=404)
    DismissedNotice.objects.get_or_create(user=request.user,key=key)
    return JsonResponse({'ok':True})
