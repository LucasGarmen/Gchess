from django.apps import AppConfig


class GamesConfig(AppConfig):
    name = 'games'

    def ready(self):
        from . import checks  # Register storage diagnostics without connecting to the DB.
        from . import tournament_signals
