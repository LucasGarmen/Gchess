"""Painted heads share the existing independently equipped SVG accessory rig."""
from django.templatetags.static import static
from django.utils.html import escape
from .cosmetic_catalog import FREE_ITEMS

def painted_head(avatar):
    if avatar not in FREE_ITEMS['avatar']:
        return None
    source = escape(static(f'games/avatars/rustic/{avatar}.webp'))
    return (f'<image id="portrait-{avatar}" data-painted-avatar="{avatar}" '
            f'href="{source}" x="24" y="8" width="112" height="112" '
            'preserveAspectRatio="xMidYMid meet"/>')
