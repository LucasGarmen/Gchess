"""Short, curated opening lines. No engine or AI request is needed."""
import json
import chess
from django.http import JsonResponse
from django.shortcuts import render
from django.http import Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .i18n import current_language

KEYS=('title','intro','learn','practice','white','black','next','hint','restart','back','correct','wrong','done','network','select','line_help','move','plan','choose','progress')
TEXTS={
'es':dict(zip(KEYS,('Aperturas','Entendé los primeros movimientos y después probá recordarlos sin ayuda.','Aprender paso a paso','Practicar de memoria','Blancas','Negras','Siguiente jugada','Mostrar pista','Volver a empezar','Todas las aperturas','¡Bien! El rival respondió.','Esa jugada no pertenece a esta línea. Probá otra o pedí una pista.','Completaste esta línea. Repetila de memoria o probá otra apertura.','No pudimos comprobar la jugada. Intentá de nuevo.','Elegí una pieza y después su destino.','Practicamos una línea de ejemplo. Hay otras respuestas válidas en una partida real.','Jugada','Plan de la apertura','Elegí una apertura','Progreso de esta línea'))),
'pt':dict(zip(KEYS,('Aberturas','Entenda os primeiros movimentos e depois tente lembrá-los sem ajuda.','Aprender passo a passo','Praticar de memória','Brancas','Pretas','Próxima jogada','Mostrar dica','Recomeçar','Todas as aberturas','Muito bem! O adversário respondeu.','Essa jogada não faz parte desta linha. Tente outra ou peça uma dica.','Você completou esta linha. Repita de memória ou tente outra abertura.','Não foi possível verificar a jogada. Tente novamente.','Escolha uma peça e depois o destino.','Praticamos uma linha de exemplo. Há outras respostas válidas em uma partida real.','Jogada','Plano da abertura','Escolha uma abertura','Progresso desta linha'))),
'en':dict(zip(KEYS,('Openings','Understand the first moves, then try recalling them without help.','Learn step by step','Practice from memory','White','Black','Next move','Show hint','Restart','All openings','Good! Your opponent replied.','That move is outside this line. Try another or ask for a hint.','You completed this line. Repeat from memory or try another opening.','Could not check the move. Please try again.','Choose a piece, then its destination.','This is one example line. Other replies can be valid in a real game.','Move','Opening plan','Choose an opening','Progress through this line'))),
}
# Names, plans and move-by-move explanations follow the same language order.
LANGS=('es','pt','en')
CONCEPTS={
'center':('Este peón ocupa el centro y deja salir al alfil.','Este peão ocupa o centro e abre caminho para o bispo.','This pawn claims the center and opens a path for the bishop.'),
'knight':('Sacás un caballo y controlás casillas del centro.','Você desenvolve um cavalo e controla casas centrais.','You develop a knight and control central squares.'),
'bishop':('Desarrollás el alfil antes de enrocar; ya empieza a participar.','Você desenvolve o bispo antes de rocar; ele já participa do jogo.','You develop the bishop before castling, bringing it into play.'),
'castle':('Ponés al rey a salvo y acercás la torre al centro.','Você protege o rei e aproxima a torre do centro.','You bring your king to safety and your rook closer to the center.'),
'support':('Este peón prepara o sostiene el centro; no hace falta mover todas las piezas de golpe.','Este peão prepara ou sustenta o centro; desenvolva as peças aos poucos.','This pawn prepares or supports the center; develop your pieces steadily.'),
'capture':('Este cambio libera tensión en el centro y abre líneas para tus piezas.','Esta troca alivia a tensão no centro e abre linhas para suas peças.','This exchange releases central tension and opens lines for your pieces.'),
}
LINES=(
('italian',('Italiana','Italiana','Italian Game'),'white','e4 e5 Nf3 Nc6 Bc4 Bc5 c3 Nf6 d3 d6 O-O O-O',('Desarrollá rápido, enrocá y prepará d4 cuando tus piezas estén listas.','Desenvolva rápido, faça o roque e prepare d4 quando suas peças estiverem prontas.','Develop quickly, castle, and prepare d4 when your pieces are ready.')),
('ruy-lopez',('Española','Espanhola','Ruy Lopez'),'white','e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7',('Presioná el caballo que defiende e5, sin apresurarte a capturarlo.','Pressione o cavalo que defende e5 sem se apressar em capturá-lo.','Pressure the knight defending e5 without rushing to capture it.')),
('queens-gambit',('Gambito de dama','Gambito da dama',"Queen’s Gambit"),'white','d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O',('Ofrecés el peón de c para disputar el centro y desarrollar tus piezas.','Você oferece o peão de c para disputar o centro e desenvolver suas peças.','Offer the c-pawn to challenge the center and develop your pieces.')),
('sicilian',('Siciliana','Siciliana','Sicilian Defense'),'black','e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 Nc6',('Respondés al centro desde un costado y buscás contrajuego con tus piezas.','Você disputa o centro pelo flanco e busca contrajogo com suas peças.','Challenge the center from the flank and seek active counterplay.')),
('french',('Francesa','Francesa','French Defense'),'black','e4 e6 d4 d5 Nc3 Nf6 e5 Nfd7 f4 c5',('Construís un centro firme y lo atacás con c5; cuidá el alfil de c8.','Você constrói um centro sólido e o ataca com c5; cuide do bispo de c8.','Build a solid center and challenge it with c5; watch your c8 bishop.')),
('caro-kann',('Caro-Kann','Caro-Kann','Caro-Kann Defense'),'black','e4 c6 d4 d5 Nc3 dxe4 Nxe4 Bf5 Ng3 Bg6',('Preparás d5 con c6 y sacás el alfil antes de cerrar su diagonal con e6.','Você prepara d5 com c6 e desenvolve o bispo antes de fechar a diagonal com e6.','Prepare d5 with c6 and develop the bishop before closing its diagonal with e6.')),
)

def lesson(slug,lang):
    row=next((row for row in LINES if row[0]==slug),None)
    if row is None: raise Http404
    slug,names,color,line,plans=row;board=chess.Board();moves=[];li=LANGS.index(lang)
    for san in line.split():
        move=board.parse_san(san)
        concept='castle' if board.is_castling(move) else 'capture' if board.is_capture(move) else 'knight' if board.piece_at(move.from_square).piece_type==chess.KNIGHT else 'bishop' if board.piece_at(move.from_square).piece_type==chess.BISHOP else 'center' if san in ('e4','d4','e5','d5') else 'support'
        explanation=CONCEPTS[concept][li]
        special={
            'a6':('Preguntás al alfil si va a cambiar el caballo o retirarse.','Você pergunta ao bispo se vai trocar o cavalo ou recuar.','You ask the bishop to exchange the knight or retreat.'),
            'Ba4':('Retirás el alfil del ataque del peón y mantenés la presión sobre el caballo.','Você retira o bispo do ataque do peão e mantém a pressão no cavalo.','You retreat the bishop from the pawn attack and keep pressure on the knight.'),
            'Nfd7':('Retirás el caballo atacado por e5 y preparás el contraataque al centro.','Você retira o cavalo atacado por e5 e prepara o contra-ataque central.','You retreat the knight attacked by e5 and prepare to challenge the center.'),
            'Bg6':('El caballo amenaza tu alfil: lo retirás manteniéndolo fuera de la cadena de peones.','O cavalo ameaça seu bispo: você recua mantendo-o fora da cadeia de peões.','The knight attacks your bishop: retreat while keeping it outside the pawn chain.'),
        }
        if san in special:explanation=special[san][li]
        moves.append(dict(san=san,uci=move.uci(),explanation=explanation));board.push(move)
    return dict(slug=slug,name=names[li],color=color,plan=plans[li],moves=moves)

def position(data,index):
    board=chess.Board()
    for move in data['moves'][:index]:board.push_uci(move['uci'])
    return dict(fen=board.fen(),index=index,finished=index==len(data['moves']),legal=[move.uci() for move in board.legal_moves])

def catalog(request):
    lang=current_language(request)
    return render(request,'games/openings.html',dict(o=TEXTS[lang],lessons=[lesson(row[0],lang) for row in LINES]))

@ensure_csrf_cookie
def play(request,slug):
    lang=current_language(request);data=lesson(slug,lang);mode='practice' if request.GET.get('mode')=='practice' else 'learn'
    index=1 if mode=='practice' and data['color']=='black' else 0
    return render(request,'games/opening_play.html',dict(o=TEXTS[lang],lesson=data,state=position(data,index),mode=mode))

@require_POST
def step(request,slug):
    lang=current_language(request);data=lesson(slug,lang)
    try:
        if len(request.body)>2048:raise ValueError
        body=json.loads(request.body)
        if not isinstance(body,dict):raise ValueError
        index=body['index'];mode=body['mode']
        if type(index) is not int or not 0<=index<len(data['moves']) or mode not in ('learn','practice'):raise ValueError
        if mode=='practice' and index%2 != (0 if data['color']=='white' else 1):raise ValueError
    except (ValueError,KeyError,TypeError):return JsonResponse({'error':TEXTS[lang]['network']},status=400)
    if mode=='practice' and body.get('move')!=data['moves'][index]['uci']:
        return JsonResponse(dict(position(data,index),correct=False,feedback=TEXTS[lang]['wrong']))
    end=min(index+(2 if mode=='practice' else 1),len(data['moves']))
    return JsonResponse(dict(position(data,end),correct=True,feedback=TEXTS[lang]['done'] if end==len(data['moves']) else TEXTS[lang]['correct'] if mode=='practice' else ''))
