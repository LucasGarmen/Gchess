"""Blindfold play reuses the regular board, move and clock validation paths."""
import re
import uuid
import chess
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .i18n import current_language

KEYS = ('title','intro','coach','human','toggle','exclusive','exclusive_help','personal_help','move','send','help','notation','native','english','history','empty','invalid','network','turn','waiting','finished','changed','new','mode','normal','blind','fair_help')
ROWS = {
 'es': ('Ajedrez a ciegas','Entrená memoria y cálculo: recordá la posición y escribí tus jugadas sin ver el tablero.','A ciegas con el coach','A ciegas contra otra persona','Ocultar tablero · jugar a ciegas','Partida exclusiva a ciegas','Ambos juegan sin tablero. Podés mostrarlo para revisar cuando termine la partida.','Esta opción oculta tu tablero. Podés volver a mostrarlo cuando quieras; el rival conserva su propia elección.','Tu jugada','Jugar','Ejemplos: e4, Cf3, O-O o e2e4. Para promover: e7e8q (dama), r (torre), b (alfil), n (caballo).','Notación','Español · C caballo, A alfil, T torre, D dama, R rey','Inglés · N caballo, B alfil, R torre, Q dama, K rey','Historial de jugadas','Todavía no hay jugadas. Empiezan las blancas.','No pudimos interpretar una jugada legal. Revisá el turno y la notación; si dos piezas pueden ir a esa casilla, indicá cuál (por ejemplo, Cgf3) o usá coordenadas.','No pudimos validar la jugada. Tu texto quedó guardado; intentá de nuevo.','Tu turno','Esperando al rival','La partida terminó. Podés mostrar el tablero para revisarla.','La posición cambió. Revisá la última jugada y volvé a intentarlo.','Nueva partida a ciegas','Forma de jugar','Con tablero','A ciegas','En partidas normales cada persona puede ocultar su tablero. En el modo exclusivo, ambos aceptan jugar sin verlo y sin ayuda de otro tablero.'),
 'pt': ('Xadrez às cegas','Treine memória e cálculo: lembre a posição e escreva suas jogadas sem ver o tabuleiro.','Às cegas com o coach','Às cegas contra outra pessoa','Ocultar tabuleiro · jogar às cegas','Partida exclusiva às cegas','Ambos jogam sem tabuleiro. Você pode mostrá-lo para revisar quando a partida terminar.','Esta opção oculta seu tabuleiro. Você pode mostrá-lo quando quiser; o adversário mantém sua própria escolha.','Sua jogada','Jogar','Exemplos: e4, Cf3, O-O ou e2e4. Para promover: e7e8q (dama), r (torre), b (bispo), n (cavalo).','Notação','Português · C cavalo, B bispo, T torre, D dama, R rei','Inglês · N cavalo, B bispo, R torre, Q dama, K rei','Histórico de jogadas','Ainda não há jogadas. As brancas começam.','Não conseguimos interpretar uma jogada legal. Confira a vez e a notação; se duas peças podem ir à casa, indique qual (por exemplo, Cgf3) ou use coordenadas.','Não foi possível validar a jogada. Seu texto foi preservado; tente novamente.','Sua vez','Esperando o adversário','A partida terminou. Você pode mostrar o tabuleiro para revisar.','A posição mudou. Confira a última jogada e tente novamente.','Nova partida às cegas','Forma de jogar','Com tabuleiro','Às cegas','Em partidas normais cada pessoa pode ocultar seu tabuleiro. No modo exclusivo, ambos aceitam jogar sem vê-lo e sem ajuda de outro tabuleiro.'),
 'en': ('Blindfold chess','Train memory and calculation: remember the position and type your moves without seeing the board.','Blindfold with the coach','Blindfold against another player','Hide board · play blindfold','Exclusive blindfold game','Both players play without a board. You can reveal it to review when the game ends.','This hides your board. You can reveal it at any time; the other player keeps their own choice.','Your move','Play','Examples: e4, Nf3, O-O or e2e4. To promote: e7e8q (queen), r (rook), b (bishop), n (knight).','Notation','English · N knight, B bishop, R rook, Q queen, K king','English · N knight, B bishop, R rook, Q queen, K king','Move history','No moves yet. White moves first.','We could not interpret a legal move. Check the turn and notation; if two pieces can reach that square, specify which (for example, Ngf3) or use coordinates.','Could not validate your move. Your text was preserved; try again.','Your turn','Waiting for the opponent','The game ended. You can reveal the board to review.','The position changed. Check the last move and try again.','New blindfold game','Playing mode','With board','Blindfold','In normal games each player can hide their own board. In exclusive mode both agree to play without seeing it or using another board.'),
}
TEXTS = {language: dict(zip(KEYS, row, strict=True)) for language,row in ROWS.items()}

def navigation(request):
    return {'blindfold': TEXTS[current_language(request)]}

def landing(request):
    return render(request,'games/blindfold.html',{'coach_url':reverse('home')+'?bot=blind-'+uuid.uuid4().hex+'&blindfold=exclusive'})

def piece_map(language):
    return {'C':'N','A':'B','T':'R','D':'Q','R':'K'} if language=='es' else {'C':'N','B':'B','T':'R','D':'Q','R':'K'} if language=='pt' else {}

def parse_move(board, notation, language='en'):
    if not isinstance(notation,str) or not 1 <= len(notation.strip()) <= 32:
        raise ValueError('Invalid notation')
    value=notation.strip()
    if re.fullmatch(r'[a-h][1-8][a-h][1-8][qrbn]?',value.lower()):
        move=chess.Move.from_uci(value.lower())
    else:
        value=value.replace('0','O')
        mapping=piece_map(language)
        if value[0] in mapping:
            value=mapping[value[0]]+value[1:]
        value=re.sub(r'=([CATDRBNQK])',lambda match:'='+mapping.get(match[1],match[1]),value)
        move=board.parse_san(value)
    if not move or move not in board.legal_moves:
        raise ValueError('Illegal move')
    return move

def local_san(san,language):
    mapping={value:key for key,value in piece_map(language).items()}
    if san and san[0] in mapping:
        san=mapping[san[0]]+san[1:]
    return re.sub(r'=([NBRQK])',lambda match:'='+mapping.get(match[1],match[1]),san)

@require_POST
@never_cache
def position(request):
    from .views import (parse_json_body, get_game_for_user, ordered_game_moves,
        serialize_moves, decode_trainer_moves, board_from_move_data)
    language=current_language(request)
    texts=TEXTS[language]
    try:
        data=parse_json_body(request)
        notation_language='en' if data.get('notation_language')=='en' else language
        if data.get('game_id'):
            game=get_game_for_user(data['game_id'],request.user,request.session.get('guest_id'),with_moves=True)
            moves=serialize_moves(game,ordered_game_moves(game))
        else:
            game=None
            moves=decode_trainer_moves(data.get('moves',[]))
        board,history=board_from_move_data(moves)
        payload={'history':[local_san(san,notation_language) for san in history],
                 'turn':'white' if board.turn else 'black','move_count':len(moves)}
        if 'notation' in data:
            if game and game.status=='finished':
                return JsonResponse({'error':texts['finished']},status=409)
            move=parse_move(board,data['notation'],notation_language)
            promotion={chess.QUEEN:'queen',chess.ROOK:'rook',chess.BISHOP:'bishop',chess.KNIGHT:'horse'}.get(move.promotion)
            payload['move']={'from':chess.square_name(move.from_square),'to':chess.square_name(move.to_square),'promotion':promotion}
        return JsonResponse(payload)
    except (ValueError,TypeError,KeyError,IndexError):
        return JsonResponse({'error':texts['invalid']},status=400)

# Shared JSON size validation and per-player rate limiting protect the parser.
from .views import rate_limit
position = rate_limit(120, 60, 'blindfold-position')(position)
