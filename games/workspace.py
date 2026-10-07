"""Private, read-only overview of a player's simultaneous games."""
import uuid
from django.db.models import Q, OuterRef, Subquery
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from .models import ChessGame, Move
from .i18n import current_language

TEXTS = {
 'es': ['Mis partidas', 'Nueva con el coach', 'Nueva contra persona', 'Tu turno', 'Turno del rival', 'Pausada', 'Terminada', 'Ver todas', 'Los relojes contra personas siguen corriendo. El coach espera hasta que vuelvas.', 'No se pudieron actualizar las partidas. Podés verlas en “Ver todas”.', 'Cerrar selector', 'Partidas contra personas', 'Partidas con el coach en este navegador', 'Todavía no hay partidas contra personas abiertas.'],
 'pt': ['Minhas partidas', 'Nova com o coach', 'Nova contra pessoa', 'Sua vez', 'Vez do adversário', 'Pausada', 'Finalizada', 'Ver todas', 'Os relógios contra pessoas continuam correndo. O coach espera até você voltar.', 'Não foi possível atualizar as partidas. Consulte “Ver todas”.', 'Fechar seletor', 'Partidas contra pessoas', 'Partidas com o coach neste navegador', 'Nenhuma partida contra pessoas aberta.'],
 'en': ['My games', 'New game with the coach', 'New human game', 'Your turn', "Opponent’s turn", 'Paused', 'Finished', 'View all', 'Human game clocks keep running. The coach waits until you return.', 'Could not refresh games. Use “View all” to check them.', 'Close selector', 'Human games', 'Coach games in this browser', 'No human games open yet.'],
}

def namespace(request):
    if request.user.is_authenticated:
        return 'user:' + str(request.user.pk)
    if not request.session.get('guest_id'):
        request.session['guest_id'] = uuid.uuid4().hex
    return 'guest:' + request.session['guest_id']

def workspace_context(request):
    words = TEXTS.get(current_language(request), TEXTS['pt'])
    return {'workspace_config': {'actor': namespace(request), 'endpoint': reverse('active_games'), 'home': reverse('home'), 'newHuman': reverse('game_create'), 'allGames': reverse('games_list'), 'words': words}}

@require_GET
@never_cache
def active_games(request):
    actor = namespace(request)
    if request.user.is_authenticated:
        participants = Q(white_user=request.user) | Q(black_user=request.user)
    else:
        guest = request.session['guest_id']
        participants = Q(white_guest_id=guest) | Q(black_guest_id=guest)
    last_move = Move.objects.filter(game_id=OuterRef('pk')).order_by('-move_number', '-id')
    games = ChessGame.objects.filter(participants, status='draft').annotate(last_color=Subquery(last_move.values('piece_color')[:1])).order_by('-created_at')
    entries = []
    for game in games:
        white = game.white_user_id == request.user.pk if request.user.is_authenticated else game.white_guest_id == request.session['guest_id']
        color = 'white' if white else 'black'
        turn = 'black' if game.last_color == 'white' else 'white'
        entries.append({'id': game.pk, 'url': reverse('game_detail', args=[game.pk]), 'opponent': game.black_player if white else game.white_player, 'yourTurn': turn == color, 'rated': game.is_rated})
    return JsonResponse({'actor': actor, 'games': entries})
