"""Original vector art for the Gchess collection; all inputs resolve to the server catalog."""
from .cosmetic_catalog import FREE_ITEMS, DEFAULTS

def valid(kind,item):
    return item if item in FREE_ITEMS[kind] else DEFAULTS[kind]

def path(d,fill='#30372b',stroke='#c1a06b',width=1.5):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'

def circle(x,y,r,fill,stroke='none',width=1.5):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'

def rect(x,y,w,h,fill,stroke='none',radius=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'

CLOTH_COLORS=['#536950','#e2cca0','#395742','#a5684e','#6d627f','#517387','#433b31','#242e29','#875040','#b69570','#537b66','#8b5847','#866478','#74817b','#983f47','#bcc6b9','#dad0ae','#49766b','#6f694f','#66758d']
def clothing(item):
    item=valid('clothing',item);idx=FREE_ITEMS['clothing'].index(item);c=CLOTH_COLORS[idx]
    base=path('M24 145Q28 119 60 107H100Q132 119 136 145Q80 164 24 145Z',c)
    if item=='cape':return path('M24 145L45 107L80 117L115 107L136 145Q80 170 24 145Z',c)+path('M62 108L80 122L98 108','none')
    if item in ('hoodie','space_suit','puffer'):
        base+=path('M57 108Q48 114 57 124L80 128L103 124Q112 114 103 108L95 119H65Z',c)
        if item=='hoodie':base+=path('M69 125v17M91 125v17','none','#ecd6a0',2)
        if item=='space_suit':base+=rect(68,131,24,13,'#35483f','#ddd3ad')+circle(75,137,2,'#c9a45c')+circle(85,137,2,'#74a99a')
        if item=='puffer':base+=path('M34 128h92M30 138h100M80 123v30','none','#bcc4bc',2)
    elif item=='armor':base+=path('M38 119L62 111L80 123L98 111L122 119L112 150H48Z','#83958b')+path('M80 123v29M48 132h64','none','#d1bd87',3)
    elif item=='kimono':base+=path('M57 108L94 152M103 109L71 141','none','#e8c7a0',5)
    elif item=='tuxedo':base+=path('M62 109L80 143L98 109','#efdfb9')+path('M68 119L80 124L92 119V129L80 124L68 129Z','#4b2927')
    else:
        base+=path('M60 108L80 126L100 108L104 117L91 135L80 126L69 135L56 117Z',c,'#d1b988')
        if item in ('denim','leather','bomber','varsity','vest'):base+=path('M80 127v28M43 134h18M99 134h18','none','#ddc6a1',2)
        if item=='jersey':base+=rect(71,131,18,15,'#e1d3ae')+path('M77 134h6l-5 9','none','#7b453a',2)
        if item=='striped':base+=path('M42 126h76M35 138h90M31 150h98','none','#426456',4)
        if item=='hawaiian':
            for x,y in [(47,128),(105,134),(66,143),(112,148)]:base+=path(f'M{x-4} {y}h8M{x} {y-4}v8M{x-3} {y-3}l6 6','none','#e4bf80',2)
    return base

def headwear(item):
    item=valid('accessory',item)
    if item=='none':return ''
    crown=path('M44 48Q44 19 80 19Q111 19 116 48Z','#52634b')
    brim=path('M42 47Q80 38 123 49L119 56Q80 48 44 57Z','#293d32')
    if item=='cap':return crown+brim+path('M73 28h10v5h-2v8h-6v-8h-2Z','#e1c17c')
    if item=='beret':return path('M43 47Q35 25 67 23Q94 12 115 29Q125 41 110 48Z','#8d4d3f')+path('M47 46Q80 40 111 47L109 53H48Z','#442e28')+path('M80 23l4-9','none')
    if item in ('beanie','earflap'):
        s=path('M44 49Q45 19 80 19Q113 19 115 49Z','#b29262')+circle(80,16,7,'#e3c996')+path('M58 30v16M69 27v18M81 26v18M94 28v17M105 33v13','none','#826641',2)+path('M43 45Q80 39 116 46L114 58Q80 51 46 59Z','#d0b17c')
        return s+(path('M46 52v26l9-7V54M113 52v26l-9-7V54','#b29262') if item=='earflap' else '')
    if item=='visor':return path('M47 40Q80 34 112 42V50Q80 44 47 49Z','#c6ae79')+brim
    if item in ('fedora','cowboy','straw','flat_cap'):
        c={'fedora':'#665340','cowboy':'#9a774b','straw':'#d7bb77','flat_cap':'#737258'}[item]
        if item=='flat_cap':return path('M44 46Q49 24 82 28Q106 31 116 47L99 51H47Z',c)+brim
        return path('M49 44L54 22L80 28L104 22L112 44Z',c)+path('M37 44Q80 53 123 44L129 55Q80 65 31 55Z',c)+path('M52 40h58v6H50Z','#38372b')
    if item=='bucket':return path('M51 22H107L112 45L123 56Q80 63 37 56L48 45Z','#8a8861')+path('M48 44h64','none')
    if item=='top_hat':return path('M53 16H107L104 46H56Z','#343b31')+path('M56 38h48v8H56Z','#7d4437')+path('M38 46Q80 54 122 46V56Q80 64 38 56Z','#343b31')
    if item=='crown':return path('M45 48L40 23L62 35L80 13L98 35L120 23L115 48Z','#d0a954')+path('M46 48h68v8H46Z','#9c7031')+circle(80,42,4,'#8b493d')
    if item=='pirate':return path('M36 47L46 19L80 31L114 19L124 47Q80 57 36 47Z','#2b3430')+circle(80,36,5,'#e9d7ac')+path('M71 45l18-6M71 39l18 6','none','#e9d7ac',2)
    if item=='turban':return path('M43 49Q35 17 80 17Q126 17 116 49Z','#966b7b')+path('M47 32Q78 54 112 29M48 24Q79 44 115 38','none','#dab993',3)+circle(80,47,5,'#e2bf78')
    if item=='wizard':return path('M47 48L74 12L91 20L112 48Z','#4c5677')+path('M34 48Q80 58 125 48L121 59H39Z','#4c5677')+path('M78 29l3 5 5 1-4 4 1 5-5-2-4 2 1-5-4-4 5-1Z','#dbc079')
    if item=='helmet':return path('M43 48Q44 15 80 15Q115 15 116 48L111 61H49Z','#788477')+path('M52 43Q80 37 109 43L106 53H55Z','#31483d')
    if item=='sailor':return path('M48 38Q43 20 81 20Q117 20 113 38Z','#e4dcc6')+rect(47,38,66,13,'#ece3ce')+path('M77 40v8M73 44h8','none','#435f69',2)
    if item=='laurel':
        return ''.join(path(f'M{x} {y}q-10-9-12 1q8 9 12-1M{160-x} {y}q10-9 12 1q-8 9-12-1Z','#859355') for x,y in [(48,49),(51,37),(59,27),(69,22)])
    if item=='chef':return circle(60,24,13,'#eee4cb')+circle(80,18,14,'#eee4cb')+circle(101,24,13,'#eee4cb')+path('M51 28H110L106 52H55Z','#eee4cb')+path('M57 43h48','none','#a69472')
    return ''

def hair(item):
    item=valid('hairstyle',item)
    if item=='none':return ''
    if item=='shaved':return path('M49 49Q49 28 80 28Q111 28 111 49Q80 38 49 49Z','#b29b76','#6e614c')
    c={'blue_mohawk':'#547b9e','pink_bob':'#b66d88','green_spikes':'#739450','red_braids':'#a35f45','blond_quiff':'#c5a25a','purple_dreads':'#866888','silver_crop':'#a7a699'}.get(item,'#514333')
    if item in ('dreads','purple_dreads','braids','red_braids'):
        s=path('M49 45Q45 25 80 22Q114 23 113 45Z',c)
        for x in [46,54,65,77,89,101,112]:s+=path(f'M{x} 36Q{x-4} 49 {x} 62L{x+2} {92 if x in (46,112) else 51}','none',c,7 if 'dreads' in item or item=='dreads' else 5)
        return s
    if item in ('mohawk','blue_mohawk','punk'):return path('M68 47L68 26L72 12L82 18L88 10L94 27L92 47Z',c)
    if item=='afro':return ''.join(circle(x,y,12,c) for x,y in [(50,43),(50,28),(64,21),(79,18),(94,21),(109,28),(111,42)])
    if item in ('bun','ponytail'):
        return circle(81,19,10,c)+path('M46 48Q42 26 80 27Q117 27 114 48L106 57L101 43H59L54 57Z',c)+(path('M108 36Q133 61 113 91L104 72Z',c) if item=='ponytail' else '')
    if item in ('spikes','green_spikes'):return path('M46 57L42 37L53 40L57 20L69 30L78 13L86 31L99 20L103 40L117 37L111 57L99 47L82 43L60 48Z',c)
    if item in ('curls','waves'):
        return ''.join(circle(x,y,7,c) for x,y in [(51,42),(60,34),(71,30),(83,31),(94,33),(105,41)])
    if item=='pink_bob':return path('M42 76V44Q42 23 80 24Q117 23 118 44V77L104 84L103 47H57L56 84Z',c)
    return path('M47 65L47 43Q50 23 83 25L105 32L114 48L110 61L101 42Q81 52 59 44L55 65Z',c)+path('M59 36Q79 31 100 36','none','#c8ae79',1)

def beard(item):
    item=valid('face',item)
    if item=='none':return ''
    c='#9a998c' if item=='silver_beard' else '#45372c'
    if item in ('moustache','handlebar'):
        s=path('M80 89Q75 84 70 88Q66 92 63 90Q67 99 80 93Q93 99 97 90Q94 92 90 88Q85 84 80 89Z',c,'none')
        return s+(path('M64 92Q53 91 56 86M96 92Q107 91 104 86','none',c,3) if item=='handlebar' else '')
    if item=='stubble':return ''.join(circle(x,y,0.9,c) for x,y in [(58,90),(62,96),(69,101),(78,105),(87,103),(96,98),(102,91),(70,90),(90,90)])
    if item=='goatee':return path('M72 99Q80 103 88 99L86 111H74Z',c,'none')+path('M70 89Q80 85 90 89','none',c,3)
    bottom=123 if item in ('long_beard','braided_beard') else 110
    s=path(f'M54 84Q58 96 69 98L80 100L91 98Q102 96 106 84L104 103L91 {bottom}H69L56 103Z',c,'none')+path('M71 90Q80 86 89 90','none',c,4)
    if item=='braided_beard':s+=path('M74 103l12 5-12 5 12 5','none','#b29465',2)
    return s

def eyewear(item):
    item=valid('eyewear',item)
    if item=='none':return ''
    bridge=path('M76 71Q80 67 84 71M48 69h6M106 69h6','none','#d4b77d',2)
    if item=='round':return circle(65,73,11,'none','#d4b77d',2)+circle(95,73,11,'none','#d4b77d',2)+bridge
    if item=='monocle':return circle(95,73,10,'none','#d4b77d',2)+path('M104 78L110 99','none','#d4b77d',1)
    if item in ('sport','visor_lens'):return path('M51 63Q80 58 109 63L106 79Q80 86 54 79Z','#456e71','#d4b77d')+path('M58 66l13-2','none','#a9d5c9',2)
    fill='#2c4547' if item=='sunglasses' else 'none'
    if item=='aviator':return path('M54 65H76L74 78Q65 88 56 78ZM84 65H106L104 78Q95 88 86 78Z',fill,'#d4b77d',2)+bridge
    return rect(54,65,22,16,fill,'#d4b77d',2 if item=='square' else 5)+rect(84,65,22,16,fill,'#d4b77d',2 if item=='square' else 5)+bridge

def earrings(item):
    item=valid('earrings',item)
    if item=='none':return ''
    out='';c='#dcb763' if item=='gold_hoops' else '#d1d4c3'
    for x in (48,112):
        if item in ('gold_hoops','silver_hoops'):out+=circle(x,85,5,'none',c,2.5)
        elif item=='studs':out+=circle(x,80,2.5,c)
        elif item=='diamond':out+=path(f'M{x} 77l4 4-4 5-4-5Z','#d5eae5')
        elif item=='chain':out+=circle(x,81,2,c)+path(f'M{x} 83v13','none',c,2)+circle(x,97,3,'#cdb979')
        else:out+=circle(x,81,4,'#232e2a','#a5b19a')
    return out

SPECIES={'dinosaur':'#6f9655','alien':'#8cac72','bear':'#9f7956','tiger':'#bd8a4b','robot':'#91a49c','crocodile':'#69815a','shark':'#719397','fox':'#b97d4a','wolf':'#879288','panda':'#e2d9bf','dragon':'#8b726f'}
from .cosmetic_art_more import COLORS as EXTRA_COLORS
SPECIES.update(EXTRA_COLORS)
from .cosmetic_piece_avatars import COLORS as PIECE_COLORS
SPECIES.update(PIECE_COLORS)

def head(avatar):
    from .cosmetic_piece_avatars import piece_head
    piece=piece_head(avatar)
    if piece is not None:return piece
    from .cosmetic_portraits import human_head, OUTLINES, portrait_eyes, portrait_finish
    human=human_head(avatar)
    if human is not None:return human
    from .cosmetic_art_more import extra_head
    custom=extra_head(avatar)
    if custom is not None:return custom
    if avatar=='robot':return path('M46 46L56 35H104L114 46V92L101 107H59L46 92Z','#91a49c')+rect(53,62,54,20,'#273e36')+path('M57 70h13M90 70h13','none','#abc8a1',3)+rect(65,91,30,8,'#4b6256')+path('M71 93v4M80 93v4M89 93v4','none','#c9d4b3')
    c=SPECIES.get(avatar,'#cf956d' if avatar in ('strategist','mentor','captain','pilot') else '#e6b993')
    out=''
    if avatar in ('bear','panda'):out+=circle(51,39,13,c,'#796247')+circle(109,39,13,c,'#796247')+circle(51,39,7,'#594e3c')+circle(109,39,7,'#594e3c')
    if avatar in ('tiger','fox','wolf','dragon'):out+=path('M46 52L43 24L67 41M114 52L117 24L93 41Z',c)+path('M49 42L48 33L58 43M111 42L112 33L102 43Z','#dac1a0')
    if avatar in ('dinosaur','crocodile','dragon'):out+=path('M53 39L58 24L68 33L80 19L90 32L102 26L108 43Z',c)
    if avatar=='shark':out+=path('M68 37L84 15L95 43Z',c)
    outline='M49 55Q49 31 80 32Q111 31 111 55L108 84L98 102L80 109L62 102L52 84Z'
    if avatar=='alien':outline='M43 49Q42 22 80 21Q119 22 117 49L109 83L92 105H68L51 83Z'
    outline=OUTLINES.get(avatar,outline)
    lighting,fill=portrait_finish(avatar,c)
    out=lighting+out+path(outline,fill,'#6a6446',1.1)
    out+=path('M54 55Q55 39 71 37','none','#e5d9b0',1.5)
    if avatar in ('bear','panda','tiger','fox','wolf','crocodile','dinosaur','dragon','shark'):
        muzzle='#dfcea6' if avatar not in ('crocodile','dinosaur','dragon','shark') else '#9bad7d'
        out+=path('M54 84Q54 76 80 77Q106 76 106 84L104 99H56Z' if avatar=='crocodile' else 'M59 88Q59 78 80 79Q101 78 101 88L94 101H66Z',muzzle,'none')+path('M74 85H86L80 92Z','#3d4637','none')
    else:out+=path('M80 73l-3 12q3 2 7 0','none','#946b50',1.5)
    if avatar=='panda':out+=path('M54 62Q65 55 73 63L70 81H57ZM87 63Q95 55 106 62L103 81H90Z','#454e40','none')
    if avatar=='tiger':out+=path('M49 62l9 5-9 3M111 62l-9 5 9 3M63 38l5 16M80 34v17M97 38l-5 16','none','#4b4634',3)
    if avatar=='alien':out+=path('M54 63Q69 60 73 76Q56 79 54 63ZM106 63Q91 60 87 76Q104 79 106 63Z','#344d3c','none')
    else:out+=portrait_eyes(avatar)
    out+=path('M71 95q9 2 18 0','none','#635440',1.6)
    if avatar=='astronaut':out=path('M38 60Q38 18 80 18Q122 18 122 60L118 103H42Z','#d6d2b8')+out+path('M45 52Q80 27 115 52V101H45Z','none','#698278',3)+rect(44,102,72,10,'#87978a')
    return out

def default_hair(avatar):
    from .cosmetic_art_more import COLORS,extra_hair
    if avatar in COLORS:return extra_hair(avatar)
    if avatar in SPECIES or avatar=='astronaut':return ''
    style={'explorer':'waves','strategist':'sidepart','mentor':'silver_crop','competitor':'shaved','curly':'curls','scout':'braids','captain':'sidepart','pilot':'bun'}[avatar]
    if style=='shaved':return path('M48 53Q47 28 80 28Q114 28 112 53L103 45Q80 39 56 45Z','#383b32')
    return hair(style)

def accessory_shape(kind,item):
    return {'accessory':headwear,'clothing':clothing,'hairstyle':hair,'face':beard,'eyewear':eyewear,'earrings':earrings}[kind](item)

def avatar_art(avatar,hat,cloth,face,hairstyle,lenses,ears,framing):
    avatar=valid('avatar',avatar);hat=valid('accessory',hat);cloth=valid('clothing',cloth)
    face=valid('face',face);hairstyle=valid('hairstyle',hairstyle);lenses=valid('eyewear',lenses);ears=valid('earrings',ears)
    # Species use a common eye/jaw rig. Wider heads receive their own headwear scale.
    scale=1.07 if avatar in ('alien','robot','dinosaur','crocodile','elephant','hippo','gorilla','croc_safari') else 1
    hat_transform=f'translate(80 40) scale({scale}) translate(-80 -40)'
    silhouette=circle(80,66,52,'#25312b','#988052',1)
    silhouette+=f'<g data-slot="clothing">{clothing(cloth)}</g>'+path('M66 97V114Q80 126 94 114V97Z',SPECIES.get(avatar,'#c79169'),'none')
    silhouette+=f'<g data-slot="head">{head(avatar)}</g>'
    silhouette+=f'<g data-slot="hair-front">{default_hair(avatar) if hairstyle=="none" else hair(hairstyle)}</g>'
    silhouette+=f'<g data-slot="face-accessory">{beard(face)}</g><g data-slot="eyewear">{eyewear(lenses)}</g><g data-slot="earrings">{earrings(ears)}</g>'
    silhouette+=f'<g data-slot="headwear" transform="{hat_transform}">{headwear(hat)}</g>'
    return silhouette
