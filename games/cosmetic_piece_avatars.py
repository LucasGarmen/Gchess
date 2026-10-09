"""Personified chess pieces aligned to the existing clothing/accessory rig."""
COLORS={'piece_pawn':'#c7b28e','piece_bishop':'#bcba96','piece_knight':'#b89772','piece_rook':'#9caaa1','piece_king':'#d4b66d','piece_queen':'#d5b690'}

def piece_head(avatar):
    if avatar not in COLORS:return None
    from .cosmetic_art import path,circle,rect
    from .cosmetic_portraits import portrait_finish,portrait_eyes
    lighting,fill=portrait_finish(avatar,COLORS[avatar])
    dark='#625a44';crest=''
    outline='M49 57Q49 33 80 33Q111 33 111 57L108 85Q102 106 80 110Q58 106 52 85Z'
    if avatar=='piece_pawn':
        outline='M49 61Q45 31 80 31Q115 31 111 61L106 84Q100 102 80 105Q60 102 54 84Z'
        crest=path('M58 100Q80 106 102 100L105 109H55Z',fill,dark)+path('M62 107h36','none','#e6d4ac',2)
    elif avatar=='piece_bishop':
        outline='M49 57Q52 39 66 29L80 13L94 29Q108 39 111 57L106 86Q101 105 80 110Q59 105 54 86Z'
        crest=path('M85 24L72 44','none',dark,5)+circle(80,12,4,'#ddd0a6')
    elif avatar=='piece_knight':
        outline='M49 55L50 31L62 39L77 28L98 35L111 55L114 85Q106 108 80 111Q54 108 50 86Z'
        crest=path('M52 54L40 40L43 77L51 89Z','#66533f')+path('M53 38l2-16 12 16M96 38l13-16 1 23Z',fill,dark)
    elif avatar=='piece_rook':
        outline='M47 52V28H61V39H73V26H87V39H99V28H113V52L108 90L99 108H61L52 90Z'
        crest=path('M49 49h62M58 100h44','none','#d4d4b9',2)+path('M50 54h60','none',dark,2)
    elif avatar=='piece_king':
        crest=path('M74 15V8H86V15H94V23H86V34H74V23H66V15Z','#d6b773',dark)+path('M48 42L53 30L67 36L80 30L93 36L107 30L112 42L108 52H52Z',fill,dark)+circle(80,42,3,'#8a5546')
    elif avatar=='piece_queen':
        outline='M50 57Q49 36 80 36Q111 36 110 57L105 87Q100 104 80 112Q60 104 55 87Z'
        crest=path('M48 43L44 23L61 34L67 18L80 32L93 18L99 34L116 23L112 43L106 52H54Z','#d2b36d',dark)+''.join(circle(x,y,3,'#ecd4a0',dark,1) for x,y in [(44,23),(67,18),(93,18),(116,23)])+circle(80,44,3,'#9b685c')
    eyes=portrait_eyes('horse' if avatar=='piece_knight' else {'piece_pawn':'explorer','piece_bishop':'mentor','piece_rook':'captain','piece_king':'strategist','piece_queen':'pilot'}[avatar])
    face=lighting+path(outline,fill,dark,1.3)+path('M54 56Q57 42 70 39','none','#eee0bc',1.8)+eyes
    if avatar=='piece_knight':
        face+=path('M59 85Q80 78 103 87L101 100Q80 112 59 100Z','#ddc69f',dark,1)+circle(70,90,1.7,dark)+circle(93,90,1.7,dark)+path('M70 100q10 3 20-1','none',dark,1.5)
    else:
        face+=path('M80 76l-3 10h6','none','#8b7954',1.3)+path('M70 96q10 5 20-1','none',dark,1.5)
    return face+crest
