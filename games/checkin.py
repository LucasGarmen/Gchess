from zoneinfo import ZoneInfo
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import DailyCheckin
from .i18n import current_language

POINTS_PER_CHECKIN = 10

def today():
    return timezone.localdate(timezone.now(), ZoneInfo('America/Fortaleza'))

def context(request):
    texts = {
        'es': ('Puntos', 'Check-in diario · +10', 'Hoy ya recibiste tus 10 puntos', 'Se renueva a medianoche de Brasil (UTC−3).'),
        'pt': ('Pontos', 'Check-in diário · +10', 'Você já recebeu seus 10 pontos hoje', 'Renova à meia-noite do Brasil (UTC−3).'),
        'en': ('Points', 'Daily check-in · +10', 'You claimed your 10 points today', 'Resets at midnight in Brazil (UTC−3).'),
    }
    words=dict(zip(('points','claim','claimed','reset'), texts.get(current_language(request),texts['en'])))
    if not request.user.is_authenticated:
        return {'checkin_words': words}
    totals=DailyCheckin.objects.filter(user=request.user).aggregate(total=Count('id'), claimed=Count('id',filter=Q(date=today())))
    return {'checkin_words':words,'checkin_balance':totals['total']*POINTS_PER_CHECKIN,'checkin_claimed':bool(totals['claimed'])}

@login_required
@require_POST
def claim(request):
    # The database unique constraint also handles concurrent tabs and requests.
    DailyCheckin.objects.get_or_create(user=request.user,date=today())
    return redirect('shop' if request.POST.get('destination') == 'shop' else 'home')
