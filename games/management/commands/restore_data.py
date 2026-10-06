import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from games.data_export import data_models, file_hash
from accounts.models import Achievement, ACHIEVEMENT_DEFINITIONS


class Command(BaseCommand):
    help = 'Restore a verified export into an empty, migrated database. Refuses existing application data.'

    def add_arguments(self, parser):
        parser.add_argument('archive')

    def handle(self, *args, **options):
        archive = Path(options['archive']).resolve()
        try:
            manifest = json.loads(Path(str(archive) + '.manifest.json').read_text(encoding='utf-8'))
            if manifest.get('format_version') != 1 or file_hash(archive) != manifest['sha256']:
                raise ValueError('Invalid archive')
            expected = manifest['counts']
            models = data_models()
            if set(expected) != {model._meta.label_lower for model in models}:
                raise ValueError('Schema mismatch')
            if any(not isinstance(count, int) or count < 0 for count in expected.values()):
                raise ValueError('Invalid counts')
        except (OSError, ValueError, KeyError, TypeError):
            raise CommandError('Archive/manifest invalid, modified, or incompatible. No data was imported.') from None
        with transaction.atomic():
            if any(model._base_manager.exists() for model in models if model._meta.label_lower != 'accounts.achievement'):
                raise CommandError('Target database contains data. Use a separate empty database; nothing was overwritten.')
            baseline = {key: (metric, threshold, name, description, order) for key, metric, threshold, name, description, order in ACHIEVEMENT_DEFINITIONS}
            for row in Achievement.objects.all():
                if baseline.get(row.key) != (row.metric, row.threshold, row.name, row.description, row.sort_order):
                    raise CommandError('Target contains custom achievements; use an empty migrated database.')
            try:
                # Migrations seed this reference catalog, but it is not user data.
                Achievement.objects.all().delete()
                call_command('loaddata', str(archive), verbosity=0)
                actual = {model._meta.label_lower: model._base_manager.count() for model in models}
                if actual != expected:
                    raise ValueError('Counts do not match')
            except Exception:
                raise CommandError('Restore failed; imported changes were rolled back. Check schema compatibility.') from None
        self.stdout.write(self.style.SUCCESS('Restore verified: account/game record counts match the manifest.'))
