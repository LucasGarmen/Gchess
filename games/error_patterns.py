"""Conservative, reproducible tactical evidence from owned saved engine reviews."""
import math
import chess
from collections import defaultdict
from django.urls import reverse
from .models import GameReview

TEXTS={
 'es':dict(title='Lo que se repite en tus partidas',scope='Buscamos ejemplos en una muestra de tus últimas 30 partidas revisadas. Solo señalamos un patrón cuando aparece en al menos dos partidas distintas; volver a analizar la misma no suma.',empty='Todavía no hay suficientes ejemplos para señalar un error repetido. Analizá tus partidas para encontrar qué conviene practicar.',hanging='Proteger las piezas',missed='Aprovechar una pieza sin defensa',tip_hanging='Antes de mover, mirá qué piezas tuyas puede capturar el rival y si podrías recuperarlas.',tip_missed='Antes de mover, buscá piezas rivales que puedas capturar sin que recuperen la tuya.',count='Aparece en {games} partidas revisadas.',example_hanging='Después de {played}, tu {piece} en {square} podía ser capturado sin una recaptura inmediata. El análisis recomendaba {best}.',example_missed='Elegiste {played}, pero había una captura disponible: {best}, sobre un {piece} en {square} sin recaptura inmediata.',review='Ver la partida',practice='Practicar este error',evidence='Ejemplos de tus partidas',single='Un caso aislado no define tu nivel.'),
 'pt':dict(title='O que se repete nas suas partidas',scope='Buscamos exemplos em uma amostra das suas últimas 30 partidas revisadas. Só indicamos um padrão quando aparece em pelo menos duas partidas diferentes; analisar a mesma novamente não conta.',empty='Ainda não há exemplos suficientes para indicar um erro repetido. Analise suas partidas para descobrir o que praticar.',hanging='Proteger as peças',missed='Aproveitar uma peça sem defesa',tip_hanging='Antes de jogar, veja quais peças suas o adversário pode capturar e se você conseguiria recuperá-las.',tip_missed='Antes de jogar, procure peças adversárias que você possa capturar sem uma recaptura.',count='Aparece em {games} partidas revisadas.',example_hanging='Depois de {played}, seu {piece} em {square} podia ser capturado sem uma recaptura imediata. A análise recomendava {best}.',example_missed='Você escolheu {played}, mas havia uma captura disponível: {best}, de um {piece} em {square} sem recaptura imediata.',review='Ver a partida',practice='Praticar este erro',evidence='Exemplos das suas partidas',single='Um caso isolado não define seu nível.'),
 'en':dict(title='Recurring mistakes in your games',scope='We look for examples in a sample of your latest 30 reviewed games. A pattern requires evidence in at least two different games; reanalyzing the same game does not count again.',empty='There is not enough evidence to identify a recurring mistake yet. Analyze your games to find what to practice.',hanging='Protect your pieces',missed='Capture an undefended piece',tip_hanging='Before moving, check which of your pieces your opponent can capture and whether you could recapture.',tip_missed='Before moving, look for opposing pieces you can capture without an immediate recapture.',count='Appears in {games} reviewed games.',example_hanging='After {played}, your {piece} on {square} could be captured without an immediate recapture. The analysis recommended {best}.',example_missed='You chose {played}, but a capture was available: {best}, taking a {piece} on {square} without an immediate recapture.',review='View game',practice='Practice this mistake',evidence='Examples from your games',single='One isolated case does not define your ability.'),
}
PIECES={'es':{2:'caballo',3:'alfil',4:'torre',5:'dama'},'pt':{2:'cavalo',3:'bispo',4:'torre',5:'dama'},'en':{2:'knight',3:'bishop',4:'rook',5:'queen'}}


def move_description(board, move, language):
    names={
        'es':{1:'el peón',2:'el caballo',3:'el alfil',4:'la torre',5:'la dama',6:'el rey'},
        'pt':{1:'o peão',2:'o cavalo',3:'o bispo',4:'a torre',5:'a dama',6:'o rei'},
        'en':{1:'your pawn',2:'your knight',3:'your bishop',4:'your rook',5:'your queen',6:'your king'},
    }
    if board.is_castling(move):return {'es':'enrocar','pt':'rocar','en':'castling'}[language]
    text={'es':'mover {piece} a {square}','pt':'mover {piece} para {square}','en':'moving {piece} to {square}'}[language].format(piece=names[language][board.piece_at(move.from_square).piece_type],square=chess.square_name(move.to_square))
    if move.promotion:
        text+=' '+{'es':'y coronar a {piece}','pt':'e promover para {piece}','en':'and promoting to {piece}'}[language].format(piece=names[language][move.promotion])
    return text

def loose_targets(board, color):
    """Only legal captures of non-pawns that permit no immediate legal recapture."""
    if board.turn == color: return {}
    targets={}
    for move in list(board.legal_moves):
        piece=board.piece_at(move.to_square)
        if not piece or piece.color != color or piece.piece_type not in (2,3,4,5): continue
        after=board.copy();after.push(move)
        # Terminal positions are not material-loss evidence (mate/stalemate).
        if after.is_game_over(): continue
        if any(reply.to_square == move.to_square and after.is_capture(reply) for reply in after.legal_moves): continue
        targets[move.to_square]=piece.piece_type
    return targets

def detect(board, played, best):
    after=board.copy();after.push(played)
    preferred=board.copy();preferred.push(best)
    exposed=loose_targets(after,board.turn)
    avoided=loose_targets(preferred,board.turn)
    for square,piece in exposed.items():
        if square not in avoided: return dict(kind='hanging',square=chess.square_name(square),piece_type=piece)
    if board.is_capture(best) and not board.is_capture(played):
        piece=board.piece_at(best.to_square)
        if piece and piece.piece_type in (2,3,4,5) and not preferred.is_game_over():
            if not any(move.to_square==best.to_square and preferred.is_capture(move) for move in preferred.legal_moves):
                return dict(kind='missed',square=chess.square_name(best.to_square),piece_type=piece.piece_type)
    return None

def recurring_errors(user, language):
    texts=TEXTS[language];groups=defaultdict(dict);seen=set();positions={};checked=0
    if not user.is_authenticated:return dict(texts=texts,patterns=[],positions={},reviewed=0)
    for review in GameReview.objects.filter(user=user).order_by('-created_at').only('pk','game_id','fingerprint','player_color','payload','created_at')[:90]:
        identity=('game',review.game_id) if review.game_id else ('pgn',review.fingerprint)
        if identity in seen:continue
        if len(seen)>=30 or checked>=120:break
        seen.add(identity)
        payload=review.payload
        if not isinstance(payload,dict):continue
        moves,analysis=payload.get('moves',[]),payload.get('analysis',[])
        if not isinstance(moves,list) or not isinstance(analysis,list):continue
        for move,item in list(zip(moves,analysis))[:500]:
            if checked>=120:break
            if not isinstance(move,dict) or not isinstance(item,dict) or move.get('piece_color')!=review.player_color:continue
            loss=item.get('loss')
            if item.get('classification') not in ('mistake','blunder') or not isinstance(loss,(int,float)) or not math.isfinite(loss) or loss<150:continue
            context=item.get('engine_context')
            if not isinstance(context,dict):continue
            try:
                board=chess.Board(context['fen_before']);played=chess.Move.from_uci(context['played_move_uci']);best=chess.Move.from_uci(context['best_move_uci'])
                if not board.is_valid() or board.is_game_over() or played not in board.legal_moves or best not in board.legal_moves or played==best:continue
                if ('white' if board.turn else 'black')!=review.player_color:continue
                checked+=1
                finding=detect(board,played,best)
                if not finding:continue
                key=' '.join(board.fen().split()[:4]);kind=finding['kind']
                example=dict(finding,played=move_description(board,played,language),best=move_description(board,best,language),piece=PIECES[language][finding['piece_type']],review_id=review.pk,date=review.created_at.date(),position_key=key)
            except (ValueError,KeyError,TypeError):continue
            # One game contributes at most one example to each pattern.
            if identity not in groups[kind]:groups[kind][identity]=example
            positions[key]=kind
    patterns=[]
    for kind,examples in groups.items():
        if len(examples)<2:continue
        sample=list(examples.values())[:2]
        for example in sample:
            example['explanation']=texts['example_'+kind].format(**example)
            example['url']=reverse('review_detail',args=[example['review_id']])
        patterns.append(dict(kind=kind,label=texts[kind],tip=texts['tip_'+kind],games=len(examples),count_text=texts['count'].format(games=len(examples)),examples=sample,practice_url=reverse('review_practice',args=[sample[0]['review_id']])+'?pattern='+kind))
    patterns.sort(key=lambda p:-p['games'])
    recurring={p['kind'] for p in patterns}
    return dict(texts=texts,patterns=patterns,positions={k:v for k,v in positions.items() if v in recurring},reviewed=len(seen))
