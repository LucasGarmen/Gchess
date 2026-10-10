"""Independent painted clothing/hair layers and face-specific attachment points."""
from django.templatetags.static import static
from django.utils.html import escape
from .cosmetic_catalog import FREE_ITEMS

BOXES={
    'clothing':(24,99,112,59), 'accessory':(29,6,102,48),
    'hairstyle':(43,10,74,37), 'face':(54,85,52,32),
}
ITEM_BOXES={
    'clothing':{'cape':(20,98,120,63)},
    'accessory':{
        'cowboy':(21,10,118,44),'fedora':(27,8,106,46),
        'straw':(21,14,118,40),'visor':(30,30,100,24),
        'top_hat':(30,-3,100,57),'wizard':(29,-10,102,64),
        'crown':(39,12,82,42),'laurel':(41,15,78,39),
        'chef':(37,-2,86,56),'pirate':(23,10,114,44),
    },
    'hairstyle':{
        'dreads':(40,8,80,84),'purple_dreads':(40,8,80,84),
        'braids':(41,9,78,88),'red_braids':(41,9,78,88),
        'mohawk':(66,-1,28,49),'blue_mohawk':(66,-1,28,49),
        'punk':(64,-1,32,49),'afro':(35,1,90,51),
        'bun':(43,1,74,47),'ponytail':(42,8,85,84),
        'pink_bob':(38,8,84,80),'shaved':(47,26,66,20),
        'spikes':(41,4,78,43),'green_spikes':(41,4,78,43),
        'blond_quiff':(43,3,74,44),
    },
    'face':{
        'moustache':(62,84,36,12),'handlebar':(53,82,54,16),
        'stubble':(53,85,54,28),'goatee':(67,84,26,29),
        'long_beard':(52,84,56,48),'braided_beard':(52,84,56,48),
    },
}

def painted_wear(kind,item):
    if kind not in BOXES:return None
    if item=='none':return ''
    if item not in FREE_ITEMS[kind]:return None
    x,y,width,height=ITEM_BOXES.get(kind,{}).get(item,BOXES[kind])
    source=escape(static(f'games/avatars/wearables/{kind}-{item}.webp'))
    return (f'<image data-painted-wear="{kind}" data-wear-item="{item}" '
            f'href="{source}" x="{x}" y="{y}" width="{width}" height="{height}" '
            'preserveAspectRatio="none"/>')

# Eye and mouth positions refer to the painted 160-unit portrait, not the old SVG head.
HUMANS=('explorer','strategist','mentor','competitor','curly','scout','captain','pilot','messi')
FACE_POINTS={
    'explorer':(79,57,.77,78),'strategist':(80,58,.82,79),
    'mentor':(80,57,.8,79),'competitor':(80,58,.8,80),
    'curly':(80,60,.83,81),'scout':(80,59,.85,80),
    'captain':(80,57,.8,79),'pilot':(80,58,.8,80),'messi':(80,57,.8,80),
    'piece_pawn':(80,64,1.24,85),'piece_king':(80,71,.82,89),
    'piece_queen':(80,69,.86,89),'piece_bishop':(80,70,.8,91),
    'piece_rook':(80,63,.85,86),'piece_knight':(80,57,1.05,101),
    'bull':(80,56,.97,88),'bear':(80,59,.95,89),'shark':(80,60,1.25,89),
    'fox':(80,59,.93,89),'wolf':(80,59,.95,92),'tiger':(80,60,.95,90),
    'lion':(80,60,.95,90),'robot':(80,59,.95,88),
    'alien':(80,61,1.05,90),'crocodile':(80,58,1.0,91),
    'croc_safari':(80,58,1.0,92),'horse':(80,56,1.1,102),
    'zebra':(80,57,1.05,100),'dog':(80,57,.95,94),
    'elephant':(80,58,1.05,95),'panda':(80,60,.95,91),
    'raven':(80,59,.95,93),'eagle':(80,60,.95,94),
}

def attachment_transform(avatar,kind):
    x,eye,width,mouth=FACE_POINTS.get(avatar,(80,60,1.0,90))
    if kind=='eyewear':return f'translate({x} {eye}) scale({width} .85) translate(-80 -73)'
    if kind=='face':return f'translate({x} {mouth}) scale({min(width,1.05)} .9) translate(-80 -95)'
    if kind=='earrings':return f'translate({x} {eye+11}) scale({1 if avatar in HUMANS else 1.05} .85) translate(-80 -85)'
    if kind=='accessory':
        scale=.84 if avatar in HUMANS else 1.05 if avatar in ('bull','elephant','hippo','shark') else .95
        bottom=46 if avatar in HUMANS else 50
        return f'translate(80 {bottom}) scale({scale} .9) translate(-80 -54)'
    return ''
