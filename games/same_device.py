from django.shortcuts import render
from django.views.decorators.http import require_GET
from .i18n import current_language

TEXTS={
 'pt':dict(help_title='Como jogar',title='No mesmo dispositivo',intro='2 jogadores · sem conta e sem Elo',again='Nova partida',confirm='Começar outra partida? A atual será substituída.',rotate='Virar a cada turno',help='Cada pessoa joga na sua vez. A partida fica nesta aba, separada das partidas online e com Gchess Bot.',moves='Lances',review='Analisar partida'),
 'es':dict(help_title='Cómo jugar',title='En el mismo dispositivo',intro='2 jugadores · sin cuenta y sin Elo',again='Nueva partida',confirm='¿Empezar otra partida? Se reemplazará la actual.',rotate='Girar en cada turno',help='Cada persona juega en su turno. La partida queda en esta pestaña, separada de las partidas online y con Gchess Bot.',moves='Jugadas',review='Analizar partida'),
 'en':dict(help_title='How to play',title='On the same device',intro='2 players · no account or Elo',again='New game',confirm='Start another game? This will replace the current one.',rotate='Flip after each turn',help='Each person plays on their turn. This game stays in this tab, separate from online and Games with Gchess Bot.',moves='Moves',review='Analyze game'),
}

@require_GET
def play(request):
    return render(request,'games/same_device.html',{'local':TEXTS[current_language(request)],'same_device':True})
