"""Shared descriptions for the existing training modes. No database writes."""
MODE_ROUTES = ('practice', 'daily_puzzle', 'blitz', 'streak')
MODE_CONTENT = {
    'es': (
        ('Práctica guiada', 'Aprendé a tu ritmo', 'Elegí un tema, resolvé la posición y revisá la solución.', 'Sin límite de tiempo. Podés usar pistas, reintentar y revisar la línea.', 'Con sesión iniciada: XP, rating de puzzles y logros. El contador de categorías se guarda en este navegador.'),
        ('Puzzle diario', 'Un desafío nuevo cada día', 'Un desafío nuevo cada día, con un resultado por cuenta.', 'Un intento por día. Un error termina el intento; el tiempo mide cuánto tardaste, sin cuenta regresiva.', 'Con sesión iniciada: resultado del día, tiempo y progreso de puzzles. Mañana hay otro desafío.'),
        ('Blitz · 3 minutos', 'Entrená la rapidez', 'Resolvé tantos puzzles como puedas antes de que termine el reloj.', 'El reloj empieza al tocar Iniciar desafío. Cada puzzle correcto da 10 puntos, más 5 por cada jugada de mate adicional. Un error resta 2 puntos, sin bajar de cero; podés seguir.', 'Con sesión iniciada: tu mejor puntuación de Blitz. Estos puntos son distintos de los XP y del rating.'),
        ('Racha · sin errores', 'Entrená la precisión', 'Encadená puzzles correctos y tratá de superar tu récord.', 'Sin reloj. Cada puzzle resuelto suma un acierto; el primer error termina el desafío.', 'Con sesión iniciada: tu mejor racha de este modo. Es un récord separado de la secuencia general de aciertos.'),
    ),
    'pt': (
        ('Prática guiada', 'Aprenda no seu ritmo', 'Escolha um tema, resolva a posição e reveja a solução.', 'Sem limite de tempo. Use dicas, tente novamente e reveja a linha.', 'Com login: XP, rating de puzzles e conquistas. O contador de categorias fica neste navegador.'),
        ('Puzzle diário', 'Um novo desafio por dia', 'Um novo desafio por dia, com um resultado por conta.', 'Uma tentativa por dia. Um erro encerra a tentativa; o tempo mede sua duração, sem contagem regressiva.', 'Com login: resultado do dia, tempo e progresso de puzzles. Amanhã há outro desafio.'),
        ('Blitz · 3 minutos', 'Treine a rapidez', 'Resolva o máximo de puzzles antes de o relógio terminar.', 'O relógio começa ao tocar em Iniciar desafio. Cada puzzle correto vale 10 pontos, mais 5 por jogada de mate adicional. Um erro tira 2 pontos, sem ficar negativo; você pode continuar.', 'Com login: sua melhor pontuação de Blitz. Esses pontos são diferentes de XP e rating.'),
        ('Sequência · sem erros', 'Treine a precisão', 'Acerte puzzles consecutivos e tente superar seu recorde.', 'Sem relógio. Cada puzzle resolvido soma um acerto; o primeiro erro encerra o desafio.', 'Com login: sua melhor sequência neste modo. É um recorde separado da sequência geral de acertos.'),
    ),
    'en': (
        ('Guided practice', 'Learn at your own pace', 'Choose a theme, solve the position and review the solution.', 'No time limit. Use hints, retry and review the line.', 'When signed in: XP, puzzle rating and achievements. Category counters are stored in this browser.'),
        ('Daily puzzle', 'A new challenge each day', 'A new challenge each day, with one result per account.', 'One attempt per day. An error ends the attempt; elapsed time is measured without a countdown.', 'When signed in: today’s result, time and puzzle progress. There is another challenge tomorrow.'),
        ('Blitz · 3 minutes', 'Train your speed', 'Solve as many puzzles as possible before time runs out.', 'The clock starts when you select Start challenge. Each correct puzzle earns 10 points, plus 5 for each additional mate move. An error costs 2 points, never below zero; you can continue.', 'When signed in: your best Blitz score. These points are separate from XP and rating.'),
        ('Streak · no mistakes', 'Train your accuracy', 'Solve consecutive puzzles and try to beat your record.', 'No clock. Each solved puzzle adds one success; the first error ends the challenge.', 'When signed in: your best streak in this mode. This record is separate from your overall correct-answer sequence.'),
    ),
}

TRAINING_TEXTS = {
    'es': {
        'training_another_round': 'Otra ronda',
        'training_start_challenge': 'Iniciar desafío', 'training_challenge_ready': 'Leé las reglas y tocá Iniciar desafío cuando estés listo.', 'streak_login_to_save': 'Iniciá sesión para guardar tu mejor racha.', 'blitz_login_to_save': 'Iniciá sesión para guardar tu mejor puntuación.', 'practice_progress': 'En este navegador', 'streak_current': 'Aciertos en este desafío', 'streak_run_help': 'Cada puzzle correcto suma uno. El primer error termina el desafío.', 'streak_failed': 'Error: terminó la racha.', 'nav_training': 'Entrenar', 'training_title': 'Elegí cómo querés entrenar',
        'training_intro': 'Aprender, crear un hábito o superar tu récord: cada modo tiene un objetivo distinto.',
        'training_modes': 'Los cuatro entrenamientos', 'training_start': 'Empezar',
        'training_all': 'Todos los modos', 'training_rules': 'Reglas y progreso',
        'training_progress': 'Tu progreso', 'training_guest': 'Podés probar Práctica, Blitz y Racha sin cuenta. Iniciá sesión para guardar tu progreso; el puzzle diario requiere una cuenta.',
        'training_today': 'Tu próximo entrenamiento', 'training_daily_ready': 'El desafío de hoy te espera.',
        'training_daily_continue': 'Tenés un desafío diario en curso. Podés continuar.',
        'training_daily_done': 'Ya completaste tu intento de hoy. Ahora podés practicar.',
        'training_recommended': 'Empezá por Práctica guiada para conocer los puzzles.',
        'training_continue': 'Continuar el diario', 'training_daily_result': 'Ver resultado de hoy',
        'training_record_blitz': 'Récord Blitz · puntos', 'training_record_streak': 'Récord Racha · puzzles',
        'training_goal': 'Tu próximo objetivo', 'training_goal_help': 'Puzzles correctos para alcanzar el siguiente objetivo de entrenamiento.',
        'training_goal_done': 'Completaste todos los objetivos de cantidad de puzzles. Seguí mejorando tus récords.',
        'training_metrics': 'Qué significa cada medida',
        'training_xp_help': 'Los XP reconocen puzzles resueltos. Cada 100 XP subís un nivel. El nivel mide actividad, no fuerza ajedrecística.',
        'training_rating_help': 'El rating de puzzles sube con aciertos y baja con errores. Ordena el ranking de ejercicios; es distinto del Elo de partidas.',
        'training_records_help': 'Blitz guarda puntos por rapidez y Racha guarda aciertos seguidos. Sus récords son personales y no se mezclan entre sí.',
        'training_sequence_help': 'La secuencia general cuenta aciertos consecutivos entre tus entrenamientos. No representa días de actividad ni el récord del modo Racha.',
        'training_account': 'Cuenta necesaria', 'training_explore': 'Explorar entrenamientos',
        'home_hub_title': 'Tu entrenamiento', 'home_hub_guest': 'Elegí un objetivo y conocé las reglas de cada modo.',
        'home_hub_intro': 'Tu nivel, rating de puzzles y secuencia de aciertos.',
        'home_hub_rating': 'Rating de puzzles', 'home_hub_streak': 'Aciertos seguidos',
        'leaderboard_title': 'Ranking de ejercicios', 'leaderboard_intro': 'Compará tu progreso resolviendo posiciones de ajedrez. Ordenado por tu puntaje de ejercicios; es distinto del Elo de partidas y de los récords de Blitz y Racha.',
        'nav_leaderboard': 'Ranking de ejercicios',
    },
    'pt': {
        'training_another_round': 'Outra rodada',
        'training_start_challenge': 'Iniciar desafio', 'training_challenge_ready': 'Leia as regras e toque em Iniciar desafio quando estiver pronto.', 'practice_progress': 'Neste navegador', 'streak_current': 'Acertos neste desafio', 'nav_training': 'Treinar', 'training_title': 'Escolha como quer treinar',
        'training_intro': 'Aprender, criar um hábito ou superar seu recorde: cada modo tem um objetivo.',
        'training_modes': 'Os quatro treinos', 'training_start': 'Começar',
        'training_all': 'Todos os modos', 'training_rules': 'Regras e progresso',
        'training_progress': 'Seu progresso', 'training_guest': 'Experimente Prática, Blitz e Sequência sem conta. Entre para salvar seu progresso; o puzzle diário exige uma conta.',
        'training_today': 'Seu próximo treino', 'training_daily_ready': 'O desafio de hoje espera por você.',
        'training_daily_continue': 'Seu puzzle diário está em andamento. Você pode continuar.',
        'training_daily_done': 'Você concluiu a tentativa de hoje. Agora você pode praticar.',
        'training_recommended': 'Comece pela Prática guiada para conhecer os puzzles.',
        'training_continue': 'Continuar o diário', 'training_daily_result': 'Ver resultado de hoje',
        'training_record_blitz': 'Recorde Blitz · pontos', 'training_record_streak': 'Recorde Sequência · puzzles',
        'training_goal': 'Seu próximo objetivo', 'training_goal_help': 'Puzzles corretos para alcançar o próximo objetivo de treino.',
        'training_goal_done': 'Você concluiu todos os objetivos de quantidade de puzzles. Continue melhorando seus recordes.',
        'training_metrics': 'O que significa cada medida',
        'training_xp_help': 'XP reconhece puzzles resolvidos. A cada 100 XP você sobe um nível. O nível mede atividade, não força no xadrez.',
        'training_rating_help': 'O rating de puzzles sobe com acertos e cai com erros. Organiza o ranking de exercícios; é diferente do Elo de partidas.',
        'training_records_help': 'Blitz guarda pontos de rapidez e Sequência guarda acertos consecutivos. São recordes pessoais separados.',
        'training_sequence_help': 'A sequência geral conta acertos consecutivos entre seus treinos. Não representa dias de atividade nem o recorde do modo Sequência.',
        'training_account': 'Conta necessária', 'training_explore': 'Explorar treinos',
        'home_hub_title': 'Seu treino', 'home_hub_guest': 'Escolha um objetivo e conheça as regras de cada modo.',
        'home_hub_intro': 'Seu nível, rating de puzzles e sequência de acertos.',
        'home_hub_rating': 'Rating de puzzles', 'home_hub_streak': 'Acertos seguidos',
        'leaderboard_title': 'Ranking de exercícios', 'leaderboard_intro': 'Compare seu progresso resolvendo posições de xadrez. Ordenado pela pontuação dos exercícios; é diferente do Elo de partidas e dos recordes de Blitz e Sequência.',
        'nav_leaderboard': 'Ranking de exercícios',
    },
    'en': {
        'training_another_round': 'Another round',
        'training_start_challenge': 'Start challenge', 'training_challenge_ready': 'Read the rules and select Start challenge when you are ready.', 'practice_progress': 'In this browser', 'streak_current': 'Correct in this challenge', 'nav_training': 'Train', 'training_title': 'Choose how you want to train',
        'training_intro': 'Learn, build a habit or beat your record: each mode has its own purpose.',
        'training_modes': 'The four training modes', 'training_start': 'Start',
        'training_all': 'All modes', 'training_rules': 'Rules and progress',
        'training_progress': 'Your progress', 'training_guest': 'Try Practice, Blitz and Streak without an account. Sign in to save progress; the daily puzzle requires an account.',
        'training_today': 'Your next training session', 'training_daily_ready': 'Today’s challenge is waiting for you.',
        'training_daily_continue': 'Your daily puzzle is in progress. You can continue.',
        'training_daily_done': 'You completed today’s attempt. You can practice now.',
        'training_recommended': 'Start with Guided practice to learn how puzzles work.',
        'training_continue': 'Continue daily puzzle', 'training_daily_result': 'View today’s result',
        'training_record_blitz': 'Blitz record · points', 'training_record_streak': 'Streak record · puzzles',
        'training_goal': 'Your next goal', 'training_goal_help': 'Correct puzzles toward your next training milestone.',
        'training_goal_done': 'You completed every puzzle-count milestone. Keep improving your records.',
        'training_metrics': 'What each measure means',
        'training_xp_help': 'XP recognizes solved puzzles. Every 100 XP adds a level. Levels measure activity, not chess strength.',
        'training_rating_help': 'Puzzle rating rises with correct answers and falls with errors. It orders the puzzle leaderboard and is separate from game Elo.',
        'training_records_help': 'Blitz records speed points and Streak records consecutive correct puzzles. They are separate personal records.',
        'training_sequence_help': 'The overall sequence counts consecutive correct answers across training sessions. It is neither active days nor the Streak mode record.',
        'training_account': 'Account required', 'training_explore': 'Explore training',
        'home_hub_title': 'Your training', 'home_hub_guest': 'Choose a goal and learn how each mode works.',
        'home_hub_intro': 'Your level, puzzle rating and consecutive correct answers.',
        'home_hub_rating': 'Puzzle rating', 'home_hub_streak': 'Correct in a row',
        'leaderboard_title': 'Exercise leaderboard', 'leaderboard_intro': 'Compare your progress solving chess positions. Ordered by exercise rating; separate from game Elo and personal Blitz and Streak records.',
        'nav_leaderboard': 'Exercise leaderboard',
    },
}

for language, modes in MODE_CONTENT.items():
    for route, row in zip(MODE_ROUTES, modes):
        prefix = 'daily' if route == 'daily_puzzle' else route
        TRAINING_TEXTS[language][prefix + '_title'] = row[0]
        TRAINING_TEXTS[language][prefix + '_intro'] = row[2]


def training_navigation(request):
    from .i18n import current_language
    language = current_language(request)
    modes = [dict(route=route, title=row[0], goal=row[1], summary=row[2], rules=row[3], progress=row[4], account_required=route == 'daily_puzzle')
             for route, row in zip(MODE_ROUTES, MODE_CONTENT[language])]
    route = getattr(request.resolver_match, 'url_name', None)
    active = next((mode for mode in modes if mode['route'] == route), None)
    return {'training_modes': modes, 'active_training_mode': active, 'is_training_page': bool(active or route in ('training','daily_training','weekly_challenge','weekly_play'))}
