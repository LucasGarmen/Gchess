"""Individual portrait proportions; accessory anchors remain at x65/95, y72."""
HUMANS={
 'explorer':('#dbab82','M49 52Q50 30 80 31Q111 32 111 54L106 87Q100 106 80 110Q60 106 54 87Z','M77 74l-3 12h9','M69 95Q80 103 92 94'),
 'strategist':('#b78059','M50 49Q55 31 80 32Q105 31 110 49L109 86L97 105L80 112L63 105L51 86Z','M81 73l-5 13 8 1','M71 97l19-2'),
 'mentor':('#c7a080','M48 53Q49 32 80 33Q111 32 112 53L109 91L97 104L80 108L63 104L51 91Z','M79 74l-2 13q5 3 9 0','M70 96q10 4 20 0'),
 'competitor':('#a77352','M47 54Q49 29 80 30Q111 29 113 54L110 89L97 107H63L50 89Z','M80 74v11l6 2','M69 97h22'),
 'curly':('#e6b994','M50 55Q50 31 80 32Q110 31 110 55L108 85Q106 106 80 111Q54 106 52 85Z','M78 75l-2 10q4 3 8 0','M69 95Q80 103 91 95'),
 'scout':('#c88f6c','M51 53Q50 30 80 31Q110 30 109 53L105 87L93 103L80 110L67 103L55 87Z','M80 74l-3 13h6','M72 96q8 5 17-1'),
 'captain':('#986747','M48 51Q49 30 80 30Q111 30 112 51L109 88L99 106H61L51 88Z','M78 73l-3 14h11','M69 96q11-2 22 0'),
 'pilot':('#e4b598','M50 53Q51 31 80 31Q109 31 110 53L105 87Q99 104 80 111Q61 104 55 87Z','M80 74l-2 12h6','M72 95q9 5 17-2'),
 'astronaut':('#b99170','M49 55Q49 32 80 32Q111 32 111 55L108 85L96 104L80 110L64 104L52 85Z','M80 75l-3 11h6','M71 97q9 2 18-1'),
 'messi':('#d0a17d','M49 54Q48 31 80 32Q111 31 111 54L109 83L101 98L91 108H69L59 98L51 83Z','M79 74l-4 12q5 4 10 0','M71 96q9 3 18-1'),
}

# Rounded, tapered, square and broad profiles give creatures their own silhouette.
OUTLINES={
 'elephant':'M47 53Q45 31 80 31Q115 31 113 53L112 84Q108 108 80 111Q52 108 48 84Z',
 'lion':'M49 55Q48 33 80 33Q112 33 111 55L107 87L96 103L80 110L64 103L53 87Z',
 'croc_safari':'M47 53Q49 35 80 35Q111 35 113 53L114 91L104 107H56L46 91Z',
 'duck':'M48 55Q48 29 80 29Q112 29 112 55L110 85Q106 105 80 108Q54 105 50 85Z',
 'giraffe':'M53 51Q53 31 80 32Q107 31 107 51L103 89L93 109H67L57 89Z',
 'dog':'M49 53Q49 30 80 31Q111 30 111 53L107 85Q105 106 80 111Q55 106 53 85Z',
 'cat':'M51 54Q54 35 80 34Q106 35 109 54L106 88L94 103L80 110L66 103L54 88Z',
 'gorilla':'M44 55Q44 29 80 29Q116 29 116 55L113 89L103 108H57L47 89Z',
 'rabbit':'M53 52Q51 30 80 30Q109 30 107 52L105 84Q101 104 80 111Q59 104 55 84Z',
 'raccoon':'M49 53Q49 32 80 32Q111 32 111 53L108 86L96 103L80 111L64 103L52 86Z',
 'penguin':'M50 53Q49 31 80 31Q111 31 110 53L108 85Q100 107 80 111Q60 107 52 85Z',
 'owl':'M47 52Q49 31 80 31Q111 31 113 52L107 88L95 104L80 113L65 104L53 88Z',
 'hippo':'M44 57Q43 33 80 33Q117 33 116 57L115 90Q108 110 80 110Q52 110 45 90Z',
 'rhino':'M46 54Q45 31 80 31Q115 31 114 54L110 88L100 107H60L50 88Z',
 'zebra':'M53 52Q52 31 80 31Q108 31 107 52L104 86L94 109H66L56 86Z',
 'horse':'M52 51Q52 31 80 31Q108 31 108 51L105 86L96 112H64L55 86Z',
 'octopus':'M45 53Q42 23 80 24Q118 23 115 53L108 88Q101 106 80 109Q59 106 52 88Z',
 'eagle':'M51 54Q51 32 80 31Q109 32 109 54L105 86L94 103L80 111L66 103L55 86Z',
 'skeleton':'M48 52Q46 28 80 28Q114 28 112 52L111 83L99 91L97 108H63L61 91L49 83Z',
 'bear':'M45 55Q44 30 80 30Q116 30 115 55L110 88Q105 108 80 112Q55 108 50 88Z',
 'tiger':'M48 54Q49 31 80 31Q111 31 112 54L108 88L98 103L80 111L62 103L52 88Z',
 'crocodile':'M47 54Q47 35 80 35Q113 35 113 54L113 91L104 107H56L47 91Z',
 'dinosaur':'M47 55Q46 31 80 30Q114 31 113 55L109 91L98 107H62L51 91Z',
 'shark':'M50 54Q48 32 80 29Q112 32 110 54L112 87L98 106L80 114L62 106L48 87Z',
 'fox':'M49 54Q50 33 80 32Q110 33 111 54L103 86L93 99L80 112L67 99L57 86Z',
 'wolf':'M48 53Q49 30 80 31Q111 30 112 53L106 89L94 105L80 112L66 105L54 89Z',
 'panda':'M46 56Q45 31 80 31Q115 31 114 56L110 88Q104 110 80 112Q56 110 50 88Z',
 'dragon':'M47 52Q50 32 80 30Q110 32 113 52L108 86L96 105L80 113L64 105L52 86Z',
}

EYES={
 'explorer':(5,0,'#738650'),'strategist':(3,-2,'#7d683c'),'mentor':(3,1,'#89928a'),
 'competitor':(3,-3,'#695337'),'curly':(6,1,'#8b623d'),'scout':(4,-1,'#70866b'),
 'captain':(4,-2,'#5b4937'),'pilot':(5,2,'#7c7355'),'astronaut':(4,0,'#738879'),
 'messi':(4,-2,'#795d3d'),'elephant':(4,2,'#887c55'),'lion':(4,-2,'#bca15c'),
 'croc_safari':(3,-3,'#b7ac55'),'duck':(6,2,'#677347'),'giraffe':(5,1,'#87643d'),
 'dog':(6,1,'#a67a43'),'cat':(4,-2,'#9caa61'),'gorilla':(3,-3,'#886a45'),
 'rabbit':(6,2,'#976e64'),'raccoon':(5,-1,'#aa9a65'),'penguin':(5,1,'#657667'),
 'owl':(7,0,'#c3a45e'),'hippo':(4,2,'#8d6c81'),'rhino':(3,-1,'#8f825f'),
 'zebra':(4,0,'#79613e'),'horse':(5,1,'#986c40'),'octopus':(6,2,'#a76968'),
 'eagle':(3,-3,'#c6a35c'),'bear':(4,1,'#90734a'),'tiger':(4,-3,'#b79b50'),
 'crocodile':(3,-2,'#b8a756'),'dinosaur':(5,0,'#b8a65c'),'shark':(3,-3,'#638b94'),
 'fox':(4,-1,'#b58c50'),'wolf':(3,-2,'#a49c63'),'panda':(5,2,'#80755c'),
 'dragon':(3,-3,'#c29b63'),
}

def portrait_finish(avatar, color):
    # Soft sculpted lighting, shared consistently by the catalog and equipped art.
    def shade(factor):
        rgb=[int(color[i:i+2],16) for i in (1,3,5)]
        return '#'+''.join(f'{min(255,int(v*factor)):02x}' for v in rgb)
    key='portrait-'+avatar
    defs=f'<defs><linearGradient id="{key}" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="{shade(1.17)}"/><stop offset=".48" stop-color="{color}"/><stop offset="1" stop-color="{shade(.82)}"/></linearGradient></defs>'
    return defs,f'url(#{key})'

def portrait_eyes(avatar):
    from .cosmetic_art import path,circle
    height,tilt,iris=EYES[avatar]
    # Eyes retain the accessory anchors while character has a distinct gaze.
    height=max(3,height); tilt=tilt*.35
    out=''
    for x,sign in ((65,1),(95,-1)):
        out+=path(f'M{x-7} {72+tilt*sign}Q{x} {70-height*.65} {x+7} {72-tilt*sign}Q{x} {74+height*.55} {x-7} {72+tilt*sign}Z','#fff0d8','#65513c',.8)
        out+=circle(x,72,3.4,iris)+circle(x,72,1.8,'#242f2b')+circle(x-1.1,70.9,.95,'#fff9ea')
        out+=path(f'M{x-7} {63+tilt*sign}Q{x} {60+abs(tilt)} {x+7} {63-tilt*sign}','none','#514333',2.1)
    return out

def human_head(avatar):
    from .cosmetic_art import path,circle,rect
    if avatar not in HUMANS:return None
    skin,outline,nose,mouth=HUMANS[avatar]
    out=path('M48 65Q40 61 43 76L49 83M112 65Q120 61 117 76L111 83Z',skin,'#8e7051',1)
    lighting,fill=portrait_finish(avatar,skin)
    out=lighting+out+path(outline,fill,'#72553f',1.1)
    out+=path('M53 57Q53 39 74 37','none','#f5d5ae',2)+path('M107 62Q108 83 99 94','none','#9d7252',1.2)
    out+=path('M55 82q6-3 11 0M94 82q6-3 11 0','none','#d59472',2.4)
    out+=path('M73 103q7 3 14 0','none','#ac7658',1)
    out+=portrait_eyes(avatar)+path(nose,'none','#966c51',1.5)+path(mouth,'none','#815040',1.5)+path('M77 89q3 2 6 0','none','#af7656',.9)
    if avatar=='pilot':out+=path('M58 71l-3-2M102 71l3-2','none','#514333',1.4)+path('M75 97q5 2 10-1','none','#a06b61',2)
    if avatar=='mentor':out+=path('M56 80l12 2M92 82l12-2M70 91l-5 9M90 91l5 9','none','#9c795a',1)+path('M66 55l10-1M84 54l10 1','none','#b38d6b',1)
    if avatar=='curly':out+=circle(58,87,2,'#c7886e')+circle(102,87,2,'#c7886e')
    if avatar=='scout':out+=''.join(circle(x,y,.8,'#996a4c') for x,y in [(57,84),(62,86),(66,83),(94,83),(98,86),(103,84)])
    if avatar=='messi':out+=path('M55 85L60 99L70 105H90L100 99L105 85L103 101L92 111H68L57 101Z','#63503d','none')+path('M72 91q8-4 16 0','none','#63503d',2)
    if avatar=='astronaut':out=path('M38 60Q38 18 80 18Q122 18 122 60L118 103H42Z','#d6d2b8')+out+path('M45 52Q80 27 115 52V101H45Z','none','#698278',3)+rect(44,102,72,10,'#87978a')
    return out
