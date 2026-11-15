"""Shared D0 SQLite snapshot boundary. Not a filesystem or production trust root."""
from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3
import time

TABLES = frozenset({'run_heads','run_leases','run_admissions','sample_budgets',
    'sample_reservations','run_mutations','events','outbox','fences','run_audit',
    'run_lease_renewals','sample_settlements'})
NAMES = frozenset({'lifecycle.d0.sqlite','lifecycle-prefix.d0.sqlite'})
MAX_BYTES = 8 * 1024 * 1024
MAX_STEPS = 1_000_000


def _authorizer(action, arg1, arg2, database, source):
    if source is not None:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and arg1 in TABLES and (database == 'main' or (database is None and arg2 == '')):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and arg2 == 'count':
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _check_path(p, expected_name):
    if (expected_name not in NAMES or not p.is_absolute() or p.name != expected_name
            or not p.is_file() or p.resolve() != p or not 0 < p.stat().st_size <= MAX_BYTES
            or any(Path(str(p)+suffix).exists() or Path(str(p)+suffix).is_symlink()
                   for suffix in ('-wal','-shm','-journal'))):
        raise ValueError('D0_LIFECYCLE_SNAPSHOT_PATH_HOLD')


@contextmanager
def lifecycle_snapshot(path, expected_name):
    """Read a disposable fixed-profile database; reject sidecars and indirect reads."""
    p = Path(path)
    _check_path(p, expected_name)
    with closing(sqlite3.connect(p.as_uri()+'?mode=ro', uri=True, timeout=1)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA query_only').fetchone() != (1,) or db.execute('PRAGMA trusted_schema').fetchone() != (0,):
            raise ValueError('D0_LIFECYCLE_SNAPSHOT_GUARD_HOLD')
        if db.execute('PRAGMA journal_mode').fetchone() != ('delete',):
            raise ValueError('D0_LIFECYCLE_SNAPSHOT_JOURNAL_HOLD')
        db.execute('BEGIN')
        deadline = time.monotonic() + 2.0
        # The schema read establishes the same SQLite transaction snapshot as the data reads.
        rows = db.execute('SELECT name,type FROM main.sqlite_schema').fetchall()
        kinds = {name: kind for name,kind in rows if name in TABLES}
        if kinds != dict.fromkeys(TABLES,'table') or any(kind in ('view','trigger') for _,kind in rows):
            raise ValueError('D0_LIFECYCLE_SNAPSHOT_SCHEMA_HOLD')
        ordinary = {name for schema,name,kind,*_ in db.execute('PRAGMA table_list')
                    if schema == 'main' and kind == 'table'}
        if not TABLES <= ordinary:
            raise ValueError('D0_LIFECYCLE_SNAPSHOT_SCHEMA_HOLD')
        db.set_authorizer(_authorizer)
        steps = 0
        def progress():
            nonlocal steps
            steps += 1000
            return int(steps >= MAX_STEPS or time.monotonic() >= deadline)
        db.set_progress_handler(progress,1000)
        try:
            yield db
            _check_path(p, expected_name)
            if time.monotonic() >= deadline:
                raise ValueError('D0_LIFECYCLE_SNAPSHOT_DEADLINE_HOLD')
        finally:
            db.set_progress_handler(None,0)
            db.set_authorizer(None)
            db.rollback()


def require_single_head(cursor, key):
    """Check uniqueness even if a candidate database lacks its expected PK."""
    cursor.execute('SELECT count(*) FROM t1_candidate.run_heads WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND run_id=%s',key)
    if cursor.fetchone() != (1,) or cursor.fetchone() is not None:
        raise ValueError('D0_LIFECYCLE_HEAD_COUNT_HOLD')
