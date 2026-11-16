"""0211 D0 restore-external intent authority fixture; no live effects or trust grant.

A separate, non-restored SQLite store serializes cooperating root publishers and
T1 callers. This is not independent custody or distributed provider fencing.
"""
from contextlib import closing, contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3


def _digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


@dataclass(frozen=True)
class RootPin:
    record_sha: str
    key_sha: str
    recovery_epoch: int

    def validate(self):
        if not (_digest(self.record_sha) and _digest(self.key_sha) and
                type(self.recovery_epoch) is int and 0 < self.recovery_epoch < 2**63):
            raise ValueError('D0_AUTHORITY_PIN_HOLD')


def _path(path):
    p = Path(os.path.abspath(path))
    if not p.name.endswith('.authority.sqlite') or p.resolve() != p or any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('D0_AUTHORITY_PATH_HOLD')
    return p


class D0IntentAuthority:
    """Fixture: never restore alongside product DBs. All publishers must use CAS."""
    def __init__(self, path):
        self.path = _path(path)

    def _db(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, isolation_level=None, timeout=2)
        db.execute('PRAGMA trusted_schema=OFF')
        return db

    @classmethod
    def create(cls, path, root):
        if type(root) is not RootPin:
            raise ValueError('D0_AUTHORITY_PIN_HOLD')
        root.validate()
        a = cls(path)
        fd = os.open(a.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(a._db()) as db:
            db.executescript("""BEGIN IMMEDIATE;
            CREATE TABLE roots(seq INTEGER PRIMARY KEY, record_sha TEXT UNIQUE NOT NULL,
                key_sha TEXT NOT NULL, epoch INTEGER NOT NULL);
            CREATE TABLE claims(scope_sha TEXT PRIMARY KEY, binding TEXT UNIQUE NOT NULL,
                tx TEXT UNIQUE NOT NULL, request_digest TEXT NOT NULL, root_seq INTEGER NOT NULL,
                root_sha TEXT NOT NULL);
            CREATE TRIGGER roots_no_update BEFORE UPDATE ON roots BEGIN SELECT RAISE(ABORT,'append only'); END;
            CREATE TRIGGER roots_no_delete BEFORE DELETE ON roots BEGIN SELECT RAISE(ABORT,'append only'); END;
            CREATE TRIGGER roots_no_replace BEFORE INSERT ON roots WHEN EXISTS(SELECT 1 FROM roots WHERE seq=NEW.seq OR record_sha=NEW.record_sha) BEGIN SELECT RAISE(ABORT,'append only'); END;
            CREATE TRIGGER claims_no_update BEFORE UPDATE ON claims BEGIN SELECT RAISE(ABORT,'append only'); END;
            CREATE TRIGGER claims_no_delete BEFORE DELETE ON claims BEGIN SELECT RAISE(ABORT,'append only'); END;
            CREATE TRIGGER claims_no_replace BEFORE INSERT ON claims WHEN EXISTS(SELECT 1 FROM claims WHERE scope_sha=NEW.scope_sha OR binding=NEW.binding OR tx=NEW.tx) BEGIN SELECT RAISE(ABORT,'append only'); END;""")
            db.execute('INSERT INTO roots VALUES (1,?,?,?)', (root.record_sha, root.key_sha, root.recovery_epoch))
            db.execute('COMMIT')
        return a

    @staticmethod
    def _head(db):
        row = db.execute('SELECT seq,record_sha,key_sha,epoch FROM roots ORDER BY seq DESC LIMIT 1').fetchone()
        if row is None:
            raise ValueError('D0_AUTHORITY_MISSING_HOLD')
        seq, *data = row
        root = RootPin(*data)
        root.validate()
        return seq, root

    def publish(self, expected, new):
        if type(expected) is not RootPin or type(new) is not RootPin:
            raise ValueError('D0_AUTHORITY_PIN_HOLD')
        expected.validate()
        new.validate()
        with closing(self._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            seq, current = self._head(db)
            if current != expected or new.key_sha != current.key_sha or new.recovery_epoch < current.recovery_epoch or new.record_sha == current.record_sha:
                raise ValueError('D0_AUTHORITY_CAS_HOLD')
            db.execute('INSERT INTO roots VALUES (?,?,?,?)', (seq+1, new.record_sha, new.key_sha, new.recovery_epoch))
            db.execute('COMMIT')

    @contextmanager
    def claim_and_fence(self, expected, scope_sha, binding, tx, request_digest):
        """Consume scope before T1; then lock the root through the caller's commit.

        Any failure after claim leaves a permanent quarantine. No reset or retry.
        A publisher winning the gap between claim commit and fence causes HOLD.
        """
        if type(expected) is not RootPin or not all(_digest(x) for x in (scope_sha,binding,request_digest)) or type(tx) is not str or not 0 < len(tx) <= 512:
            raise ValueError('D0_AUTHORITY_INPUT_HOLD')
        expected.validate()
        with closing(self._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            seq, current = self._head(db)
            if current != expected:
                raise ValueError('D0_AUTHORITY_ROOT_HOLD')
            if db.execute('SELECT 1 FROM claims WHERE scope_sha=? OR binding=? OR tx=?', (scope_sha,binding,tx)).fetchone():
                raise ValueError('D0_AUTHORITY_ALREADY_CLAIMED_HOLD')
            db.execute('INSERT INTO claims VALUES (?,?,?,?,?,?)', (scope_sha,binding,tx,request_digest,seq,current.record_sha))
            db.execute('COMMIT')
            db.execute('BEGIN IMMEDIATE')
            if self._head(db) != (seq, expected):
                raise ValueError('D0_AUTHORITY_ROOT_CHANGED_HOLD')
            try:
                yield
            finally:
                if db.in_transaction:
                    db.execute('ROLLBACK')


def execute_authority_fenced_transition(*, authority, intent, context, registry, witness,
        expected_binding, memory_path, reader, public_key, raw, journal, connect, clock):
    """Opt-in wrapper around 0210; no caller-supplied latest callback or live grant."""
    from app.core.transaction.fenced_transition import execute_fenced_transition, intent_pin
    from app.core.transaction.witnessed_mapping import binding_digest
    from app.core.agent_runtime.memory_witness import LatestWitnessPin
    if type(authority) is not D0IntentAuthority or type(witness) is not LatestWitnessPin:
        raise ValueError('D0_AUTHORITY_ADAPTER_HOLD')
    if binding_digest(intent, context, registry, witness) != expected_binding:
        raise ValueError('D0_AUTHORITY_BINDING_HOLD')
    if any(os.path.samefile(authority.path, p) for p in (memory_path, reader.path, journal.path)):
        raise ValueError('D0_AUTHORITY_SEPARATION_HOLD')
    pin = intent_pin(intent, expected_binding)
    root = RootPin(witness.record_sha, witness.key_sha, witness.recovery_epoch)
    with authority.claim_and_fence(root, pin.scope_sha, pin.binding, pin.transaction_ref, pin.request_digest):
        return execute_fenced_transition(intent, context, registry, witness, expected_binding,
            memory_path, reader, public_key, raw, journal, connect, clock, lambda: witness)
