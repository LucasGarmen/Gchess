import gzip
import json
import os
import tempfile
from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection, transaction
from django.utils import timezone

from games.data_export import EXCLUDED_MODELS, data_models, file_hash


class Command(BaseCommand):
    help = 'Export portable user/game data and a checksum manifest. Store both files outside the service.'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True, help='New .json.gz output path (never overwrites).')

    def handle(self, *args, **options):
        output = Path(options['output']).resolve()
        manifest = Path(str(output) + '.manifest.json')
        if not str(output).endswith('.json.gz'):
            raise CommandError('Output must end with .json.gz.')
        if output.exists() or manifest.exists():
            raise CommandError('Output already exists; choose a new filename.')
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=output.parent, suffix='.tmp')
        os.close(fd)
        temporary = Path(temporary)
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                counts = {model._meta.label_lower: model._base_manager.count() for model in data_models()}
                with gzip.open(temporary, 'wt', encoding='utf-8') as stream:
                    call_command('dumpdata', exclude=EXCLUDED_MODELS, natural_foreign=True,
                                 natural_primary=True, use_base_manager=True, stdout=stream, verbosity=0)
            # Exclusive creation prevents accidental replacement of another export.
            archive_fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(archive_fd, 'wb') as destination, temporary.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    destination.write(chunk)
            record = {'format_version': 1, 'created_at': timezone.now().isoformat(),
                      'sha256': file_hash(output), 'counts': counts,
                      'excluded_models': list(EXCLUDED_MODELS)}
            manifest_fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(manifest_fd, 'w', encoding='utf-8') as stream:
                json.dump(record, stream, indent=2)
            output.chmod(0o600)
            manifest.chmod(0o600)
        except Exception as exc:
            # Filesystem/DB messages can contain credentials or personal data.
            raise CommandError('Export failed. Preserve the source database and check access/configuration.') from None
        finally:
            temporary.unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f'Export complete: {sum(counts.values())} records. Keep the archive and manifest together.'))
