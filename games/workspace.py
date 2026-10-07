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

EXIT_TEXTS = {
 'es': {
  'storage': 'Las partidas con el coach son temporales y quedan solo en esta pestaña. No se guardan en tu cuenta; al cerrar la pestaña podés perderlas.',
  'logout': 'Tenés partidas con el coach empezadas. Al cerrar sesión dejarán de aparecer en Mis partidas. Son temporales: no se guardan en tu cuenta y al cerrar esta pestaña podés perderlas. ¿Querés cerrar sesión?',
 },
 'pt': {
  'storage': 'As partidas com o coach são temporárias e ficam apenas nesta aba. Não são salvas na sua conta; ao fechar a aba você pode perdê-las.',
  'logout': 'Você tem partidas com o coach em andamento. Ao sair da conta, elas deixarão de aparecer em Minhas partidas. São temporárias: não são salvas na sua conta e ao fechar esta aba você pode perdê-las. Quer sair da conta?',
 },
 'en': {
  'storage': 'Coach games are temporary and stay only in this tab. They are not saved to your account; closing the tab can lose them.',
  'logout': 'You have coach games in progress. Logging out will hide them from My games. They are temporary: they are not saved to your account and closing this tab can lose them. Log out?',
 },
}

def namespace(request):
    if request.user.is_authenticated:
        return 'user:' + str(request.user.pk)
    if not request.session.get('guest_id'):
        request.session['guest_id'] = uuid.uuid4().hex
    return 'guest:' + request.session['guest_id']

def workspace_context(request):
    language = current_language(request)
    words = TEXTS.get(language, TEXTS['pt'])
    exit_texts = EXIT_TEXTS.get(language, EXIT_TEXTS['pt'])
    return {'workspace_config': {'actor': namespace(request), 'endpoint': reverse('active_games'), 'home': reverse('home'), 'newHuman': reverse('game_create'), 'allGames': reverse('games_list'), 'words': words, 'blindfoldLabel':{'es':'A ciegas','pt':'Às cegas','en':'Blindfold'}[language], 'storageNotice': exit_texts['storage'], 'logoutWarning': exit_texts['logout'], 'stayLabel': {'es':'Seguir conectado','pt':'Continuar conectado','en':'Stay signed in'}[language], 'leaveLabel': {'es':'Cerrar sesión','pt':'Sair da conta','en':'Log out'}[language]}}

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
        entries.append({'id': game.pk, 'url': reverse('game_detail', args=[game.pk]), 'opponent': game.black_player if white else game.white_player, 'title': game.title, 'yourTurn': turn == color, 'rated': game.is_rated, 'blindfoldOnly':game.blindfold_only})
    return JsonResponse({'actor': actor, 'games': entries})
