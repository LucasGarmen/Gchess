from django.contrib.auth.models import User
from django.test import TestCase,Client
from django.urls import reverse
from .models import CosmeticLoadout

class StarterShopTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('shop_player')
        self.other=User.objects.create_user('other_shop_player')
        self.client.force_login(self.user)
    def equip(self,kind,item):return self.client.post(reverse('shop_equip'),{'kind':kind,'item':item})
    def test_public_catalog_is_read_only_and_defaults_are_available(self):
        response=Client().get(reverse('shop'))
        self.assertEqual(response.status_code,200)
        self.assertEqual(CosmeticLoadout.objects.count(),0)
        self.assertEqual(len(response.context['shop_cards']),171)
    def test_avatar_and_cap_persist_independently_after_login(self):
        self.equip('avatar','explorer');self.equip('face','moustache')
        self.client.logout();self.client.force_login(self.user)
        selected=self.client.get(reverse('shop')).context['cosmetics']
        self.assertEqual((selected['avatar'],selected['face']),('explorer','moustache'))
        self.equip('face','none')
        self.assertEqual(CosmeticLoadout.objects.get(user=self.user).face,'none')

    def test_catalog_validation_blocks_future_or_forged_items(self):
        for kind,item in [('board','wood'),('avatar','admin'),('accessory','shirt'),('coins','9999'),('avatar','<script>')]:
            self.assertEqual(self.equip(kind,item).status_code,400)
        self.assertEqual(CosmeticLoadout.objects.count(),0)
    def test_account_isolation_ignores_client_supplied_user_id(self):
        self.client.post(reverse('shop_equip'),{'kind':'face','item':'moustache','user_id':self.other.pk})
        self.assertFalse(CosmeticLoadout.objects.filter(user=self.other).exists())
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('shop')).context['cosmetics']['accessory'],'none')
    def test_equipping_requires_post_login_and_csrf(self):
        self.assertEqual(self.client.get(reverse('shop_equip')).status_code,405)
        self.assertEqual(Client().post(reverse('shop_equip'),{'kind':'avatar','item':'explorer'}).status_code,302)
        protected=Client(enforce_csrf_checks=True);protected.force_login(self.user)
        self.assertEqual(protected.post(reverse('shop_equip'),{'kind':'avatar','item':'explorer'}).status_code,403)
    def test_repeated_equipping_creates_one_loadout(self):
        for _ in range(3):self.equip('avatar','explorer')
        self.assertEqual(CosmeticLoadout.objects.filter(user=self.user).count(),1)
    def test_free_board_and_profile_show_selected_avatar(self):
        self.equip('board','rustic');self.equip('avatar','explorer')
        response=self.client.get(reverse('profile_stats'))
        self.assertContains(response,'profile-shop-avatar')
        self.assertContains(response,reverse('shop'))
    def test_labels_cover_three_languages(self):
        for lang,title in [('es','Tienda'),('pt','Loja'),('en','Shop')]:
            session=self.client.session;session['language']=lang;session.save()
            response=self.client.get(reverse('shop'))
            self.assertEqual(response.context['shop_texts']['title'],title)
            self.assertContains(response,'aria-current="page"')
    def test_equipping_has_no_elo_or_game_effect(self):
        from accounts.models import PlayerProfile
        profile,_=PlayerProfile.objects.get_or_create(user=self.user)
        before=profile.elo
        self.equip('face','moustache');profile.refresh_from_db()
        self.assertEqual(profile.elo,before)

    def test_categories_do_not_inherit_fixed_sidebar_navigation(self):
        response=self.client.get(reverse('shop'))
        self.assertContains(response,'class="shop-category"',count=7)
        self.assertNotContains(response,'<nav class="shop-tabs"')

    def test_all_slots_preserve_previous_selection(self):
        for kind,item in [('avatar','explorer'),('clothing','club'),('face','moustache'),('pieces','rustic'),('board','rustic')]:
            self.assertEqual(self.equip(kind,item).status_code,302)
        self.assertEqual(CosmeticLoadout.objects.get(user=self.user).face,'moustache')
        response=self.client.get(reverse('shop'))
        self.assertContains(response,'data-board="rustic"')
        self.assertContains(response,'data-pieces="rustic"')

    def test_every_catalog_preview_renders(self):
        from .cosmetic_catalog import FREE_ITEMS,AVAILABLE_ITEMS
        for kind,items in FREE_ITEMS.items():
            for item in items:
                with self.subTest(kind=kind,item=item):
                    self.assertEqual(self.equip(kind,item).status_code,302 if item in AVAILABLE_ITEMS[kind] else 403)
        response=self.client.get(reverse('shop'))
        self.assertEqual(response.status_code,200)
        self.assertEqual(sum(card['locked'] for card in response.context['shop_cards']),158)

    def test_accessory_tile_contains_only_object_and_native_equip_button(self):
        from django.template.loader import render_to_string
        response=self.client.get(reverse('shop'))
        for kind,item in [('accessory','cap'),('face','moustache'),('eyewear','glasses'),('clothing','forest')]:
            card=next(c for c in response.context['shop_cards'] if c['kind']==kind and c['item']==item)
            html=render_to_string('games/_shop_card.html',dict(card=card,user=self.user,shop_texts=response.context['shop_texts']),request=response.wsgi_request)
            self.assertIn('shop-accessory-art',html)
            self.assertNotIn('data-avatar-rig',html)
            if card['locked']:
                self.assertIn('disabled',html)
                self.assertNotIn('<form',html)
            else:
                self.assertIn('method="post"',html)
                self.assertIn('csrfmiddlewaretoken',html)
            self.assertIn('shop-item-button',html)
        self.assertNotContains(response,'Explorador')
        self.assertNotContains(response,'Estratega')

    def test_accessory_types_combine_and_replace_only_their_own_type(self):
        self.equip('face','moustache')
        self.equip('board','rustic')
        self.assertEqual(CosmeticLoadout.objects.get(user=self.user).face,'moustache')
        for kind,item in [('accessory','cap'),('hairstyle','dreads'),('eyewear','round'),('earrings','gold_hoops'),('face','long_beard')]:
            self.assertEqual(self.equip(kind,item).status_code,403)
        self.assertEqual(self.equip('face','long_beard,stubble').status_code,400)

    def test_legacy_glasses_move_to_independent_slot(self):
        import importlib
        from django.apps import apps
        loadout=CosmeticLoadout.objects.create(user=self.user,avatar='mentor',face='glasses',accessory='cap')
        migration=importlib.import_module('games.migrations.0033_cosmeticloadout_earrings_cosmeticloadout_eyewear_and_more')
        migration.move_legacy_glasses(apps,None)
        loadout.refresh_from_db()
        self.assertEqual((loadout.face,loadout.eyewear,loadout.avatar,loadout.accessory),('none','glasses','mentor','cap'))
    def test_catalog_labels_and_svg_shapes_are_complete_in_all_languages(self):
        from .cosmetic_catalog import FREE_ITEMS
        from .shop_texts import TEXTS
        from .cosmetic_art import avatar_art,accessory_shape
        import xml.etree.ElementTree as ET
        for lang in ('es','pt','en'):
            for kind,items in FREE_ITEMS.items():
                self.assertEqual(set(TEXTS[lang]['items'][kind]),set(items))
        for avatar in FREE_ITEMS['avatar']:
            svg=avatar_art(avatar,'fedora','hoodie','stubble','dreads','round','gold_hoops','bust')
            ET.fromstring('<svg>'+svg+'</svg>')
        for kind in ('accessory','clothing','hairstyle','face','eyewear','earrings'):
            for item in FREE_ITEMS[kind]:
                art=accessory_shape(kind,item)
                if item!='none':self.assertTrue(art,(kind,item))
                ET.fromstring('<svg>'+art+'</svg>')
    def test_shop_has_no_explanatory_prompts_and_accessories_are_grouped(self):
        session=self.client.session;session['language']='es';session.save()
        response=self.client.get(reverse('shop'))
        self.assertNotContains(response,'Podés combinar')
        self.assertNotContains(response,'Elegí una categoría')
        self.assertNotContains(response,'Detalles de la cara')
        self.assertContains(response,'Barbas y bigotes')
        self.assertContains(response,'shop-hairstyle')

    def test_avatar_only_expansion_preserves_other_category_counts(self):
        from .cosmetic_catalog import FREE_ITEMS
        self.assertEqual(len(FREE_ITEMS['avatar']),46)
        for kind in ('board','pieces','accessory','clothing','hairstyle'):
            self.assertEqual(len(FREE_ITEMS[kind]),20)
        self.assertEqual((len(FREE_ITEMS['face']),len(FREE_ITEMS['eyewear']),len(FREE_ITEMS['earrings'])),(9,9,7))
        for avatar in ('elephant','lion','duck','giraffe','dog','messi'):
            self.assertEqual(self.equip('avatar',avatar).status_code,403)

    def test_participant_portrait_uses_that_players_loadout_and_escapes_name(self):
        from .templatetags.cosmetic_art import player_avatar,draw_avatar
        from django.contrib.auth.models import AnonymousUser
        CosmeticLoadout.objects.create(user=self.user,avatar='explorer',face='moustache')
        CosmeticLoadout.objects.create(user=self.other,avatar='duck',eyewear='round')
        own=player_avatar(self.user,'<script>');other=player_avatar(self.other,'Opponent')
        self.assertNotEqual(own,other)
        self.assertIn('portrait-explorer',other)
        self.assertNotIn('portrait-duck',other)
        self.assertIn('&lt;script&gt;',own);self.assertNotIn('<script>',own)
        import re
        normalize=lambda svg: re.sub(r'-[0-9a-f]{32}', '', str(svg))
        self.assertEqual(normalize(player_avatar(AnonymousUser())),normalize(draw_avatar('explorer',framing='bust')))

    def test_coach_board_hides_removed_instructions_and_shows_player(self):
        response=self.client.get(reverse('home'))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'entry-board-tip')
        self.assertNotContains(response,'workspace-storage-notice')
        self.assertContains(response,'data-human-player')

    def test_online_game_displays_both_equipped_portraits(self):
        from .models import ChessGame
        CosmeticLoadout.objects.create(user=self.user,avatar='explorer',face='moustache')
        CosmeticLoadout.objects.create(user=self.other,avatar='explorer')
        game=ChessGame.objects.create(owner=self.user,white_user=self.user,black_user=self.other,white_player=self.user.username,black_player=self.other.username)
        response=self.client.get(reverse('game_detail',args=[game.pk]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'class="board-player game-player-avatar"',count=2)
        self.assertContains(response,'data-player-color="white"')
        self.assertContains(response,'data-player-color="black"')


    def test_changing_avatar_clears_accessories_but_reselecting_does_not(self):
        from unittest.mock import patch
        from .cosmetic_catalog import AVAILABLE_ITEMS
        loadout=CosmeticLoadout.objects.create(user=self.user,avatar='explorer',face='moustache',board='rustic')
        self.equip('avatar','explorer');loadout.refresh_from_db()
        self.assertEqual(loadout.face,'moustache')
        # Exercise the rule for when more avatars become available again.
        with patch.dict(AVAILABLE_ITEMS,avatar=('explorer','strategist')):
            self.assertEqual(self.equip('avatar','strategist').status_code,302)
        loadout.refresh_from_db()
        self.assertEqual(loadout.avatar,'strategist')
        self.assertEqual((loadout.accessory,loadout.face,loadout.hairstyle,loadout.eyewear,loadout.earrings),('none',)*5)
        self.assertEqual((loadout.board,loadout.pieces,loadout.clothing),('rustic','rustic','club'))

    def test_locked_legacy_selection_is_not_used_and_rejected_posts_do_not_save(self):
        loadout=CosmeticLoadout.objects.create(user=self.user,avatar='lion',board='lava',pieces='gold',accessory='cap')
        response=self.client.get(reverse('shop'))
        self.assertEqual(response.context['cosmetics']['avatar'],'explorer')
        self.assertContains(response,'data-board="rustic"')
        self.assertContains(response,'data-pieces="rustic"')
        before=loadout.avatar
        self.assertEqual(self.equip('avatar','duck').status_code,403)
        loadout.refresh_from_db();self.assertEqual(loadout.avatar,before)
        self.equip('face','moustache');loadout.refresh_from_db()
        self.assertEqual((loadout.avatar,loadout.board,loadout.pieces,loadout.accessory),('explorer','rustic','rustic','none'))

    def test_chess_piece_avatars_are_ordered_locked_and_named(self):
        from .cosmetic_catalog import FREE_ITEMS
        from .shop_texts import TEXTS
        pieces=('piece_pawn','piece_bishop','piece_knight','piece_rook','piece_king','piece_queen')
        positions=[FREE_ITEMS['avatar'].index(piece) for piece in pieces]
        self.assertEqual(positions,sorted(positions))
        self.assertEqual(FREE_ITEMS['avatar'][-2:],list(pieces[-2:]))
        for piece in pieces:
            self.assertEqual(self.equip('avatar',piece).status_code,302 if piece=='piece_pawn' else 403)
            for lang in ('es','pt','en'):self.assertTrue(TEXTS[lang]['items']['avatar'][piece])
        self.assertContains(self.client.get(reverse('home')),'data-sound-toggle')

    def test_four_starter_avatars_include_woman_and_coaches_have_portraits(self):
        from .cosmetic_catalog import FREE_ITEMS,AVAILABLE_ITEMS
        self.assertEqual(AVAILABLE_ITEMS['avatar'],tuple(FREE_ITEMS['avatar'][:4]))
        self.assertIn('pilot',AVAILABLE_ITEMS['avatar'])
        for avatar in AVAILABLE_ITEMS['avatar']:self.assertEqual(self.equip('avatar',avatar).status_code,302)
        response=self.client.get(reverse('home'))
        self.assertContains(response,'data-coach-player')
        for level in (500,800,1000,1320,1600,2000,2500):self.assertContains(response,f'data-coach-level="{level}"',count=1)
