"""Portable account/game export. Not a substitute for PostgreSQL PITR."""
import hashlib
from django.apps import apps

EXCLUDED_MODELS = ('contenttypes.contenttype', 'auth.permission', 'sessions.session', 'admin.logentry')


def data_models():
    return [model for model in apps.get_models() if model._meta.label_lower not in EXCLUDED_MODELS and model._meta.managed and not model._meta.proxy]


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
