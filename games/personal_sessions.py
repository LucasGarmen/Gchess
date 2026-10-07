"""Personal practice selection from verified reviews and saved answers, without AI calls."""
from collections import Counter
from datetime import date, timedelta
import chess
import uuid
from django.urls import reverse
from django.utils import timezone
from .models import DailyTraining
from .personal_session_texts import TEXTS


def position_key(fen):
    # Move counters do not change the skill being rehearsed; keep castling and en passant.
    board = chess.Board(fen)
    return ' '.join(board.fen().split()[:4])


def theme_for(task):
    board = chess.Board(task['fen'])
    move = chess.Move.from_uci(task['solution'])
    after = board.copy(); after.push(move)
    if after.is_checkmate(): return 'mate'
    if board.is_check() or board.is_castling(move): return 'king'
    if board.is_capture(move): return 'material'
    if task.get('phase') in ('opening', 'endgame'): return task['phase']
    return 'decisions'


def practice_memory(user, today):
    memory = {}
    plans = list(DailyTraining.objects.filter(user=user, date__lte=today).order_by('-date')[:180])
    events = []
    for plan in plans:
        for task, answer in zip(plan.tasks, plan.progress):
            if not isinstance(task, dict) or not task.get('source') or not isinstance(answer, dict) or not answer.get('resolved'): continue
            try:
                key = position_key(task['fen'])
                practiced = date.fromisoformat(answer.get('resolved_on', plan.date.isoformat()))
            except (ValueError, TypeError, KeyError): continue
            if practiced > today: continue
            events.append((practiced, plan.pk, key, answer))
    for practiced, _, key, answer in sorted(events, key=lambda item:(item[0],item[1])):
        previous = memory.get(key)
        if previous and practiced <= previous['date']: continue
        independent = bool(answer.get('correct')) and not answer.get('helped') and answer.get('attempts') == 1
        streak = (previous['streak'] if previous else 0) + 1 if independent else 0
        interval = (3, 7, 14, 30)[min(streak-1, 3)] if independent else 1
        memory[key] = dict(date=practiced, due=practiced+timedelta(days=interval), streak=streak,
                           independent=independent, repetitions=(previous['repetitions'] if previous else 0)+1)
    return memory


def preparation(user, today):
    from .daily_training import candidates
    unique = {}
    for task in candidates(user):
        key = position_key(task['fen'])
        if key not in unique:
            unique[key] = dict(task, theme=theme_for(task))
    tasks = list(unique.values())
    memory = practice_memory(user, today)
    counts = Counter(task['theme'] for task in tasks)
    focus = counts.most_common(1)[0][0] if counts else 'mate'
    due = [t for t in tasks if position_key(t['fen']) in memory and memory[position_key(t['fen'])]['due'] <= today]
    fresh = [t for t in tasks if position_key(t['fen']) not in memory]
    due.sort(key=lambda t:(memory[position_key(t['fen'])]['independent'],memory[position_key(t['fen'])]['due'],-t['loss']))
    from .error_patterns import recurring_errors
    recurring=recurring_errors(user,'en')['positions']
    fresh.sort(key=lambda t:(position_key(t['fen']) not in recurring,t['theme'] != focus,-t['loss']))
    return dict(tasks=tasks, memory=memory, counts=counts, focus=focus, due=due, fresh=fresh)


def selected_tasks(prepared):
    # Revisiting one due position leaves room for new material; more due items fill unused slots.
    chosen = prepared['due'][:1] + prepared['fresh'][:2]
    keys = {position_key(t['fen']) for t in chosen}
    for task in prepared['due'][1:] + prepared['fresh'][2:]:
        if len(chosen) >= 3: break
        if position_key(task['fen']) not in keys:
            chosen.append(task); keys.add(position_key(task['fen']))
    for task in chosen:
        task['revisit'] = position_key(task['fen']) in prepared['memory']
    return chosen


def personal_selection(user, today):
    return selected_tasks(preparation(user,today))


def next_session(user, language, current=None):
    today = timezone.localdate(); texts = TEXTS[language]
    prepared = preparation(user,today)
    owned_keys = {position_key(t['fen']) for t in prepared['tasks']}
    memory = {k:v for k,v in prepared['memory'].items() if k in owned_keys}
    selected = current.tasks if current else selected_tasks(prepared)
    personal = [t for t in selected if isinstance(t,dict) and t.get('source')]
    focus = Counter(theme_for(t) for t in personal).most_common(1)[0][0] if personal else 'mate'
    coach_url = reverse('home')+'?bot=session-'+uuid.uuid4().hex
    status = 'finished' if current and current.completed_at else 'resume' if current else 'start'
    if status == 'finished':
        title, detail, label, url = texts['apply'], texts['apply_help'].format(focus=texts['tip_'+focus]), texts['play'], coach_url
    else:
        title, detail, label, url = texts['resume' if current else 'session'], texts['intro'], texts['continue' if current else 'start'], reverse('daily_training')
    next_due = min((v['due'] for v in memory.values() if v['due']>today),default=None)
    return dict(texts=texts,status=status,title=title,detail=detail,label=label,url=url,coach_url=coach_url,personal_focus=bool(personal),focus=texts[focus],tip=texts['tip_'+focus],
        has_personal=bool(prepared['tasks']),due=len(prepared['due']),fresh=len(prepared['fresh']),next_due=next_due,
        confirmed=sum(v['streak']>=2 for v in memory.values()),needs_help=sum(not v['independent'] for v in memory.values()),
        practiced=len(memory),themes=[dict(label=texts[theme],count=count) for theme,count in prepared['counts'].most_common(3)])
