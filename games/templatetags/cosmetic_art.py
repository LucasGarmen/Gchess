from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from games.cosmetic_art import avatar_art, accessory_shape, valid, circle, path
from games.cosmetic_catalog import FREE_ITEMS
register=template.Library()

@register.simple_tag
def draw_avatar(avatar,accessory='none',clothing='club',face='none',hairstyle='none',eyewear='none',earrings='none',framing='',label='Avatar'):
    framing='bust' if framing=='bust' else 'portrait'
    view='24 8 112 146' if framing=='bust' else '26 8 108 108'
    svg=avatar_art(avatar,accessory,clothing,face,hairstyle,eyewear,earrings,framing)
    # Each inline portrait needs independent paint servers, including hidden coaches.
    import re
    from uuid import uuid4
    suffix=uuid4().hex
    for identifier in re.findall(r'id="([^"]+)"',svg):
        svg=svg.replace(f'id="{identifier}"',f'id="{identifier}-{suffix}"').replace(f'url(#{identifier})',f'url(#{identifier}-{suffix})')
    return mark_safe(f'<svg class="gchess-avatar" viewBox="{view}" role="img" aria-label="{escape(label)}" xmlns="http://www.w3.org/2000/svg" data-avatar-rig="bust-v1" data-framing="{framing}">{svg}</svg>')

@register.simple_tag
def draw_object(kind,item):
    if kind not in ('accessory','clothing','hairstyle','face','eyewear','earrings'):return ''
    item=valid(kind,item)
    views={'accessory':'28 7 104 72','clothing':'18 104 124 59','hairstyle':'28 6 104 100','face':'47 80 66 48','eyewear':'47 58 66 44','earrings':'40 69 80 36'}
    if item=='none':
        view='48 50 64 64';svg=circle(80,82,18,'none','#aa9772',2)+path('M67 95L93 69','none','#aa9772',2)
    else:view=views[kind];svg=accessory_shape(kind,item)
    return mark_safe(f'<svg class="shop-accessory-art" viewBox="{view}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">{svg}</svg>')

@register.simple_tag
def player_avatar(player,label='Avatar'):
    from games.models import CosmeticLoadout
    from games.cosmetic_catalog import DEFAULTS,usable_loadout
    selected=CosmeticLoadout.objects.filter(user=player).first() if player and getattr(player,'is_authenticated',False) else None
    values=usable_loadout(selected or DEFAULTS)
    return draw_avatar(values['avatar'],values['accessory'],values['clothing'],values['face'],values['hairstyle'],values['eyewear'],values['earrings'],framing='bust',label=label)

@register.simple_tag
def coach_portraits():
    # Coach identities are independent of shop entitlements.
    levels=((500,'explorer','club'),(800,'scout','forest'),(1000,'pilot','ivory'),(1320,'strategist','vest'),(1600,'captain','tuxedo'),(2000,'mentor','kimono'),(2500,'piece_king','armor'))
    return mark_safe(''.join(f'<span data-coach-level="{level}"'+(' hidden' if level!=500 else '')+'>'+str(draw_avatar(avatar,clothing=cloth,label=f"Coach · {level}"))+'</span>' for level,avatar,cloth in levels))

@register.simple_tag
def analyzer_words(lang):
    keys=('eyebrow','intro','load','review','coach','file','file_help','file_error','loaded','color_help','new','position')
    words={
    'es':('Tu partida, paso a paso','Cargá una partida y recorré sus jugadas. Consultá al coach sobre la posición que estás viendo.','Cargá tu PGN','Revisá las jugadas','Conversá con el coach','Abrir archivo PGN','Podés pegar el PGN o abrir un archivo .pgn o .txt.','No se pudo abrir. Elegí un archivo .pgn o .txt de hasta 80 KB.','Archivo cargado: ','Elegí el color con el que jugaste para orientar el análisis.','Otra partida','La jugada que estás revisando'),
    'pt':('Sua partida, passo a passo','Carregue uma partida e percorra as jogadas. Consulte o coach sobre a posição que está vendo.','Carregue seu PGN','Revise as jogadas','Converse com o coach','Abrir arquivo PGN','Cole o PGN ou abra um arquivo .pgn ou .txt.','Não foi possível abrir. Escolha um arquivo .pgn ou .txt de até 80 KB.','Arquivo carregado: ','Escolha a cor com que jogou para orientar a análise.','Outra partida','A jogada que você está revisando'),
    'en':('Your game, move by move','Load a game and explore its moves. Ask the coach about the position you are viewing.','Load your PGN','Review the moves','Talk with the coach','Open PGN file','Paste the PGN or open a .pgn or .txt file.','Could not open. Choose a .pgn or .txt file up to 80 KB.','File loaded: ','Choose the color you played to guide the analysis.','Another game','The move you are reviewing')}
    return dict(zip(keys,words.get(lang,words['en'])))

@register.simple_tag
def entry_board(kind):
    """Small decorative legal positions; the actual game remains interactive."""
    import chess
    from django.templatetags.static import static
    board=chess.Board()
    lines={'coach':['e4','e5','Nf3','Nc6'], 'friends':['d4','d5','c4','e6'], 'train':['e4','e5','Nf3','Nc6','Bc4','Nf6','Ng5']}
    for move in lines.get(kind,[]):
        board.push_san(move)
    names={chess.PAWN:'pawn',chess.KNIGHT:'horse',chess.BISHOP:'bishop',chess.ROOK:'rook',chess.QUEEN:'queen',chess.KING:'king'}
    cells=[]
    for rank in range(7,-1,-1):
        for file in range(8):
            piece=board.piece_at(chess.square(file,rank))
            art=''
            if piece:
                src=static('games/pieces-rustic/'+names[piece.piece_type]+'_'+('white' if piece.color else 'black')+'.svg')
                art=f'<img src="{escape(src)}" alt="" loading="lazy" draggable="false">'
            cells.append(f'<span class="entry-square {"entry-light" if (rank+file)%2 else "entry-dark"}">{art}</span>')
    return mark_safe('<div class="entry-mini-board" aria-hidden="true">'+''.join(cells)+'</div>')

@register.simple_tag
def quick_play_words(lang):
    words={
        'es':('Partida rápida','Buscamos un rival disponible con Elo cercano. 5 min · sin cambiar tu Elo. Invitados: nivel inicial 800.','Jugar ahora','Entrá para buscar rival'),
        'pt':('Partida rápida','Buscamos um adversário disponível com Elo próximo. 5 min · sem alterar seu Elo. Visitantes: nível inicial 800.','Jogar agora','Entre para encontrar um adversário'),
        'en':('Quick match','Find an available opponent with a nearby Elo. 5 min · unrated. Guests start at level 800.','Play now','Sign in to find an opponent')}
    return dict(zip(('title','help','play','login'),words.get(lang,words['en'])))


@register.simple_tag
def home_hero_words(lang):
    words={
        'es':('Entrená con nuestro coach','Jugá ajedrez. Entendé cada jugada.','Elegí tu nivel, jugá y preguntale al coach cómo mejorar.','Entrenar con el coach','A tu ritmo · Desde principiante','Jugar una partida rápida','Con un rival disponible · 5 minutos','Jugá con amigos','Compartí una invitación y desafialos.','Practicá una posición','Puzzles, aperturas y ejercicios para mejorar.'),
        'pt':('Treine com nosso coach','Jogue xadrez. Entenda cada lance.','Escolha seu nível, jogue e pergunte ao coach como melhorar.','Treinar com o coach','No seu ritmo · Desde iniciante','Jogar uma partida rápida','Com um adversário disponível · 5 minutos','Jogue com amigos','Compartilhe um convite e desafie seus amigos.','Pratique uma posição','Puzzles, aberturas e exercícios para melhorar.'),
        'en':('Train with our coach','Play chess. Understand every move.','Choose your level, play and ask the coach how to improve.','Train with the coach','At your pace · Beginners welcome','Play a quick match','With an available opponent · 5 minutes','Play with friends','Share an invitation and challenge your friends.','Practice a position','Puzzles, openings and exercises to improve.')}
    keys=('title','eyebrow','intro','coach','coach_hint','quick','quick_hint','friends','friends_help','practice','practice_help')
    return dict(zip(keys,words.get(lang,words['en'])))
