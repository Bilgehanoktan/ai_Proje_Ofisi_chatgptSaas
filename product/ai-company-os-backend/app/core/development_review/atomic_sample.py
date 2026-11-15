"""D0 atomicity lab. No canonical T1, provider, dispatch or security authority."""
from contextlib import contextmanager, closing
from pathlib import Path
import sqlite3

SCOPE = ('D0_ATOMIC_SAMPLE', 'synthetic-tenant', 'synthetic-company')
DDL = """
CREATE TABLE meta(profile TEXT PRIMARY KEY CHECK(profile='D0_ATOMIC_SAMPLE'), tenant TEXT NOT NULL CHECK(tenant='synthetic-tenant'), company TEXT NOT NULL CHECK(company='synthetic-company'));
INSERT INTO meta VALUES('D0_ATOMIC_SAMPLE','synthetic-tenant','synthetic-company');
CREATE TABLE head(id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL CHECK(version>=0), state TEXT NOT NULL CHECK(state IN ('PENDING','OBSERVED')));
CREATE TABLE lease(id INTEGER PRIMARY KEY REFERENCES head(id), holder TEXT NOT NULL, fence INTEGER NOT NULL CHECK(fence>0), tick INTEGER NOT NULL, expires INTEGER NOT NULL CHECK(expires>tick));
CREATE TABLE event(command_id TEXT PRIMARY KEY, version INTEGER UNIQUE NOT NULL, holder TEXT NOT NULL, fence INTEGER NOT NULL, tick INTEGER NOT NULL);
CREATE TABLE audit(command_id TEXT PRIMARY KEY REFERENCES event(command_id), decision TEXT NOT NULL CHECK(decision='SAMPLE_ONLY'));
CREATE TABLE outbox(command_id TEXT PRIMARY KEY REFERENCES event(command_id), status TEXT NOT NULL CHECK(status='DENY'));
INSERT INTO head VALUES(1,0,'PENDING');
"""


def integer(n):
    return type(n) is int and 0 <= n < 2**63-1


def holder_ok(s):
    return isinstance(s, str) and s.startswith('demo-') and 5 < len(s) <= 128 and s.isascii() and all(c.isalnum() or c in '-_.' for c in s)


class AtomicSample:
    def __init__(self, path, tenant='synthetic-tenant', company='synthetic-company'):
        if (tenant, company) != SCOPE[1:]:
            raise ValueError('SAMPLE_SCOPE_DENY')
        self.path = Path(path)
        if not self.path.name.endswith('.atomic.d0.sqlite') or self.path.is_symlink():
            raise ValueError('SAMPLE_PATH_INVALID')

    def create(self):
        with self.path.open('xb'):
            pass
        try:
            with closing(sqlite3.connect(self.path)) as db:
                db.executescript(DDL)
                db.commit()
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise

    @contextmanager
    def _db(self):
        if not self.path.is_file() or self.path.is_symlink():
            raise ValueError('SAMPLE_DB_MISSING')
        with closing(sqlite3.connect(self.path.resolve().as_uri()+'?mode=rw', uri=True)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT profile,tenant,company FROM meta').fetchall() != [SCOPE]:
                    raise ValueError('SAMPLE_DB_SCOPE_MISMATCH')
                yield db

    def renew(self, holder, fence, tick, ttl):
        """Acquire if absent/expired (fence=None); otherwise heartbeat with exact fence."""
        if not holder_ok(holder) or not integer(tick) or not integer(ttl) or not 1 <= ttl <= 100 or tick+ttl >= 2**63-1 or (fence is not None and (not integer(fence) or fence==0)):
            raise ValueError('SAMPLE_LEASE_INVALID')
        with self._db() as db:
            if db.execute('SELECT state FROM head WHERE id=1').fetchone() != ('PENDING',):
                raise ValueError('SAMPLE_TERMINAL')
            old = db.execute('SELECT holder,fence,tick,expires FROM lease WHERE id=1').fetchone()
            if old and tick < old[2]:
                raise ValueError('SAMPLE_CLOCK_REGRESSION')
            if old and tick < old[3]:
                if (holder,fence) != old[:2] or tick <= old[2]:
                    raise ValueError('SAMPLE_LEASE_BUSY_OR_STALE')
                generation = old[1]
                expires = max(old[3],tick+ttl)
            else:
                if fence is not None:
                    raise ValueError('SAMPLE_LEASE_EXPIRED')
                generation = old[1]+1 if old else 1
                expires = tick+ttl
                if not integer(generation):
                    raise ValueError('SAMPLE_FENCE_EXHAUSTED')
            db.execute('INSERT INTO lease VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET holder=excluded.holder,fence=excluded.fence,tick=excluded.tick,expires=excluded.expires',(holder,generation,tick,expires))
            return generation

    def observe(self, command, holder, fence, tick, version):
        if not holder_ok(command) or not holder_ok(holder) or not all(integer(x) for x in (fence,tick,version)) or not fence or version >= 2**63-2:
            raise ValueError('SAMPLE_COMMAND_INVALID')
        with self._db() as db:
            prior = db.execute('SELECT version,holder,fence,tick FROM event WHERE command_id=?',(command,)).fetchone()
            if prior:
                if prior != (version+1,holder,fence,tick):
                    raise ValueError('SAMPLE_IDEMPOTENCY_CONFLICT')
                return 'DUPLICATE_IGNORED'
            lease = db.execute('SELECT holder,fence,tick,expires FROM lease WHERE id=1').fetchone()
            if not lease or lease[:2] != (holder,fence) or not lease[2] <= tick < lease[3]:
                raise ValueError('SAMPLE_LEASE_STALE')
            if db.execute("UPDATE head SET version=version+1,state='OBSERVED' WHERE id=1 AND version=? AND state='PENDING'",(version,)).rowcount != 1:
                raise ValueError('SAMPLE_CAS_HOLD')
            db.execute('INSERT INTO event VALUES(?,?,?,?,?)',(command,version+1,holder,fence,tick))
            db.execute("INSERT INTO audit VALUES(?,'SAMPLE_ONLY')",(command,))
            db.execute("INSERT INTO outbox VALUES(?,'DENY')",(command,))
            return 'SAMPLE_OBSERVED'

    def snapshot(self):
        with self._db() as db:
            head = db.execute('SELECT version,state FROM head WHERE id=1').fetchone()
            counts = {t: db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('event','audit','outbox')}
        return {'mode':SCOPE[0],'tenant':SCOPE[1],'company':SCOPE[2],'head':head,'counts':counts,'admission':'DENY','dispatch_allowed':False,'release_ready':False,'provider_called':False,'spend_allowed':False}
