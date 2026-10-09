"""Twenty additional original portraits on the shared Gchess accessory rig."""
from .cosmetic_art import path, circle, rect

COLORS={'elephant':'#a8a494','lion':'#c79a53','croc_safari':'#526f47','duck':'#e9d9a4','giraffe':'#cbaa68','dog':'#b18c66','messi':'#d4a57d','cat':'#9c9982','gorilla':'#69766c','rabbit':'#c5c6b3','raccoon':'#979f92','penguin':'#d9ddc7','owl':'#a89a70','hippo':'#a090a0','rhino':'#979e8f','zebra':'#ded9c5','horse':'#9c7451','octopus':'#ac7e82','eagle':'#d8d5bd','skeleton':'#e0d6b7'}

def eyes():
    return path('M56 63l16-2M88 61l16 2','none','#414837',2)+circle(65,72,2.4,'#283b30')+circle(95,72,2.4,'#283b30')

def face_base(c,outline=None):
    return path(outline or 'M49 55Q49 31 80 32Q111 31 111 55L108 85L98 102L80 109L62 102L52 85Z',c,'#756b4a')

def muzzle(c):
    return path('M59 87Q61 78 80 79Q99 78 101 87L94 102H66Z',c,'none')+path('M74 86H86L80 92Z','#3d4637','none')+path('M72 96q8 3 16 0','none','#645a42',1.5)

def extra_head(avatar):
    if avatar not in COLORS:return None
    c=COLORS[avatar];back='';front='';snout=''
    if avatar=='elephant':
        back=path('M53 49Q25 34 33 75Q39 91 55 87M107 49Q135 34 127 75Q121 91 105 87Z',c)
        front=path('M71 81Q79 74 89 81L89 105Q98 118 100 103','none','#848878',12)+path('M67 87l-3 17M94 87l3 17','none','#e6dbb6',3)
    elif avatar=='lion':
        back=path('M80 16L96 23L111 22L116 36L129 43L123 59L130 73L118 89L111 111L95 111L80 123L65 111L49 111L42 89L30 73L37 58L31 42L44 36L49 22L64 23Z','#86613d')
        back+=circle(52,39,9,c)+circle(108,39,9,c);snout=muzzle('#e2c78a')
    elif avatar=='croc_safari':
        back=path('M56 39L64 25L75 34L85 24L95 34L106 28L111 44Z',c)
        snout=path('M54 82Q80 72 106 82L108 98L98 104H62L52 98Z','#879766')+path('M59 93h42','none','#354833',2)
        front=path('M64 94l3 5 3-5M78 94l3 5 3-5M92 94l3 5 3-5Z','#e8dfbc','none')
    elif avatar=='duck':
        back=path('M62 36L68 24L79 34L87 25L97 38Z','#e9d9a4')
        snout=path('M59 86Q80 73 101 86L104 95Q80 107 56 95Z','#be9653')+path('M61 92h38','none','#826a39',1.5)
    elif avatar=='giraffe':
        back=path('M50 50L40 34L58 36M110 50L120 34L102 36Z',c)+path('M64 39V22M96 39V22','none','#a88650',6)+circle(64,21,5,'#80663c')+circle(96,21,5,'#80663c')
        front=''.join(path(f'M{x} {y}l5-2 4 5-6 4-4-3Z','#9b7544','none') for x,y in [(57,47),(77,36),(94,47),(53,81),(97,81)])
        snout=muzzle('#d9c58e')
    elif avatar=='dog':
        back=path('M51 43Q27 38 34 83L46 94L55 54M109 43Q133 38 126 83L114 94L105 54Z','#755c42')
        snout=muzzle('#dfc797');front=path('M86 37Q111 34 109 64Q90 64 86 37Z','#806342','none')
    elif avatar=='messi':
        snout=path('M53 81Q57 96 69 97L80 101L91 97Q103 96 107 81L103 103L92 110H68L57 103Z','#65543c','none')+path('M70 89Q80 85 90 89','none','#65543c',3)
        front=path('M73 96q7 2 14 0','none','#bd976e',1.5)
    elif avatar in ('cat','zebra','horse'):
        back=path('M47 53L43 25L63 40M113 53L117 25L97 40Z',c)
        snout=muzzle('#ded0a7' if avatar!='zebra' else '#777d6d')
        if avatar=='cat':front=path('M53 88l-10-3M54 94l-11 1M107 88l10-3M106 94l11 1','none','#d2c6a3',1.5)
        elif avatar=='zebra':front=path('M56 45l12 9M104 45l-12 9M79 35v23M51 81l11 4M109 81l-11 4','none','#545d4e',4)
        else:front=path('M76 36h8l3 37-7 7-7-7Z','#dbca9a','none')
    elif avatar=='gorilla':
        back=circle(47,65,9,'#596459')+circle(113,65,9,'#596459')
        snout=path('M58 82Q61 74 80 75Q99 74 102 82L98 102H62Z','#91977f')+path('M72 86h16M70 95h20','none','#414d3c',3)
        front=path('M53 61Q66 53 76 62M84 62Q95 53 107 61','none','#424f3f',4)
    elif avatar=='rabbit':
        back=path('M55 43Q40 7 53 9Q65 12 68 40M105 43Q120 7 107 9Q95 12 92 40Z',c)+path('M54 17l7 19M106 17l-7 19','none','#b39288',3)
        snout=muzzle('#e2ddc3');front=rect(74,94,6,7,'#f1e9d0')+rect(81,94,6,7,'#f1e9d0')
    elif avatar=='raccoon':
        back=circle(52,39,10,c)+circle(108,39,10,c)
        front=path('M52 62Q80 51 108 62L105 80Q80 69 55 80Z','#4b5948','none');snout=muzzle('#ddd7b9')
    elif avatar=='penguin':
        back=path('M43 54Q43 24 80 25Q117 24 117 54L110 94L80 112L50 94Z','#46594d')
        snout=path('M67 87L80 78L93 87L80 97Z','#bf9b4f');front=path('M48 42Q60 31 70 37M112 42Q100 31 90 37','none','#46594d',7)
    elif avatar=='owl':
        back=path('M47 51L40 24L67 36M113 51L120 24L93 36Z',c)
        front=circle(65,70,14,'#dbcca2','#7c7250')+circle(95,70,14,'#dbcca2','#7c7250')
        snout=path('M73 86L80 79L87 86L80 95Z','#9b8550')
    elif avatar=='hippo':
        back=circle(52,40,9,c)+circle(108,40,9,c)
        snout=path('M54 87Q54 76 80 77Q106 76 106 87V102H54Z','#b4a0a8')+circle(67,87,2,'#786c70')+circle(93,87,2,'#786c70')+path('M61 98h38','none','#7b6c70',1.5)
    elif avatar=='rhino':
        back=path('M50 48L43 32L64 39M110 48L117 32L96 39Z',c)
        snout=muzzle('#aeb1a0');front=path('M73 87L82 66L87 87Z','#d3c8a5')
    elif avatar=='octopus':
        back=''.join(path(f'M{x} 81Q{x-17} 106 {x-8} 116Q{x+3} 117 {x+2} 107','none','#ac7e82',8) for x in (49,62,95,111))
        front=path('M72 90Q80 86 88 90L85 97H75Z','#7b5c62','none')
    elif avatar=='eagle':
        back=path('M50 50L52 30L67 34L80 25L95 34L108 30L110 50Z',c)
        snout=path('M70 83Q79 74 90 83L93 93L80 101L78 91L68 89Z','#bca05e')
        front=path('M56 62l17 3M87 65l17-3','none','#656b53',3)
    elif avatar=='skeleton':
        front=path('M52 63Q65 54 73 65L70 80H57ZM87 65Q95 54 108 63L103 80H90Z','#45513e','none')+path('M80 82l-5 8h10Z','#45513e','none')
        snout=rect(63,95,34,10,'#d8cba8','#85795c')+path('M69 96v8M76 96v8M83 96v8M90 96v8','none','#85795c',1)
    from .cosmetic_portraits import OUTLINES,portrait_eyes,portrait_finish
    lighting,fill=portrait_finish(avatar,c)
    result=lighting+back+face_base(fill,OUTLINES.get(avatar))+path('M54 55Q55 39 71 37','none','#e5d9b0',1.5)+snout
    if avatar!='elephant':result+=front
    if avatar!='skeleton':result+=portrait_eyes(avatar)
    if avatar=='elephant':result+=front
    return result

def extra_hair(avatar):
    if avatar=='messi':return path('M48 63L47 45Q51 29 81 30Q108 29 113 48L108 63L103 44Q82 54 58 44L55 64Z','#504632')+path('M58 38Q80 34 100 38','none','#847354',1.5)
    if avatar in ('zebra','horse'):return path('M72 37L71 20L80 27L88 18L91 37Z','#514b39')
    return ''
