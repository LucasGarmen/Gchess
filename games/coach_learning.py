"""Bounded, account-local learning facts for the conversational coach."""
import hashlib
import json
import re
from collections import Counter
from django.core.cache import cache
from django.utils import timezone
from .models import DailyTraining, GameReview
from .personal_sessions import position_key, practice_memory, theme_for
from .personal_session_texts import TEXTS


def learning_context(user, language):
    if not user.is_authenticated: return None
    today=timezone.localdate()
    current=DailyTraining.objects.filter(user=user,date=today).only('pk','date','tasks','progress','completed_at').first()
    latest=GameReview.objects.filter(user=user).order_by('-created_at').values_list('pk',flat=True).first()
    if not latest and not current: return None
    revision=json.dumps(current.progress if current else [],sort_keys=True)+str(current.completed_at if current else '')
    key=f'coach-learning:v2:{user.pk}:{language}:{today}:{latest}:{current.pk if current else 0}:'+hashlib.sha256(revision.encode()).hexdigest()
    cached=cache.get(key)
    if cached is not None: return cached
    from .daily_training import candidates
    tasks=candidates(user,max_reviews=6,max_positions=24)
    unique={}
    for task in tasks:
        unique.setdefault(position_key(task['fen']),task)
    counts=Counter(theme_for(task) for task in unique.values())
    texts=TEXTS[language]
    memory=practice_memory(user,today) if unique else {}
    memory={k:v for k,v in memory.items() if k in unique}
    context=dict(source='saved_reviews_and_training',scope='limited_sample_not_a_skill_diagnosis',
        verified_positions=len(unique),patterns=[dict(topic=theme,label=texts[theme],positions=count) for theme,count in counts.most_common(3)],
        practice=dict(positions=len(memory),confirmed=sum(v['streak']>=2 for v in memory.values()),
                      needs_support=sum(not v['independent'] for v in memory.values()),due=sum(v['due']<=today for v in memory.values())),session=None)
    if current:
        # Only owned review references may contribute to a personal focus.
        source_ids={t.get('source') for t in current.tasks if isinstance(t,dict) and t.get('source')}
        owned=set(GameReview.objects.filter(user=user,pk__in=source_ids).values_list('pk',flat=True))
        themes=[]
        for task in current.tasks:
            if not isinstance(task,dict) or task.get('source') not in owned: continue
            try: themes.append(theme_for(task))
            except (ValueError,KeyError,TypeError): continue
        theme=Counter(themes).most_common(1)[0][0] if themes else 'mate'
        resolved=[a for a in current.progress if isinstance(a,dict) and a.get('resolved')]
        independent=sum(bool(a.get('correct')) and not a.get('helped') and a.get('attempts')==1 for a in resolved)
        context['session']=dict(date=today.isoformat(),status='completed' if current.completed_at else 'in_progress',
            focus=texts[theme],tip=texts['tip_'+theme],uses_own_games=bool(themes),resolved=len(resolved),
            total=len(current.tasks),independent=independent,with_help_or_retries=len(resolved)-independent)
    from .error_patterns import recurring_errors
    findings=recurring_errors(user,language)
    context['recurring']=[dict(label=p['label'],tip=p['tip'],games=p['games'],examples=[e['explanation'] for e in p['examples']]) for p in findings['patterns']]
    if not unique and not current: return None
    cache.set(key,context,60)
    return context


def learning_fallback(context, language, question=""):
    from .engine_analysis import normalize_piece_text
    asks_practice=bool(re.search(r"practic|pratic|entren|trein|repas|revisar|work on",normalize_piece_text(question)))
    asks_progress=not asks_practice and bool(re.search(r"mejorando|melhorando|improving|progres|aprendi|learned",normalize_piece_text(question)))
    if not context:
        return {'es':'Todavía no tengo revisiones o entrenamientos guardados para orientarte con tus resultados. Podés empezar con práctica guiada; después analizá una partida y abrí Mi aprendizaje para una sesión personalizada.',
                'pt':'Ainda não tenho revisões ou treinos salvos para orientar você pelos seus resultados. Comece com a prática guiada; depois analise uma partida e abra Meu aprendizado para uma sessão personalizada.',
                'en':'I do not have saved reviews or training to guide you using your results yet. Start with guided practice, then analyze a game and open My learning for a personalized session.'}[language]
    session=context.get('session')
    if asks_progress:
        practice=context['practice']
        if not practice['positions']:
            return {'es':'Todavía no tengo suficientes repasos de tus partidas para comparar tu progreso. Resolver una posición una vez no alcanza para saber si la aprendiste. En Mi aprendizaje podés practicarla y comprobarlo en otro día.',
                    'pt':'Ainda não tenho revisões suficientes das suas partidas para comparar seu progresso. Resolver uma posição uma vez não basta para saber se você aprendeu. Em Meu aprendizado você pode praticá-la e conferir em outro dia.',
                    'en':'I do not have enough repeated practice from your games to compare progress yet. Solving a position once does not establish that you learned it. Open My learning to practice and check again on another day.'}[language]
        return {'es':'En los repasos guardados hay {confirmed} posiciones que resolviste al primer intento y sin ayuda en días distintos. En {needs_support}, el último intento necesitó pistas o reintentos. Es una señal sobre esos ejercicios; todavía no demuestra que juegues mejor en partidas nuevas. Mi aprendizaje te muestra qué repasar.',
                'pt':'Nas revisões salvas há {confirmed} posições resolvidas na primeira tentativa e sem ajuda em dias diferentes. Em {needs_support}, a última tentativa precisou de dicas ou repetições. Isso descreve esses exercícios; ainda não demonstra melhora em partidas novas. Meu aprendizado mostra o que revisar.',
                'en':'In saved practice, {confirmed} positions were solved on the first attempt without help on different days. For {needs_support}, the latest attempt needed hints or retries. That describes these exercises; it does not yet demonstrate improvement in new games. My learning shows what to revisit.'}[language].format(**practice)
    if context.get('recurring'):
        pattern=context['recurring'][0]
        intro={'es':'En {games} partidas revisadas aparece este error: {label}.','pt':'Em {games} partidas revisadas aparece este erro: {label}.','en':'This mistake appears in {games} reviewed games: {label}.'}[language].format(**pattern)
        return intro+' '+pattern['examples'][0]+' '+pattern['tip']+' '+{'es':'En Mi aprendizaje podés ver los ejemplos y practicar.','pt':'Em Meu aprendizado você pode ver os exemplos e praticar.','en':'Open My learning to see the examples and practice.'}[language]
    if session:
        return {'es':'Hoy te propongo practicar esto: {focus}. Resolviste {resolved} de {total} posiciones, {independent} al primer intento y sin pistas. {tip} En Mi aprendizaje podés ver el próximo paso.',
                'pt':'Hoje sugiro praticar isto: {focus}. Você resolveu {resolved} de {total} posições, {independent} na primeira tentativa e sem dicas. {tip} Em Meu aprendizado você pode ver o próximo passo.',
                'en':'Today I suggest practicing this: {focus}. You solved {resolved} of {total} positions, {independent} on the first attempt without hints. {tip} Open My learning to see your next step.'}[language].format(**dict(session,focus=session['focus'].lower(),tip=session['tip'][:1].upper()+session['tip'][1:]))
    label=context['patterns'][0]['label'] if context['patterns'] else TEXTS[language]['mate']
    return {'es':'En las posiciones revisadas aparece {focus}. Eso orienta la práctica, pero no significa que siempre cometas ese error. Abrí Mi aprendizaje para trabajar esas posiciones y revisar tus resultados.',
            'pt':'Nas posições revisadas aparece {focus}. Isso orienta a prática, mas não significa que você sempre cometa esse erro. Abra Meu aprendizado para treinar essas posições e revisar seus resultados.',
            'en':'The reviewed positions include {focus}. This guides practice; it does not mean you always make that mistake. Open My learning to practice those positions and review your results.'}[language].format(focus=label)
