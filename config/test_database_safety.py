"""Regression checks that never connect to an external database."""
import os
from pathlib import Path
import runpy
import sys
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured


from config.test_runner import LocalOnlyTestRunner


class DatabaseSafetyTests(TestCase):
    def test_plain_test_command_uses_isolated_settings(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sys, 'argv', ['manage.py', 'test']):
            with patch('django.core.management.execute_from_command_line') as execute:
                runpy.run_path(str(Path(__file__).resolve().parents[1] / 'manage.py'), run_name='__main__')
                self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], 'config.test_settings')
                execute.assert_called_once()

    def test_server_command_keeps_normal_settings(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sys, 'argv', ['manage.py', 'runserver']):
            with patch('django.core.management.execute_from_command_line'):
                runpy.run_path(str(Path(__file__).resolve().parents[1] / 'manage.py'), run_name='__main__')
                self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], 'config.settings')

    def test_remote_alias_blocks_before_django_database_setup(self):
        databases = {
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'other': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'example'},
        }
        with patch('config.test_runner.settings.DATABASES', databases):
            with patch('django.test.runner.DiscoverRunner.setup_databases') as setup:
                with self.assertRaisesRegex(ImproperlyConfigured, 'restricted to local SQLite'):
                    LocalOnlyTestRunner(verbosity=0).setup_databases()
                setup.assert_not_called()

    def test_local_sqlite_reaches_normal_test_setup(self):
        with patch('config.test_runner.settings.DATABASES', {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}):
            with patch('django.test.runner.DiscoverRunner.setup_databases', return_value='local') as setup:
                self.assertEqual(LocalOnlyTestRunner(verbosity=0).setup_databases(), 'local')
                setup.assert_called_once()

