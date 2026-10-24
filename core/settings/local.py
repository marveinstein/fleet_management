from .base import *
from django.db.backends.signals import connection_created
from django.dispatch import receiver

DEBUG = True

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # 20 second wait on lock instead of immediate fail
        }
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """
    Optimize SQLite for high-throughput concurrent telemetry ingestion.
    WAL mode allows simultaneous readers and writers.
    """
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 20000;')
            cursor.execute('PRAGMA cache_size = -64000;')  # 64MB memory page cache
            cursor.execute('PRAGMA temp_store = MEMORY;')
            cursor.execute('PRAGMA foreign_keys = ON;')
