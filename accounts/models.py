from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

XP_PER_LEVEL = 100
PUZZLE_RATING_START = 800
PUZZLE_RATING_FLOOR = 100
# Los mates mas profundos mueven mas rating porque demandan mas calculo.
PUZZLE_RATING_DELTAS_BY_MATE_IN = {
    1: 8,
    2: 12,
    3: 16,
    4: 24,
}

ACHIEVEMENT_DEFINITIONS = (
    ('first_puzzle', 'puzzles_correctos', 1, 'Primer puzzle', 'Resuelve tu primer puzzle.', 10),
    ('puzzles_10', 'puzzles_correctos', 10, '10 puzzles', 'Resuelve 10 puzzles.', 20),
    ('puzzles_50', 'puzzles_correctos', 50, '50 puzzles', 'Resuelve 50 puzzles.', 30),
    ('puzzles_100', 'puzzles_correctos', 100, '100 puzzles', 'Resuelve 100 puzzles.', 40),
    ('puzzles_500', 'puzzles_correctos', 500, '500 puzzles', 'Resuelve 500 puzzles.', 50),
    ('puzzles_1000', 'puzzles_correctos', 1000, '1000 puzzles', 'Resuelve 1000 puzzles.', 60),
    ('streak_10', 'mejor_racha', 10, '10 correctos seguidos', 'Consigue una racha de 10 aciertos.', 70),
    ('streak_25', 'mejor_racha', 25, '25 correctos seguidos', 'Consigue una racha de 25 aciertos.', 80),
    ('streak_50', 'mejor_racha', 50, '50 correctos seguidos', 'Consigue una racha de 50 aciertos.', 90),
    ('xp_1000', 'xp_total', 1000, '1000 XP', 'Acumula 1000 XP.', 100),
    ('level_10', 'nivel', 10, 'Nivel 10', 'Alcanza el nivel 10.', 110),
    ('level_25', 'nivel', 25, 'Nivel 25', 'Alcanza el nivel 25.', 120),
    ('level_50', 'nivel', 50, 'Nivel 50', 'Alcanza el nivel 50.', 130),
)

ACHIEVEMENT_METRIC_CHOICES = (
    ('puzzles_correctos', 'Puzzles correctos'),
    ('mejor_racha', 'Mejor racha'),
    ('xp_total', 'XP total'),
    ('nivel', 'Nivel'),
)


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    elo = models.IntegerField(default=1200)

    def __str__(self):
        return f"{self.user.username} ({self.elo})"


class UserPuzzleStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='puzzle_stats')
    puzzles_resueltos = models.PositiveIntegerField(default=0)
    puzzles_correctos = models.PositiveIntegerField(default=0)
    puzzles_incorrectos = models.PositiveIntegerField(default=0)
    porcentaje_de_aciertos = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tiempo_total = models.DurationField(default=timedelta)
    tiempo_promedio = models.DurationField(default=timedelta)
    mejor_racha = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)
    ultimo_puzzle_resuelto = models.CharField(max_length=120, blank=True)
    fecha_ultimo_entrenamiento = models.DateTimeField(blank=True, null=True)
    xp_total = models.PositiveIntegerField(default=0)
    nivel = models.PositiveIntegerField(default=1)
    xp_del_nivel_actual = models.PositiveIntegerField(default=0)
    puzzle_rating = models.PositiveIntegerField(default=PUZZLE_RATING_START)
    ultimo_cambio_rating = models.IntegerField(default=0)
    mejor_rating = models.PositiveIntegerField(default=PUZZLE_RATING_START)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'estadistica de puzzles'
        verbose_name_plural = 'estadisticas de puzzles'

    def __str__(self):
        return f"Estadisticas de puzzles de {self.user.username}"

    @property
    def xp_restante(self):
        restante = XP_PER_LEVEL - self.xp_del_nivel_actual
        return restante if restante > 0 else XP_PER_LEVEL

    @property
    def porcentaje_xp_nivel(self):
        return min(100, int((self.xp_del_nivel_actual / XP_PER_LEVEL) * 100))

    def aplicar_rating_puzzle(self, correcto, mate_in=None):
        rating_delta = puzzle_rating_delta_for_mate_in(mate_in)

        if not correcto:
            rating_delta = -rating_delta

        self.ultimo_cambio_rating = rating_delta
        self.puzzle_rating = max(PUZZLE_RATING_FLOOR, self.puzzle_rating + rating_delta)
        self.mejor_rating = max(self.mejor_rating, self.puzzle_rating)

    def registrar_puzzle(self, puzzle_id, correcto, tiempo=None, xp_ganado=0, mate_in=None):
        # Centraliza los calculos para que la vista solo indique el resultado del puzzle.
        tiempo = tiempo or timedelta()
        if tiempo < timedelta():
            tiempo = timedelta()

        xp_ganado = max(0, int(xp_ganado or 0))
        self.puzzles_resueltos += 1
        self.ultimo_puzzle_resuelto = str(puzzle_id or '')
        self.fecha_ultimo_entrenamiento = timezone.now()
        self.tiempo_total += tiempo
        self.aplicar_rating_puzzle(correcto, mate_in)

        if correcto:
            self.puzzles_correctos += 1
            self.racha_actual += 1
            self.mejor_racha = max(self.mejor_racha, self.racha_actual)
            self.xp_total += xp_ganado
            self.nivel = (self.xp_total // XP_PER_LEVEL) + 1
            self.xp_del_nivel_actual = self.xp_total % XP_PER_LEVEL
        else:
            self.puzzles_incorrectos += 1
            self.racha_actual = 0

        self.tiempo_promedio = self.tiempo_total / self.puzzles_resueltos
        self.porcentaje_de_aciertos = (
            (Decimal(self.puzzles_correctos) * Decimal('100') / Decimal(self.puzzles_resueltos))
            .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
        self.save(update_fields=[
            'puzzles_resueltos',
            'puzzles_correctos',
            'puzzles_incorrectos',
            'porcentaje_de_aciertos',
            'tiempo_total',
            'tiempo_promedio',
            'mejor_racha',
            'racha_actual',
            'ultimo_puzzle_resuelto',
            'fecha_ultimo_entrenamiento',
            'xp_total',
            'nivel',
            'xp_del_nivel_actual',
            'puzzle_rating',
            'ultimo_cambio_rating',
            'mejor_rating',
            'updated_at',
        ])
        unlock_achievements_for_stats(self)


class Achievement(models.Model):
    key = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=220)
    metric = models.CharField(max_length=40, choices=ACHIEVEMENT_METRIC_CHOICES)
    threshold = models.PositiveIntegerField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'logro'
        verbose_name_plural = 'logros'

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_unlocks')
    unlocked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-unlocked_at', 'achievement__sort_order']
        unique_together = [('user', 'achievement')]
        verbose_name = 'logro de usuario'
        verbose_name_plural = 'logros de usuarios'

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


def ensure_default_achievements():
    expected_keys = [achievement[0] for achievement in ACHIEVEMENT_DEFINITIONS]
    if Achievement.objects.filter(key__in=expected_keys).count() == len(expected_keys):
        return

    for key, metric, threshold, name, description, sort_order in ACHIEVEMENT_DEFINITIONS:
        Achievement.objects.update_or_create(
            key=key,
            defaults={
                'name': name,
                'description': description,
                'metric': metric,
                'threshold': threshold,
                'sort_order': sort_order,
            },
        )


def achievement_metric_value(stats, achievement):
    return int(getattr(stats, achievement.metric, 0) or 0)


def puzzle_rating_delta_for_mate_in(mate_in):
    try:
        mate_in = int(mate_in)
    except (TypeError, ValueError):
        mate_in = 1

    if mate_in <= 1:
        return PUZZLE_RATING_DELTAS_BY_MATE_IN[1]

    return PUZZLE_RATING_DELTAS_BY_MATE_IN.get(mate_in, 32)


def unlock_achievements_for_stats(stats):
    ensure_default_achievements()

    unlocked_ids = set(
        UserAchievement.objects
        .filter(user=stats.user)
        .values_list('achievement_id', flat=True)
    )
    now = timezone.now()
    new_unlocks = []

    for achievement in Achievement.objects.all():
        if achievement.id in unlocked_ids:
            continue

        if achievement_metric_value(stats, achievement) >= achievement.threshold:
            new_unlocks.append(UserAchievement(
                user=stats.user,
                achievement=achievement,
                unlocked_at=now,
            ))

    if new_unlocks:
        UserAchievement.objects.bulk_create(new_unlocks, ignore_conflicts=True)

    return new_unlocks
