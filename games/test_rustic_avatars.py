from pathlib import Path
import xml.etree.ElementTree as ET
from django.test import SimpleTestCase
from django.contrib.staticfiles import finders
from .cosmetic_catalog import FREE_ITEMS
from .templatetags.cosmetic_art import draw_avatar

class PaintedAvatarTests(SimpleTestCase):
    def test_every_catalog_head_is_packaged_as_a_small_local_asset(self):
        for avatar in FREE_ITEMS['avatar']:
            with self.subTest(avatar=avatar):
                source=finders.find(f'games/avatars/rustic/{avatar}.webp')
                self.assertIsNotNone(source)
                self.assertLess(Path(source).stat().st_size,180_000)

    def test_retired_accessories_do_not_render_even_for_legacy_loadouts(self):
        svg=ET.fromstring(str(draw_avatar('explorer','cowboy','leather','moustache','dreads','round','gold_hoops',framing='bust')))
        namespace={'svg':'http://www.w3.org/2000/svg'}
        slots=[node.attrib.get('data-slot') for node in svg if node.tag.endswith('g')]
        self.assertEqual(slots,['clothing','head'])
        self.assertIn('/explorer.webp',svg.find("svg:g[@data-slot='head']/svg:image",namespace).attrib['href'])
        self.assertIn('clothing-leather.webp',svg.find("svg:g[@data-slot='clothing']/svg:image",namespace).attrib['href'])

    def test_every_painted_wearable_is_packaged(self):
        for kind in ('clothing','accessory','hairstyle','face'):
            for item in FREE_ITEMS[kind]:
                if item=='none':continue
                with self.subTest(kind=kind,item=item):
                    source=finders.find(f'games/avatars/wearables/{kind}-{item}.webp')
                    self.assertIsNotNone(source)
                    self.assertLess(Path(source).stat().st_size,180_000)

    def test_shop_metal_gradients_cannot_change_another_items_color(self):
        import re
        from .templatetags.cosmetic_art import draw_object
        gold=str(draw_object('earrings','gold_hoops'))
        silver=str(draw_object('earrings','silver_hoops'))
        self.assertTrue(set(re.findall(r'id="([^" ]+)"',gold)).isdisjoint(re.findall(r'id="([^" ]+)"',silver)))
        for art in (gold,silver):
            identifiers=set(re.findall(r'id="([^" ]+)"',art))
            self.assertTrue(set(re.findall(r'url\(#([^)]*)\)',art)).issubset(identifiers))
