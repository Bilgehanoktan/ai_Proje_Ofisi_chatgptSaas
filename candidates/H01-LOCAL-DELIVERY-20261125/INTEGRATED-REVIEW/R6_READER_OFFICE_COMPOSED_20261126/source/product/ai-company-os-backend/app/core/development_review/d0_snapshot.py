"""Shared D0 fixture snapshot. A local read-only guard, not independent authority."""
from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3
import time

NAMES = frozenset({'lifecycle.d0.sqlite', 'lifecycle-prefix.d0.sqlite'})
MAX_BYTES = 8 * 1024 * 1024


class ReadCursor:
    """Only internal SELECT statements, with a narrow SQLite dialect adapter."""
    def __init__(self, db):
        self.cursor = db.cursor()

    def execute(self, sql, params=()):
        if (type(sql) is not str or not sql.startswith('SELECT ')
                or ';' in sql or 'FOR UPDATE' in sql):
            raise ValueError('D0_SNAPSHOT_SELECT_ONLY')
        return self.cursor.execute(sql.replace('t1_candidate.', '').replace('%s', '?'), params)

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        self.cursor.close()


def _check_path(p, name):
    if (name not in NAMES or not p.is_absolute() or p.name != name
            or not p.is_file() or p.resolve() != p
            or not 0 < p.stat().st_size <= MAX_BYTES):
        raise ValueError('D0_SNAPSHOT_PATH_HOLD')
    # A closed exported sample is required; do not read a live WAL/journal fixture.
    for suffix in ('-wal', '-shm', '-journal'):
        sidecar = Path(str(p) + suffix)
        if sidecar.exists() or sidecar.is_symlink():
            raise ValueError('D0_SNAPSHOT_SIDECAR_HOLD')


@contextmanager
def open_d0_snapshot(path, name):
    """Own one read transaction; never create, repair, migrate or open live stores.

    Deadline limits SQLite VM work, not wall-clock freshness or a security proof.
    The caller must use a trusted local fixture directory (TOCTOU is not solved).
    """
    p = Path(path)
    _check_path(p, name)
    with closing(sqlite3.connect(p.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA query_only').fetchone() != (1,) or db.execute('PRAGMA trusted_schema').fetchone() != (0,):
            raise ValueError('D0_SNAPSHOT_GUARD_HOLD')
        db.execute('BEGIN')
        deadline = time.monotonic() + 2.0
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        cursor = ReadCursor(db)
        try:
            yield cursor
            _check_path(p, name)
            if time.monotonic() >= deadline:
                raise ValueError('D0_SNAPSHOT_DEADLINE_HOLD')
        finally:
            cursor.close()
            db.set_progress_handler(None, 0)
            db.rollback()
