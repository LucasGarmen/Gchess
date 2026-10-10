"""Server-owned free collection. No payments, rewards or VIP entitlements enabled."""
FREE_ITEMS={'avatar': ['explorer', 'strategist', 'mentor', 'competitor', 'curly', 'scout', 'captain', 'pilot', 'dinosaur', 'alien', 'bear', 'tiger', 'robot', 'crocodile', 'shark', 'fox', 'wolf', 'panda', 'astronaut', 'dragon', 'elephant', 'lion', 'croc_safari', 'duck', 'giraffe', 'dog', 'messi', 'cat', 'gorilla', 'rabbit', 'raccoon', 'penguin', 'owl', 'hippo', 'rhino', 'zebra', 'horse', 'octopus', 'eagle', 'skeleton'], 'board': ['rustic', 'walnut', 'slate', 'sand', 'ocean', 'wine', 'gold', 'lava', 'emerald', 'midnight', 'ice', 'copper', 'amethyst', 'rose', 'olive', 'marble', 'coffee', 'royal', 'silver', 'obsidian'], 'pieces': ['rustic', 'club', 'modern', 'tournament', 'gold', 'silver', 'copper', 'obsidian', 'ivory', 'jade', 'ruby', 'sapphire', 'amethyst', 'lava', 'ice', 'rose', 'bronze', 'pearl', 'midnight', 'sandstone'], 'accessory': ['none', 'cap', 'beret', 'beanie', 'visor', 'fedora', 'cowboy', 'bucket', 'top_hat', 'crown', 'pirate', 'straw', 'turban', 'wizard', 'helmet', 'sailor', 'flat_cap', 'earflap', 'laurel', 'chef'], 'clothing': ['club', 'ivory', 'forest', 'terracotta', 'hoodie', 'denim', 'leather', 'tuxedo', 'jersey', 'sweater', 'bomber', 'varsity', 'kimono', 'armor', 'cape', 'space_suit', 'striped', 'hawaiian', 'vest', 'puffer'], 'hairstyle': ['none', 'dreads', 'mohawk', 'afro', 'braids', 'bun', 'ponytail', 'spikes', 'waves', 'curls', 'sidepart', 'silver_crop', 'blue_mohawk', 'pink_bob', 'green_spikes', 'red_braids', 'blond_quiff', 'purple_dreads', 'punk', 'shaved'], 'face': ['none', 'moustache', 'stubble', 'goatee', 'full_beard', 'long_beard', 'handlebar', 'braided_beard', 'silver_beard'], 'eyewear': ['none', 'glasses', 'round', 'aviator', 'square', 'sunglasses', 'sport', 'monocle', 'visor_lens'], 'earrings': ['none', 'gold_hoops', 'silver_hoops', 'studs', 'diamond', 'chain', 'black_plugs']}
# Ordered preview collection: simple pieces first, royal pieces at the end.
for piece,before in [('piece_pawn','strategist'),('piece_bishop','robot'),('piece_knight','lion'),('piece_rook','gorilla'),('piece_king',None),('piece_queen',None)]:
    FREE_ITEMS['avatar'].insert(FREE_ITEMS['avatar'].index(before) if before else len(FREE_ITEMS['avatar']),piece)
FREE_ITEMS['avatar'].remove('pilot')
FREE_ITEMS['avatar'].insert(3,'pilot')
# Additional approved western characters; royal pieces stay last.
FREE_ITEMS['avatar'][-2:-2]=['bull','raven']
DEFAULTS=dict(avatar='explorer',board='rustic',pieces='rustic',accessory='none',clothing='club',hairstyle='none',face='none',eyewear='none',earrings='none')
CHOICES={kind:[(item,item.title()) for item in items] for kind,items in FREE_ITEMS.items()}

# Catalog previews stay visible; only the starter selection is usable for now.
AVAILABLE_ITEMS={kind:(default,) for kind,default in DEFAULTS.items()}
AVAILABLE_ITEMS['avatar']=tuple(FREE_ITEMS['avatar'][:4])
AVAILABLE_ITEMS['face']=('none','moustache')

# The development server exposes the whole collection for local try-ons.
# Production workers retain the starter entitlements above.
import sys
if 'runserver' in sys.argv:
    AVAILABLE_ITEMS={kind:tuple(items) for kind,items in FREE_ITEMS.items()}
AVATAR_ACCESSORY_SLOTS=('accessory','face','hairstyle','eyewear','earrings')
SHOP_KINDS=('avatar','board','pieces','clothing')
# Accessories have been retired, including previously equipped selections.
for slot in AVATAR_ACCESSORY_SLOTS:
    AVAILABLE_ITEMS[slot]=('none',)

def usable_loadout(selected):
    values={kind:(selected.get(kind,default) if isinstance(selected,dict) else getattr(selected,kind,default)) for kind,default in DEFAULTS.items()}
    return {kind:item if item in AVAILABLE_ITEMS[kind] else DEFAULTS[kind] for kind,item in values.items()}
