from django.core.management import BaseCommand, CommandError
from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Verify PostgreSQL connectivity and applied migrations without exposing credentials.'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            raise CommandError('Production persistence is not ready: configure PostgreSQL DATABASE_URL.')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            executor = MigrationExecutor(connection)
            pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        except DatabaseError:
            raise CommandError('Database connection failed. Check the internal URL and database availability.') from None
        if pending:
            raise CommandError('Database has pending migrations. Apply them before accepting traffic.')
        self.stdout.write(self.style.SUCCESS('PostgreSQL connected; all migrations applied.'))
