from django.contrib import admin

from .models import PlayerProfile, UserPuzzleStats


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'elo')
    search_fields = ('user__username',)


@admin.register(UserPuzzleStats)
class UserPuzzleStatsAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'puzzles_resueltos',
        'puzzles_correctos',
        'puzzles_incorrectos',
        'porcentaje_de_aciertos',
        'racha_actual',
        'mejor_racha',
        'fecha_ultimo_entrenamiento',
    )
    readonly_fields = (
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
        'created_at',
        'updated_at',
    )
    search_fields = ('user__username', 'ultimo_puzzle_resuelto')
