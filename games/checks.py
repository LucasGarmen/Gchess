import os

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.database)
def storage_check(app_configs, **kwargs):
    if os.environ.get('RENDER_EXTERNAL_HOSTNAME') and settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        return [Warning(
            'Render is using SQLite instead of PostgreSQL. Data may be lost on deploy or restart.',
            hint='Export the current service data before switching to a persistent PostgreSQL DATABASE_URL.',
            id='gchess.W001',
        )]
    return []


@register(Tags.database, deploy=True)
def persistent_database_check(app_configs, **kwargs):
    if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        return [Error(
            'Production requires a persistent PostgreSQL database.',
            hint='Configure DATABASE_URL after exporting existing data. Local development can keep SQLite.',
            id='gchess.E001',
        )]
    return []
