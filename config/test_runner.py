"""Protect application databases from accidental Django test runs."""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.runner import DiscoverRunner


class LocalOnlyTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        # Check every alias before Django can create, reuse or destroy any database.
        for config in settings.DATABASES.values():
            if config.get('ENGINE') != 'django.db.backends.sqlite3':
                raise ImproperlyConfigured(
                    'Tests are restricted to local SQLite databases. '
                    'Run python manage.py test --settings=config.test_settings. '
                    'No test database was created or deleted.'
                )
        return super().setup_databases(**kwargs)
