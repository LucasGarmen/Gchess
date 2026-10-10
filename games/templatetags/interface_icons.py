"""Small semantic line icons; labels remain the source of accessible names."""
from django import template
from django.utils.html import format_html
register=template.Library()
ICONS={
 'home':'M3 11L12 3l9 8M5 10v11h5v-7h4v7h5V10',
 'play':'M8 5l11 7-11 7Z',
 'games':'M4 5h12v14H4ZM8 2h12v14M7 9h6M7 13h6',
 'analysis':'M10 3a7 7 0 1 0 0 14a7 7 0 0 0 0-14ZM15 15l6 6M6 11l3-3 3 2 3-4',
 'training':'M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3ZM12 6v15M6 8h3M15 8h3M6 12h3M15 12h3',
 'trophy':'M7 3h10v6a5 5 0 0 1-10 0ZM7 5H3v3q0 4 5 4M17 5h4v3q0 4-5 4M12 14v5M7 21h10M9 19h6',
 'ranking':'M4 20V12h5v8M10 20V4h5v16M16 20v-6h5v6',
 'shop':'M4 9h16v12H4ZM3 9l2-6h14l2 6M3 9q2 4 5 0q2 4 4 0q2 4 4 0q2 4 5 0M9 21v-7h6v7',
 'friends':'M9 4a3 3 0 1 0 0 6a3 3 0 0 0 0-6ZM2 20v-3q0-5 7-5q7 0 7 5v3M17 4q5 0 5 4q0 3-4 3M18 13q4 1 4 5v2',
 'login':'M14 3h7v18h-7M3 12h13M11 7l5 5-5 5',
 'register':'M9 3a4 4 0 1 0 0 8a4 4 0 0 0 0-8ZM2 21v-3q0-5 7-5q4 0 6 2M19 13v8M15 17h8',
 'logout':'M10 3H3v18h7M8 12h13M16 7l5 5-5 5',
 'profile':'M12 3a4 4 0 1 0 0 8a4 4 0 0 0 0-8ZM4 21v-3q0-5 8-5q8 0 8 5v3',
 'coach':'M12 3a4 4 0 1 0 0 8a4 4 0 0 0 0-8ZM3 20q0-7 9-7M16 14h6v6h-3l-3 2Z',
 'practice':'M12 3l3 5 6 1-4 5 1 6-6-3-6 3 1-6-4-5 6-1Z',
 'openings':'M5 21V8h14v13M3 3h5v5h3V3h3v5h3V3h4v5M3 21h18M10 21v-6h4v6',
 'daily':'M5 5h14v16H5ZM8 3v4M16 3v4M5 10h14M8 15l3 3 5-5',
 'progress':'M3 20h18M5 16l5-5 4 2 6-9M15 4h5v5',
 'lock':'M6 10h12v11H6ZM8 10V6a4 4 0 0 1 8 0v4M12 14v3',
 'blindfold':'M2 12q10-13 20 0q-10 13-20 0ZM4 3l16 18',
}
@register.simple_tag
def ui_icon(name):
    return format_html('<svg class="ui-icon" data-icon="{}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="{}"/></svg>',name,ICONS.get(name,ICONS['play']))
