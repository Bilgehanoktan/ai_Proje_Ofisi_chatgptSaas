"""Bounded D0 SQLite read boundary for admission and pair markers; not a trust root."""
from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3

MAX_BYTES = 8 * 1024 * 1024
MAX_STEPS = 1_000_000
ADMISSION_TABLES = frozenset({'meta','membership','sample_budget','sample_event',
                              'sample_admission','sample_audit','sample_outbox'})
PAIR_TABLES = frozenset({'sample_pair'})


@contextmanager
def guarded_read(path, suffix, tables):
    if (suffix, tables) not in (('.admission.d0.sqlite', ADMISSION_TABLES),
                                ('.admission.d0.sqlite', PAIR_TABLES),
                                ('.workbench.d0.sqlite', PAIR_TABLES)):
        raise ValueError('D0_PAIRED_READ_PROFILE_HOLD')
    p = Path(path)
    if not p.name.endswith(suffix) or p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise ValueError('D0_PAIRED_READ_PATH_HOLD')
    resolved = p.resolve()
    if any(Path(str(resolved)+s).exists() or Path(str(resolved)+s).is_symlink()
           for s in ('-wal','-shm','-journal')):
        raise ValueError('D0_PAIRED_READ_SIDECAR_HOLD')
    with closing(sqlite3.connect(resolved.as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA trusted_schema').fetchone() != (0,):
            raise ValueError('D0_PAIRED_READ_SCHEMA_HOLD')
        if db.execute('PRAGMA journal_mode').fetchone() != ('delete',):
            raise ValueError('D0_PAIRED_READ_JOURNAL_HOLD')
        db.execute('BEGIN')
        steps = 0
        def progress():
            nonlocal steps
            steps += 1000
            return int(steps >= MAX_STEPS)
        db.set_progress_handler(progress,1000)
        try:
            rows = db.execute('SELECT name,type FROM main.sqlite_schema').fetchall()
            kinds = {name:kind for name,kind in rows if name in tables}
            ordinary = {name for schema,name,kind,*_ in db.execute('PRAGMA table_list')
                        if schema == 'main' and kind == 'table'}
            if (kinds != dict.fromkeys(tables,'table') or not tables <= ordinary
                    or any(kind in ('view','trigger') for _,kind in rows)):
                raise ValueError('D0_PAIRED_READ_SCHEMA_HOLD')
            def authorizer(action, arg1, arg2, database, source):
                if source is not None: return sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_SELECT: return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and arg1 in tables and database == 'main':
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY
            db.set_authorizer(authorizer)
            yield db
        finally:
            db.set_authorizer(None)
            db.set_progress_handler(None,0)
