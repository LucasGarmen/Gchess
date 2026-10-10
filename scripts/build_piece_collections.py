"""Build original, sharp SVG chess collections. Existing catalog keys stay stable."""
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]/'games/static/games'
# Theme, light material, dark material, light trim, dark trim.
SETS={
 'club':('carved','#efe1bf','#59432c','#a17e46','#dbc38d'),
 'modern':('minimal','#e7e7d7','#293b35','#8fa99a','#a9c5b5'),
 'tournament':('regal','#f1dfb7','#403b32','#a37c37','#d7b365'),
 'gold':('war','#f0d399','#414942','#9e6d27','#d7b36d'),
 'silver':('robot','#dae4df','#344346','#657f83','#8de2d1'),
 'copper':('clockwork','#e4bb87','#72543e','#865b31','#f0bd75'),
 'obsidian':('skeleton','#e9ddbf','#514d46','#847561','#ded0a8'),
 'ivory':('porcelain','#f2e9d5','#465b65','#638096','#e0d2ad'),
 'jade':('bamboo','#c8d29b','#355b41','#688741','#a5c96e'),
 'ruby':('dragon','#ead0b1','#792f30','#a64933','#efad61'),
 'sapphire':('sea','#d6e7d9','#245574','#4f8c95','#9edacb'),
 'amethyst':('wizard','#e2d5e6','#51446d','#9773a3','#d0b0e5'),
 'lava':('volcano','#ead1a5','#3c3431','#a35827','#ff993f'),
 'ice':('crystal','#e5f3e8','#427b8f','#679ca2','#b3edee'),
 'rose':('garden','#efe0b7','#765048','#a76a61','#ddb39a'),
 'bronze':('gladiator','#dfc399','#575843','#896b36','#d5b071'),
 'pearl':('ghost','#e5e9db','#49616b','#8ba3a0','#c2d9c9'),
 'midnight':('pirate','#e2d4ad','#3c4348','#8a774e','#d8b671'),
 'sandstone':('desert','#e9c795','#6b4933','#a6783e','#e7bf79'),
}
def path(d,fill='url(#material)',stroke=None,width=2):
 return f'<path d="{d}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{width}"' if stroke else '')+'/>'
def circle(x,y,r,fill):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'
def skull(y,ink):
 return path(f'M34 {y+12}Q32 {y-8} 50 {y-9}Q68 {y-8}66 {y+12}L60 {y+17}V{y+24}H40V{y+17}Z')+circle(42,y+5,4,ink)+circle(58,y+5,4,ink)+path(f'M50 {y+10}l-3 5h6Z',ink)+path(f'M44 {y+18}v6m6-6v6m6-6v6','none',ink,1.5)
def crown(piece,trim):
 if piece=='king':return path('M46 8h8v8h8v7h-8v9h-8v-9h-8v-7h8Z',trim)
 if piece=='queen':return path('M30 20l8 15 12-18 12 18 8-15-6 25H36Z',trim)+''.join(circle(x,y,2.8,trim) for x,y in [(30,20),(50,17),(70,20)])
 if piece=='bishop':return path('M50 14Q69 33 61 43H39Q31 33 50 14Z')+path('M51 21l-7 13','none',trim,3)
 if piece=='rook':return path('M29 19h9v9h8v-9h8v9h8v-9h9v23H29Z')
 return ''
def horse(theme,trim,ink):
 # A long muzzle, ear and mane remain legible across all fantasy collections.
 out=path('M29 73V49L35 32L44 21L47 10L54 19L63 26L74 43L72 54L63 58L53 49L51 62L65 73Z')
 out+=path('M36 32L28 44L34 44L27 55L34 54L28 65L36 62','none',trim,3)+circle(57,32,2.7,ink)+path('M65 44l5 1','none',ink,2)
 if theme in ('war','gladiator'):out+=path('M43 21L56 22L68 38L57 40L47 29Z',trim)+path('M35 53l13 6-6 10Z',trim)
 if theme=='skeleton':out+=path('M37 46l10-3m-9 10 8-2m-8 10 8-2','none',ink,2.5)+path('M59 48l3 6m3-5 2 5','none',ink,1.4)
 if theme=='dragon':out+=path('M34 36L20 22L24 45L17 60L34 54Z',trim)+path('M47 13L39 7L40 24Z',trim)
 if theme=='sea':out+=path('M30 69q-16 5-8 13q6 4 10-3M62 70q17 0 15 10q-2 6-7 1','none',trim,4)
 if theme in ('robot','clockwork'):out+=path('M45 26h15v10H45Z',trim)+path('M33 57h14v11H33Z',trim)+circle(52,31,2,ink)
 return out

def body(theme,piece,trim,ink):
 pawn=piece=='pawn';top=39 if pawn else 41
 if theme=='skeleton':
  out=skull(34 if pawn else 44,ink)
  if not pawn:out=crown(piece,trim)+out
  out+=path('M46 61v14m8-14v14M35 65l30 10m-30 0 30-10','none',trim,5)
  return out
 if theme=='robot':
  out=path('M34 35l7-9h18l7 9v25H34Z')+path('M38 38h24v12H38Z',ink)+path('M41 43h5m8 0h5','none',trim,3)+path('M39 60h22l8 17H31Z')
  return (crown(piece,trim) if not pawn else path('M49 26V17','none',trim,2)+circle(49,15,3,trim))+out
 if theme=='ghost':
  out=path('M28 75Q35 64 34 48Q33 29 50 29Q67 29 66 48Q65 64 72 75L62 71L56 77L50 73L43 77L36 71Z')+circle(43,46,3,ink)+circle(57,46,3,ink)
  return (crown(piece,trim) if not pawn else '')+out
 if theme in ('crystal','volcano'):
  out=path('M50 25L66 43L61 63L72 77H28L39 63L34 43Z')+path('M50 25L47 62L28 77M50 25L54 62L72 77M34 43L47 62H54L66 43','none',trim,2.5)
  if theme=='volcano':out+=path('M49 33l5 12-8 9 10 10-4 12','none',trim,3)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='wizard':
  out=path('M35 47L27 74Q50 84 73 74L65 47Z')+path('M50 12L67 42L75 46Q50 55 25 46L34 42Z')+path('M43 58l3 5 6-1-4 4 1 6-5-3-5 3 1-6-4-4 6 1Z',trim)
  return (crown(piece,trim) if piece in ('king','queen','rook','bishop') else '')+out
 if theme=='war' or theme=='gladiator':
  out=path('M34 42Q34 27 50 27Q66 27 66 42V52H34Z')+path('M38 39h24v8H38Z',ink)+path('M39 53L29 74L50 80L71 74L61 53Z')+path('M50 57l11 5-3 9-8 6-8-6-3-9Z',trim)+path('M50 61v10','none',ink,2)
  if theme=='gladiator':out+=path('M35 32Q50 12 65 32','none',trim,6)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='sea':
  out=path('M33 46Q28 25 50 27Q72 25 67 46L60 62H40Z')+path('M40 60Q22 67 26 76q5 7 9-1M48 61Q38 84 48 81M56 61q20 8 16 17q-5 4-9-3','none',trim,5)+circle(43,43,2,ink)+circle(57,43,2,ink)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='dragon':
  out=path('M35 73L37 44L30 30L43 35L50 22L57 35L70 30L63 44L65 73Z')+path('M36 48L20 42L26 65L36 60M64 48L80 42L74 65L64 60Z',trim)+path('M43 44l4 2m6 0 4-2','none',ink,2.5)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='pirate':
  out=path('M35 39Q35 28 50 28Q65 28 65 39V54Q50 65 35 54Z')+path('M24 35L32 23L43 28L50 19L57 28L68 23L76 35Q50 47 24 35Z',ink)+path('M37 49L63 40','none',trim,3)+circle(43,45,3,ink)+path('M37 63l26 13m-26 0 26-13','none',trim,4)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='desert':
  out=path('M30 76L38 47L50 25L62 47L70 76Z')+path('M38 47h24M34 62h32','none',trim,3)+path('M44 40h12v10H44Z',ink)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='garden':
  out=path('M35 74Q44 59 41 43H59Q56 59 65 74Z')+''.join(circle(x,y,8,'url(#material)') for x,y in [(40,33),(50,27),(60,33),(56,44),(44,44)])+circle(50,36,5,trim)+path('M42 64Q25 54 27 65Q35 75 42 64M58 66Q76 52 72 68Q65 77 58 66Z',trim)
  return (crown(piece,trim) if not pawn else '')+out
 if theme=='bamboo':
  out=path('M38 30Q50 23 62 30L60 73H40Z')+path('M39 41h22M40 56h20M40 70h20','none',trim,3)+path('M41 44Q23 34 28 52Q37 56 41 44M60 54Q76 40 75 58Q68 65 60 54Z',trim)
  return (crown(piece,trim) if not pawn else circle(50,25,8,'url(#material)'))+out
 if theme=='clockwork':
  out=path('M36 44Q36 29 50 29Q64 29 64 44L61 60L68 76H32L39 60Z')+circle(50,48,12,trim)+circle(50,48,7,ink)+path('M50 40v8l5 3','none',trim,2)+path('M33 50h-8m42 0h8','none',trim,5)
  return (crown(piece,trim) if not pawn else circle(50,26,5,trim))+out
 if theme=='regal':
  out=path('M34 44Q50 51 66 44L61 58Q59 67 72 76H28Q41 67 39 58Z')+path('M36 48h28M34 72h32','none',trim,2)+path('M50 55l5 6-5 6-5-6Z',trim)
  return (crown(piece,trim) if not pawn else circle(50,29,13,'url(#material)'))+out
 # Three quieter collections also have their own silhouettes and bases.
 if theme=='minimal':
  out=path('M38 43h24v31H38Z')
  return (crown(piece,trim) if not pawn else circle(50,30,12,'url(#material)'))+out
 if theme=='porcelain':
  out=path('M37 43Q47 59 28 75Q50 82 72 75Q53 59 63 43Z')+path('M39 62q11-10 22 0m-17 3 6-4 6 4','none',trim,2)
  return (crown(piece,trim) if not pawn else circle(50,31,13,'url(#material)'))+out
 out=path('M37 44H63L59 61L70 76H30L41 61Z')+path('M41 49v12m6-12v15m6-15v15m6-15v12','none',trim,1.5)
 return (crown(piece,trim) if not pawn else circle(50,30,12,'url(#material)'))+out

def build(style,theme,piece,color,light,dark,lt,dt):
 fill=light if color=='white' else dark;trim=lt if color=='white' else dt;ink='#342c22' if color=='white' else '#ecdfbb'
 defs=f'<defs><linearGradient id="material" x2="1" y2=".18"><stop stop-color="{trim}"/><stop offset=".23" stop-color="{fill}"/><stop offset=".7" stop-color="{fill}"/><stop offset="1" stop-color="{trim}"/></linearGradient></defs>'
 shape=horse(theme,trim,ink) if piece=='horse' else body(theme,piece,trim,ink)
 # Bases visibly vary with the collection, not just its paint.
 if theme in ('robot','minimal','desert','crystal','volcano'):base=path('M30 77H70L79 88H21Z')+path('M29 83h42','none',trim,2)
 elif theme in ('skeleton','pirate'):base=path('M29 78H71L75 87H25Z')+path('M32 82l36 4m-36 0 36-4','none',trim,2)
 elif theme in ('sea','ghost','garden'):base=path('M25 78Q50 72 75 78L77 86Q50 93 23 86Z')+path('M29 84q21 5 42 0','none',trim,2)
 else:base=path('M29 77H71V82H76V88H24V82H29Z')+path('M30 84h40','none',trim,2)
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><title>{escape(theme+" "+piece+" "+color)}</title>{defs}<ellipse cx="50" cy="91" rx="29" ry="2" fill="#14130f" opacity=".15"/><g stroke="{ink}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round">{shape}{base}</g></svg>'
if __name__=='__main__':
 for style,(theme,light,dark,lt,dt) in SETS.items():
  folder=ROOT/f'pieces-{style}';folder.mkdir(exist_ok=True)
  for color in ('white','black'):
   for piece in ('king','queen','rook','bishop','horse','pawn'):
    (folder/f'{piece}_{color}.svg').write_text(build(style,theme,piece,color,light,dark,lt,dt),encoding='utf-8')
 print('Built 19 distinct collections, 228 SVG pieces; rustic collection preserved.')
