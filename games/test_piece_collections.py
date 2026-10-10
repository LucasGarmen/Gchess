from pathlib import Path
import xml.etree.ElementTree as ET
from django.test import SimpleTestCase
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from .cosmetic_catalog import FREE_ITEMS
from .shop_texts import TEXTS

class PieceCollectionTests(SimpleTestCase):
    def test_all_collections_have_complete_self_contained_sharp_assets(self):
        namespace={'s':'http://www.w3.org/2000/svg'}
        silhouettes=[]
        for style in FREE_ITEMS['pieces']:
            geometry=[]
            for color in ('white','black'):
                roles=[]
                for role in ('king','queen','rook','bishop','horse','pawn'):
                    source=finders.find(f'games/pieces-{style}/{role}_{color}.svg')
                    self.assertIsNotNone(source)
                    text=Path(source).read_text(encoding='utf-8')
                    svg=ET.fromstring(text)
                    self.assertEqual(svg.attrib['viewBox'],'0 0 100 100')
                    self.assertNotIn('<filter',text)
                    self.assertNotIn('<image',text)
                    shapes=tuple(node.attrib.get('d','') for node in svg.findall('.//s:path',namespace))
                    roles.append(shapes)
                    geometry.extend(shapes)
                self.assertEqual(len(set(roles)),6,style)
            silhouettes.append(tuple(geometry))
        self.assertEqual(len(set(silhouettes)),20,'Collections must change geometry, not only colors.')

    def test_previews_show_each_role_in_both_colors_and_labels_cover_languages(self):
        html=render_to_string('games/_shop_pieces.html',{'piece_style':'obsidian'})
        for role in ('king','queen','rook','bishop','horse','pawn'):
            for color in ('white','black'):
                self.assertIn(f'{role}_{color}.svg?v=4',html)
        for lang in ('es','pt','en'):
            self.assertEqual(len(TEXTS[lang]['items']['pieces']),20)
