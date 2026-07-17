from django.contrib import admin
from django.db.models import Sum

from .models import BlitzBestResult, ChessGame, DailyPuzzle, DailyPuzzleAttempt, DailyVisit, StreakBestResult


@admin.register(ChessGame)
class ChessGameAdmin(admin.ModelAdmin):
    list_display = ('id', 'white_player', 'black_player', 'created_at', 'status', 'result')
    list_filter = ('status', 'result', 'category', 'created_at')
    search_fields = ('white_player', 'black_player', 'title')
    ordering = ('-created_at',)


@admin.register(DailyVisit)
class DailyVisitAdmin(admin.ModelAdmin):
    list_display = ('date', 'visits', 'total_visits')
    date_hierarchy = 'date'
    ordering = ('-date',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='visitas totales')
    def total_visits(self, obj):
        return DailyVisit.objects.aggregate(total=Sum('visits'))['total'] or 0


@admin.register(DailyPuzzle)
class DailyPuzzleAdmin(admin.ModelAdmin):
    list_display = ('date', 'puzzle_id', 'created_at')
    date_hierarchy = 'date'
    search_fields = ('puzzle_id',)
    ordering = ('-date',)


@admin.register(DailyPuzzleAttempt)
class DailyPuzzleAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'resultado', 'tiempo', 'daily_puzzle', 'completed_at')
    list_filter = ('resultado', 'date')
    date_hierarchy = 'date'
    search_fields = ('user__username', 'daily_puzzle__puzzle_id')
    ordering = ('-date', '-started_at')


@admin.register(BlitzBestResult)
class BlitzBestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'puzzles_resueltos', 'puzzles_correctos', 'puzzles_incorrectos', 'achieved_at')
    ordering = ('-score', '-puzzles_correctos', 'achieved_at')
    search_fields = ('user__username',)


@admin.register(StreakBestResult)
class StreakBestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'mejor_racha', 'puzzles_resueltos', 'achieved_at')
    ordering = ('-mejor_racha', '-puzzles_resueltos', 'achieved_at')
    search_fields = ('user__username',)
