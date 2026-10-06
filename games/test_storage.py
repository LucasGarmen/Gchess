import gzip
import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command, CommandError
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings

from accounts.models import PlayerProfile, UserPuzzleStats
from config.database import database_from_url
from games.checks import storage_check, persistent_database_check
from games.models import ChessGame, Move, DailyVisit


class DatabaseConfigurationTests(SimpleTestCase):
    def test_encoded_credentials_and_tls(self):
        config = database_from_url('postgresql://name%40host:p%40ss%2Fword@db.internal:5432/gchess?sslmode=require')
        self.assertEqual(config['USER'], 'name@host')
        self.assertEqual(config['PASSWORD'], 'p@ss/word')
        self.assertEqual(config['OPTIONS']['sslmode'], 'require')
        self.assertEqual(config['OPTIONS']['connect_timeout'], 5)
        self.assertEqual(config['CONN_MAX_AGE'], 0)

    def test_invalid_urls_never_echo_credentials(self):
        for url in ('sqlite:///private-secret', 'postgres://name:private-secret@host:bad/db', 'postgres://name:private-secret@host/'):
            with self.assertRaises(RuntimeError) as raised:
                database_from_url(url)
            self.assertNotIn('private-secret', str(raised.exception))

    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}})
    def test_render_warns_and_deploy_check_blocks_ephemeral_database(self):
        with patch.dict('os.environ', {'RENDER_EXTERNAL_HOSTNAME': 'gchess.example'}):
            self.assertEqual(storage_check(None)[0].id, 'gchess.W001')
        self.assertEqual(persistent_database_check(None)[0].id, 'gchess.E001')

    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.postgresql'}})
    def test_postgresql_passes_storage_configuration_check(self):
        self.assertEqual(persistent_database_check(None), [])


class StorageTests(TestCase):
    def test_health_has_no_visit_or_session_side_effects(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertFalse(DailyVisit.objects.exists())
        self.assertNotIn('sessionid', response.cookies)

    def test_health_hides_database_error_details(self):
        with patch('games.health.connection.cursor', side_effect=OperationalError('private-password')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private-password', response.content.decode())

    def test_export_restore_accounts_games_moves_and_progress(self):
        user = User.objects.create_user('export-test', password='test-password')
        profile = PlayerProfile.objects.create(user=user, elo=1450)
        stats = UserPuzzleStats.objects.create(user=user, xp_total=250)
        group = Group.objects.create(name='players')
        permission = Permission.objects.first()
        group.permissions.add(permission)
        user.groups.add(group)
        game = ChessGame.objects.create(owner=user, white_user=user, white_player='White', black_player='Black')
        Move.objects.create(game=game, move_number=1, from_square='e2', to_square='e4', piece_type='pawn', piece_color='white')
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'test.json.gz'
            call_command('export_data', output=str(archive), stdout=StringIO())
            with gzip.open(archive, 'rt', encoding='utf-8') as stream:
                records = json.load(stream)
            self.assertNotIn('sessions.session', {record['model'] for record in records})
            with self.assertRaises(CommandError):
                call_command('export_data', output=str(archive), stdout=StringIO())
            with self.assertRaises(CommandError):
                call_command('restore_data', str(archive), stdout=StringIO())
            self.assertTrue(User.objects.filter(pk=user.pk).exists())
            # Only the disposable test database is emptied for this round trip.
            User.objects.all().delete()
            Group.objects.all().delete()
            call_command('restore_data', str(archive), stdout=StringIO())
            restored = User.objects.get(username='export-test')
            self.assertTrue(restored.check_password('test-password'))
            self.assertEqual(restored.player_profile.elo, 1450)
            self.assertEqual(restored.puzzle_stats.xp_total, 250)
            self.assertTrue(restored.groups.get().permissions.filter(pk=permission.pk).exists())
            self.assertEqual(ChessGame.objects.get().owner, restored)
            self.assertEqual(Move.objects.get().to_square, 'e4')

    def test_tampered_export_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'test.json.gz'
            call_command('export_data', output=str(archive), stdout=StringIO())
            archive.write_bytes(b'tampered')
            with self.assertRaises(CommandError):
                call_command('restore_data', str(archive), stdout=StringIO())
            self.assertFalse(User.objects.exists())
