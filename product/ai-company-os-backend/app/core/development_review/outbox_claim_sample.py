"""D0 persistent local review claims; never a send queue or canonical T1 receipt."""
from .atomic_sample import AtomicSample, DDL, SCOPE, holder_ok, integer
import re

PROFILE = 'D0_OUTBOX_REVIEW_0184'
REVIEW_DDL = DDL.replace(SCOPE[0], PROFILE) + """
CREATE TABLE local_review(
 command_id TEXT PRIMARY KEY REFERENCES outbox(command_id),
 phase TEXT NOT NULL CHECK(phase IN ('CLAIMED','UNKNOWN_HOLD','READBACK_HOLD')),
 reviewer TEXT NOT NULL, generation INTEGER NOT NULL CHECK(generation>0),
 tick INTEGER NOT NULL CHECK(tick>=0), expires INTEGER NOT NULL CHECK(expires>tick),
 readback_sha TEXT,
 CHECK((phase='READBACK_HOLD') = (readback_sha IS NOT NULL))
);
"""


class OutboxReviewSample(AtomicSample):
    scope = (PROFILE, *SCOPE[1:])
    ddl = REVIEW_DDL
    suffix = '.review.atomic.d0.sqlite'

    @staticmethod
    def _bound(db, command):
        row = db.execute("SELECT e.tick FROM event e JOIN audit a USING(command_id) JOIN outbox o USING(command_id) JOIN head h ON h.id=1 AND h.version=e.version AND h.state='OBSERVED' WHERE e.command_id=? AND a.decision='SAMPLE_ONLY' AND o.status='DENY'", (command,)).fetchone()
        if row is None:
            raise ValueError('SAMPLE_OUTBOX_BINDING_HOLD')
        return row[0]

    def claim_review(self, command, reviewer, tick, ttl):
        """Only local review ownership, never an execution or dispatch lease."""
        if not holder_ok(command) or not holder_ok(reviewer) or not integer(tick) or not integer(ttl) or not 1 <= ttl <= 100 or not integer(tick+ttl):
            raise ValueError('SAMPLE_REVIEW_INVALID')
        with self._db() as db:
            if tick < self._bound(db, command):
                raise ValueError('SAMPLE_REVIEW_CLOCK_REGRESSION')
            old = db.execute('SELECT phase,generation,tick,expires FROM local_review WHERE command_id=?',(command,)).fetchone()
            if old:
                if old[0] != 'CLAIMED':
                    raise ValueError('SAMPLE_NO_BLIND_RETRY')
                if tick < old[2] or tick < old[3]:
                    raise ValueError('SAMPLE_REVIEW_BUSY_OR_STALE')
            generation = old[1]+1 if old else 1
            if not integer(generation):
                raise ValueError('SAMPLE_REVIEW_GENERATION_EXHAUSTED')
            db.execute("INSERT INTO local_review VALUES(?,'CLAIMED',?,?,?,?,NULL) ON CONFLICT(command_id) DO UPDATE SET reviewer=excluded.reviewer,generation=excluded.generation,tick=excluded.tick,expires=excluded.expires", (command,reviewer,generation,tick,tick+ttl))
            return generation

    def mark_unknown(self, command, reviewer, generation, tick):
        """Inject a sample uncertain outcome, no actual send or provider result."""
        if not holder_ok(command) or not holder_ok(reviewer) or not integer(generation) or generation==0 or not integer(tick):
            raise ValueError('SAMPLE_REVIEW_INVALID')
        with self._db() as db:
            self._bound(db, command)
            row = db.execute('SELECT phase,reviewer,generation,tick,expires FROM local_review WHERE command_id=?',(command,)).fetchone()
            if not row or row[:3] != ('CLAIMED',reviewer,generation) or not row[3] <= tick < row[4]:
                raise ValueError('SAMPLE_REVIEW_CLAIM_STALE')
            db.execute("UPDATE local_review SET phase='UNKNOWN_HOLD',tick=? WHERE command_id=?",(tick,command))
            return 'UNKNOWN_HOLD'

    def record_readback(self, command, generation, sample_sha):
        """Record a caller-supplied sample digest; no authenticity, resolution or retry."""
        if not holder_ok(command) or not integer(generation) or generation==0 or not isinstance(sample_sha,str) or not re.fullmatch('[0-9a-f]{64}',sample_sha):
            raise ValueError('SAMPLE_READBACK_INVALID')
        with self._db() as db:
            self._bound(db,command)
            row=db.execute('SELECT phase,generation,readback_sha FROM local_review WHERE command_id=?',(command,)).fetchone()
            if row == ('READBACK_HOLD',generation,sample_sha):
                return 'DUPLICATE_IGNORED'
            if row != ('UNKNOWN_HOLD',generation,None):
                raise ValueError('SAMPLE_READBACK_CONFLICT_OR_HOLD')
            db.execute("UPDATE local_review SET phase='READBACK_HOLD',readback_sha=? WHERE command_id=?",(sample_sha,command))
            return 'READBACK_HOLD'

    def inspect_review(self, command):
        if not holder_ok(command):
            raise ValueError('SAMPLE_REVIEW_INVALID')
        with self._db() as db:
            self._bound(db,command)
            row=db.execute('SELECT phase,generation,readback_sha FROM local_review WHERE command_id=?',(command,)).fetchone()
        return {'mode':PROFILE,'phase':row[0] if row else 'LOCAL_HOLD','generation':row[1] if row else None,'readback_sha':row[2] if row else None,'admission':'DENY','dispatch_allowed':False,'retry_allowed':False,'reconciled':False,'provider_called':False,'release_ready':False}


def read_projection(path):
    """Strict read-only projection of a pre-existing explicitly configured local D0 file."""
    from contextlib import closing
    import sqlite3
    from pathlib import Path
    p = Path(path)
    if not p.name.endswith(OutboxReviewSample.suffix) or not p.is_file() or p.is_symlink():
        raise ValueError('SAMPLE_PROJECTION_PATH_HOLD')
    with closing(sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        if db.execute('SELECT profile,tenant,company FROM meta LIMIT 2').fetchall() != [OutboxReviewSample.scope]:
            raise ValueError('SAMPLE_DB_SCOPE_MISMATCH')
        head=db.execute('SELECT version,state FROM head LIMIT 2').fetchall()
        commands=db.execute('SELECT command_id FROM outbox LIMIT 2').fetchall()
        if head != [(1,'OBSERVED')] or len(commands)!=1 or not holder_ok(commands[0][0]):
            raise ValueError('SAMPLE_PROJECTION_NOT_READY')
        command=commands[0][0]
        observed_tick=OutboxReviewSample._bound(db,command)
        row=db.execute('SELECT phase,generation,tick,expires,readback_sha FROM local_review WHERE command_id=?',(command,)).fetchone()
        phase,generation,recorded='LOCAL_HOLD',None,False
        if row:
            phase,generation,tick,expires,digest=row
            recorded=phase=='READBACK_HOLD'
            if phase not in {'CLAIMED','UNKNOWN_HOLD','READBACK_HOLD'} or not integer(generation) or not 1 <= generation <= 9007199254740991 or not integer(tick) or not integer(expires) or not observed_tick<=tick<expires or (recorded and (not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest))) or (not recorded and digest is not None):
                raise ValueError('SAMPLE_PROJECTION_INVALID')
        # No command ID, raw digest, path, holder, or actual authority leaves the store.
        return {'schema_version':'outbox.review.projection.v1-D0','mode':PROFILE,'tenant':'synthetic-tenant','company':'synthetic-company','phase':phase,'generation':generation,'readback_recorded':recorded,'admission':'DENY','dispatch_allowed':False,'retry_allowed':False,'reconciled':False,'provider_called':False,'release_ready':False}
