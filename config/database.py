"""Database configuration without exposing credentials in diagnostics."""
import dj_database_url


def database_from_url(database_url):
    try:
        config = dj_database_url.parse(database_url, conn_max_age=0)
    except (ValueError, TypeError) as exc:
        raise RuntimeError('DATABASE_URL is invalid; check the PostgreSQL connection URL.') from None
    if config['ENGINE'] != 'django.db.backends.postgresql':
        raise RuntimeError('DATABASE_URL must use postgres:// or postgresql://.')
    if not config.get('NAME') or not config.get('HOST'):
        raise RuntimeError('DATABASE_URL must include a database name and host.')
    # ASGI should not keep a persistent connection per worker thread.
    config.setdefault('OPTIONS', {}).setdefault('connect_timeout', 5)
    return config
