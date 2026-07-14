from django.contrib import admin

from .models import Achievement, PlayerProfile, UserAchievement, UserPuzzleStats


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
        'xp_total',
        'nivel',
        'xp_del_nivel_actual',
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
        'xp_total',
        'nivel',
        'xp_del_nivel_actual',
        'created_at',
        'updated_at',
    )
    search_fields = ('user__username', 'ultimo_puzzle_resuelto')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'metric', 'threshold', 'sort_order')
    list_filter = ('metric',)
    search_fields = ('key', 'name', 'description')
    ordering = ('sort_order', 'id')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')
    list_filter = ('achievement', 'unlocked_at')
    search_fields = ('user__username', 'achievement__name')
