"""W4 synthetic in-memory event readback; never the canonical T1 store."""
import json
import sqlite3
from contextlib import closing
from hashlib import sha256


def inspect_sqlite_replay(events: list[dict]) -> dict:
    result = {'reason': 'SQLITE_SAMPLE_INVALID', 'rows': None, 'persistent': False,
              'canonical_commit': False, 'dispatch_allowed': False}
    if not isinstance(events, list) or not 1 <= len(events) <= 100:
        return result
    rows = []
    try:
        for i, event in enumerate(events, 1):
            if (not isinstance(event, dict) or type(event.get('seq')) is not int
                    or event['seq'] != i or not isinstance(event.get('event_id'), str)
                    or not 1 <= len(event['event_id']) <= 128
                    or (event.get('tenant_id'), event.get('environment_id')) != ('synthetic-tenant', 'A0_SAMPLE_ONLY')):
                return result
            payload = json.dumps(event, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
            if len(payload) > 8192:
                return result
            rows.append((i, event['event_id'], payload, sha256(payload.encode('ascii')).hexdigest()))
    except (ValueError, TypeError, RecursionError):
        return result
    with closing(sqlite3.connect(':memory:')) as db:
        try:
            db.execute('CREATE TABLE sample_event(seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, body TEXT NOT NULL, digest TEXT NOT NULL)')
            db.executemany('INSERT INTO sample_event VALUES (?, ?, ?, ?)', rows)
            actual = db.execute('SELECT seq, event_id, body, digest FROM sample_event ORDER BY seq').fetchall()
            if actual != rows:
                raise ValueError('readback mismatch')
        except (sqlite3.Error, ValueError):
            db.rollback()
            return {**result, 'reason': 'SQLITE_SAMPLE_ROLLBACK'}
        finally:
            # The sample is always rolled back, including the successful path.
            db.rollback()
    return {**result, 'reason': 'SQLITE_MEMORY_READBACK_ONLY', 'rows': len(rows)}
