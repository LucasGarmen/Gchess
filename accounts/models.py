from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'estadistica de puzzles'
        verbose_name_plural = 'estadisticas de puzzles'

    def __str__(self):
        return f"Estadisticas de puzzles de {self.user.username}"

    def registrar_puzzle(self, puzzle_id, correcto, tiempo=None):
        # Centraliza los calculos para que la vista solo indique el resultado del puzzle.
        tiempo = tiempo or timedelta()
        if tiempo < timedelta():
            tiempo = timedelta()

        self.puzzles_resueltos += 1
        self.ultimo_puzzle_resuelto = str(puzzle_id or '')
        self.fecha_ultimo_entrenamiento = timezone.now()
        self.tiempo_total += tiempo

        if correcto:
            self.puzzles_correctos += 1
            self.racha_actual += 1
            self.mejor_racha = max(self.mejor_racha, self.racha_actual)
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
            'updated_at',
        ])
