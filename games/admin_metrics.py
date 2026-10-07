"""Superadministrator-only aggregate activity; no public endpoint."""
import csv
from datetime import timedelta, datetime, time
from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef
from django.db.models.functions import TruncDate
from django.http import HttpResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.utils import timezone
from .models import UserPresence, PlayerActivityDay

def dashboard(site, request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Solo el superadministrador puede ver estas estadísticas.')
    today=timezone.localdate(); start=today-timedelta(days=29)
    players=User.objects.filter(is_active=True,is_staff=False)
    activity=PlayerActivityDay.objects.filter(user__in=players,date__gte=start,date__lte=today)
    previous=PlayerActivityDay.objects.filter(user_id=OuterRef('user_id'),date__lt=OuterRef('date'))
    counts={r['date']:r['total'] for r in activity.values('date').annotate(total=Count('user_id'))}
    repeat={r['date']:r['total'] for r in activity.annotate(returning=Exists(previous)).filter(returning=True).values('date').annotate(total=Count('user_id'))}
    since=timezone.make_aware(datetime.combine(start,time.min))
    new={r['day']:r['total'] for r in players.filter(date_joined__gte=since,date_joined__lte=timezone.now()).annotate(day=TruncDate('date_joined')).values('day').annotate(total=Count('pk'))}
    rows=[dict(date=start+timedelta(days=i),active=counts.get(start+timedelta(days=i),0),returning=repeat.get(start+timedelta(days=i),0),new=new.get(start+timedelta(days=i),0)) for i in range(30)]
    first_day=PlayerActivityDay.objects.order_by('date').values_list('date',flat=True).first()
    for row in rows:
        row['tracked']=row['date'] >= (first_day or today)
    if request.GET.get('export')=='csv':
        response=HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition']='attachment; filename="gchess-actividad-30-dias.csv"'
        writer=csv.writer(response);writer.writerow(['fecha','cuentas_nuevas','jugadores_activos','jugadores_que_volvieron'])
        for row in rows:writer.writerow([row['date'].isoformat(),row['new'],row['active'] if row['tracked'] else '',row['returning'] if row['tracked'] else ''])
        response['Cache-Control']='private, no-store'
        return response
    online=UserPresence.objects.filter(user__in=players,last_seen__gte=timezone.now()-timedelta(seconds=60)).select_related('user').order_by('-last_seen')
    maximum=max([r['active'] for r in rows]+[r['new'] for r in rows]+[1])
    for row in rows:
        row['active_height']=round(row['active']/maximum*100)
        row['new_height']=round(row['new']/maximum*100)
    context={**site.each_context(request),'title':'Actividad de jugadores','online_count':online.count(),'online_players':list(online[:50]),'total_players':players.count(),'new_today':new.get(today,0),'active_today':counts.get(today,0),'returning_today':repeat.get(today,0),'rows':rows,'table_rows':list(reversed(rows)),'updated':timezone.now(),'first_day':first_day}
    response=TemplateResponse(request,'admin/player_activity.html',context)
    response['Cache-Control']='private, no-store'
    return response
