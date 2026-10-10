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
