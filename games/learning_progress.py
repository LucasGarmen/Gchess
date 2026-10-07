"""Read-only progress from saved training and reviews; no engine or AI calls."""
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from .models import DailyTraining, WeeklyChallengeEntry
from .learning_progress_texts import TEXTS


def daily_counts(plan):
    resolved=[p for p in plan.progress if p.get('resolved')]
    independent=sum(bool(p.get('correct')) and not p.get('helped') and p.get('attempts')==1 for p in resolved)
    return len(resolved),independent


def learning_progress(user,language,reviews):
    from .weekly import week_start
    texts=TEXTS[language];today=timezone.localdate();start=today-timedelta(days=6)
    plans=list(DailyTraining.objects.filter(user=user,date__range=(start,today)).order_by('date'))
    by_date={plan.date:plan for plan in plans};current=by_date.get(today)
    completed=sum(plan.completed_at is not None for plan in plans)
    resolved=independent=0
    for plan in plans:
        count,first=daily_counts(plan);resolved+=count;independent+=first
    calendar=[]
    for offset in range(7):
        date=start+timedelta(days=offset);plan=by_date.get(date)
        status='done' if plan and plan.completed_at else 'started' if plan else 'empty'
        calendar.append(dict(date=date,status=status,label=texts['day_'+('done' if status=='done' else 'started' if status=='started' else 'empty')],today=date==today))
    week=week_start()
    weekly=WeeklyChallengeEntry.objects.filter(user=user,challenge__week_start=week).select_related('challenge').first()
    weekly_attempts=sum(bool(p.get('attempted')) for p in weekly.progress) if weekly else 0
    daily_status='completed' if current and current.completed_at else 'in_progress' if current else 'not_started'
    daily_resolved=daily_counts(current)[0] if current else 0
    if not current or not current.completed_at:
        key='daily_resume' if current else 'daily_next';action='continue_daily' if current else 'start_daily'
        next_step=dict(text=texts[key],label=texts[action],url=reverse('daily_training'))
    elif weekly_attempts<5:
        next_step=dict(text=texts['weekly_next'],label=texts['continue_weekly'],url=reverse('weekly_challenge'))
    else:
        pending=next((row['review'] for row in reviews if not row['review'].goal_completed_at and row['summary']['errors']),None)
        next_step=dict(text=texts['review_next' if pending else 'practice_next'],label=texts['review_action' if pending else 'practice_action'],url=reverse('review_detail',args=[pending.pk]) if pending else reverse('practice'))
    activities=[]
    for plan in DailyTraining.objects.filter(user=user,date__lte=today).order_by('-date')[:10]:
        count,_=daily_counts(plan)
        if not any(p.get('attempts') or p.get('helped') or p.get('resolved') for p in plan.progress):continue
        activities.append(dict(date=plan.date,title=texts['daily_activity'],detail=f"{count} / {len(plan.tasks)} · "+texts['completed' if plan.completed_at else 'in_progress'],url=reverse('daily_training') if plan.date==today else None))
    for entry in WeeklyChallengeEntry.objects.filter(user=user,challenge__week_start__lte=week).select_related('challenge').order_by('-challenge__week_start')[:10]:
        attempts=sum(bool(p.get('attempted')) for p in entry.progress)
        if not attempts:continue
        activities.append(dict(date=timezone.localdate(entry.completed_at or entry.started_at),title=texts['weekly'],detail=f"{entry.score} / 50 · {attempts} / 5 "+texts['attempts'],url=reverse('weekly_play',args=[entry.pk])+'?practice=1' if attempts==5 or entry.challenge.week_start<week else reverse('weekly_play',args=[entry.pk])))
    for row in reviews[:10]:
        review=row['review']
        activities.append(dict(date=timezone.localdate(review.created_at),title=texts['review'],detail=row['summary']['focus_name'],url=reverse('review_detail',args=[review.pk])))
    activities.sort(key=lambda item:item['date'],reverse=True)
    return dict(texts=texts,days=completed,goal_progress=min(completed,3),goal_reached=completed>=3,calendar=calendar,
        resolved=resolved,independent=independent,daily_status=daily_status,daily_resolved=daily_resolved,
        daily_total=len(current.tasks) if current else 3,weekly_score=weekly.score if weekly else None,weekly_attempts=weekly_attempts,
        weekly_status='completed' if weekly_attempts==5 else 'in_progress' if weekly else 'not_started',week=week,next_step=next_step,activities=activities[:8])
