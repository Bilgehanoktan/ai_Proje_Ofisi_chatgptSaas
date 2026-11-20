"""0209 D0 signed restore-external memory head. Fixture custody is not independence."""
from contextlib import closing
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3

from app.core.agent_runtime.lifecycle import Scope, ClockSample, valid_scope, uint
from app.core.t1_review import digest_ok
from app.engines.memory_engine.snapshot_store import SnapshotPin, _pin_ok
from app.core.agent_runtime.joint_context import JointReview, inspect_joint_context

MAX_RECORDS = 4096
MAX_BODY = 4096


@dataclass(frozen=True)
class MemoryWitness:
    scope: Scope
    sequence: int
    recovery_epoch: int
    policy_epoch: int
    witness_epoch: int
    snapshot: SnapshotPin
    issued_tick: int
    expires_tick: int
    previous_sha: str | None = None
    pending: SnapshotPin | None = None


@dataclass(frozen=True)
class LatestWitnessPin:
    record_sha: str
    key_sha: str
    recovery_epoch: int


def _valid(w):
    return (type(w) is MemoryWitness and valid_scope(w.scope)
            and all(uint(x) for x in (w.sequence, w.recovery_epoch, w.policy_epoch,
                                      w.witness_epoch, w.issued_tick, w.expires_tick))
            and 1 <= w.sequence <= MAX_RECORDS and w.recovery_epoch > 0
            and w.issued_tick < w.expires_tick and _pin_ok(w.snapshot)
            and (w.previous_sha is None or digest_ok(w.previous_sha))
            and (w.pending is None or (_pin_ok(w.pending)
                 and w.pending.generation == w.snapshot.generation+1
                 and w.pending.digest != w.snapshot.digest)))


def witness_bytes(w):
    if not _valid(w):
        raise ValueError('MEMORY_WITNESS_FORMAT_HOLD')
    return json.dumps(['aicos-d0-memory-witness-v1', asdict(w)], sort_keys=True,
                      separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def witness_sha(w):
    return sha256(witness_bytes(w)).hexdigest()


def _transition(old, new):
    if not _valid(new):
        raise ValueError('MEMORY_WITNESS_FORMAT_HOLD')
    if old is None:
        if new.sequence != 1 or new.snapshot.generation != 1 or new.previous_sha is not None or new.pending is not None:
            raise ValueError('MEMORY_WITNESS_GENESIS_HOLD')
        return
    if (new.scope != old.scope or new.sequence != old.sequence+1 or new.previous_sha != witness_sha(old)
            or new.issued_tick < old.issued_tick or new.policy_epoch < old.policy_epoch
            or new.witness_epoch < old.witness_epoch):
        raise ValueError('MEMORY_WITNESS_CHAIN_HOLD')
    if old.pending is not None:
        if (new.pending is not None or new.snapshot != old.pending
                or new.recovery_epoch != old.recovery_epoch):
            raise ValueError('MEMORY_WITNESS_PENDING_HOLD')
    elif new.pending is not None:
        if new.snapshot != old.snapshot or new.recovery_epoch != old.recovery_epoch:
            raise ValueError('MEMORY_WITNESS_PENDING_HOLD')
    elif (new.snapshot != old.snapshot or new.recovery_epoch != old.recovery_epoch+1):
        raise ValueError('MEMORY_WITNESS_MONOTONIC_HOLD')


def _decode(body):
    if type(body) is not bytes or len(body) > MAX_BODY:
        raise ValueError('MEMORY_WITNESS_SIZE_HOLD')
    profile, obj = json.loads(body)
    if profile != 'aicos-d0-memory-witness-v1' or type(obj) is not dict:
        raise ValueError('MEMORY_WITNESS_FORMAT_HOLD')
    obj['scope'] = Scope(**obj['scope'])
    obj['snapshot'] = SnapshotPin(**obj['snapshot'])
    if obj['pending'] is not None:
        obj['pending'] = SnapshotPin(**obj['pending'])
    w = MemoryWitness(**obj)
    if witness_bytes(w) != body:
        raise ValueError('MEMORY_WITNESS_CANONICAL_HOLD')
    return w


def _path(path):
    p = Path(os.path.abspath(path))
    if not p.name.endswith('.witness.sqlite') or p.resolve() != p or any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('MEMORY_WITNESS_PATH_HOLD')
    return p


def _connect(path, mode):
    db = sqlite3.connect(_path(path).as_uri()+'?mode='+mode, uri=True, timeout=2, isolation_level=None)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        if mode == 'ro':
            db.execute('PRAGMA query_only=ON')
        return db
    except BaseException:
        db.close()
        raise


def _latest(db, public_key, committed=None):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if type(public_key) is not bytes or len(public_key) != 32:
        raise ValueError('MEMORY_WITNESS_KEY_HOLD')
    key = Ed25519PublicKey.from_public_bytes(public_key)
    old = None
    for i, (seq, digest, body, sig) in enumerate(db.execute(
            'SELECT sequence,digest,CASE WHEN length(body)<=4096 THEN body END,'
            'CASE WHEN length(signature)=64 THEN signature END FROM memory_witness ORDER BY sequence'), 1):
        if i > MAX_RECORDS or type(sig) is not bytes or len(sig) != 64:
            raise ValueError('MEMORY_WITNESS_LIMIT_HOLD')
        w = _decode(body)
        _transition(old, w)
        if seq != i or w.sequence != seq or witness_sha(w) != digest:
            raise ValueError('MEMORY_WITNESS_CHAIN_HOLD')
        key.verify(sig, body)
        # Only genesis or finalized pending transitions add a generation.
        # Recovery epochs and staged pending records do not duplicate pins.
        if committed is not None and (old is None or w.snapshot.generation != old.snapshot.generation):
            committed.append(w.snapshot)
        old = w
    return old


class MemoryWitnessReader:
    """Read only. Latest digest and key pin must originate outside BOTH restored stores."""
    def __init__(self, path):
        self.path = _path(path)

    def read_latest(self, expected, public_key):
        return self.read_history(expected, public_key)[0]

    def read_history(self, expected, public_key):
        """Return the externally pinned signed head and committed generation pins.

        The unchanged v1 chain already commits to every finalized generation.
        This is D0 evidence only; it is not a write or independent trust grant.
        """
        if (type(expected) is not LatestWitnessPin or not digest_ok(expected.record_sha)
                or not digest_ok(expected.key_sha) or not uint(expected.recovery_epoch)
                or type(public_key) is not bytes or sha256(public_key).hexdigest() != expected.key_sha):
            raise ValueError('MEMORY_WITNESS_EXTERNAL_PIN_HOLD')
        committed = []
        with closing(_connect(self.path, 'ro')) as db:
            db.execute('BEGIN')
            head = _latest(db, public_key, committed)
        if head is None or witness_sha(head) != expected.record_sha or head.recovery_epoch != expected.recovery_epoch:
            raise ValueError('MEMORY_WITNESS_EXTERNAL_PIN_HOLD')
        if (len(committed) != head.snapshot.generation or committed[-1] != head.snapshot
                or any(p.generation != i for i, p in enumerate(committed, 1))):
            raise ValueError('MEMORY_WITNESS_HISTORY_HOLD')
        return head, tuple(committed)


class D0MemoryWitnessStore(MemoryWitnessReader):
    """Disposable fixture writer. No private key custody or production trust."""
    @classmethod
    def create(cls, path):
        p = _path(path)
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(_connect(p, 'rw')) as db:
            db.execute('CREATE TABLE memory_witness(sequence INTEGER PRIMARY KEY,digest TEXT NOT NULL UNIQUE,body BLOB NOT NULL,signature BLOB NOT NULL)')
            db.execute("CREATE TRIGGER no_update BEFORE UPDATE ON memory_witness BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER no_delete BEFORE DELETE ON memory_witness BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER no_replace BEFORE INSERT ON memory_witness WHEN EXISTS(SELECT 1 FROM memory_witness WHERE sequence=NEW.sequence OR digest=NEW.digest) BEGIN SELECT RAISE(ABORT,'append only'); END")
        return cls(p)

    def append(self, record, signature, public_key, expected_previous):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        body = witness_bytes(record)
        if type(signature) is not bytes or len(signature) != 64 or type(public_key) is not bytes or len(public_key) != 32:
            raise ValueError('MEMORY_WITNESS_SIGNATURE_HOLD')
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, body)
        with closing(_connect(self.path, 'rw')) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                old = _latest(db, public_key)
                if expected_previous != (witness_sha(old) if old else None):
                    raise ValueError('MEMORY_WITNESS_CAS_HOLD')
                _transition(old, record)
                db.execute('INSERT INTO memory_witness VALUES (?,?,?,?)',
                           (record.sequence, witness_sha(record), body, signature))
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                raise
        return LatestWitnessPin(witness_sha(record), sha256(public_key).hexdigest(), record.recovery_epoch)


@dataclass(frozen=True)
class WitnessedReview(JointReview):
    independent_verified: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def inspect_witnessed_context(context, registry, expected_digest, memory_path, current_run,
                              current_lease, clock, raw, reader, expected_witness, public_key):
    """Bracket the joint review with current signed head checks; never a grant."""
    try:
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return WitnessedReview('MEMORY_WITNESS_CRYPTO_HOLD')
    try:
        if type(reader) not in (MemoryWitnessReader, D0MemoryWitnessStore) or os.path.samefile(memory_path, reader.path):
            return WitnessedReview('MEMORY_WITNESS_SEPARATION_HOLD')
        w, committed = reader.read_history(expected_witness, public_key)
        if not _valid(w) or witness_sha(w) != expected_witness.record_sha:
            return WitnessedReview('MEMORY_WITNESS_EXTERNAL_PIN_HOLD')
        if w.pending is not None:
            return WitnessedReview('MEMORY_WITNESS_PENDING_HOLD')
        if (w.snapshot != context.memory_pin or w.scope != context.invocation.run.scope
                or w.scope != current_run.scope or not isinstance(clock, ClockSample)
                or not all(uint(v) for v in (clock.now_tick, clock.policy_epoch, clock.witness_epoch))
                or (w.policy_epoch, w.witness_epoch) != (clock.policy_epoch, clock.witness_epoch)
                or not w.issued_tick <= clock.now_tick < w.expires_tick):
            return WitnessedReview('MEMORY_WITNESS_CONTEXT_HOLD')
        r = inspect_joint_context(context, registry, expected_digest, memory_path,
                                  current_run, current_lease, clock, raw, committed)
        if not r.structural_match or r.reason != 'D0_JOINT_CONTEXT_MATCH_ONLY':
            return WitnessedReview(r.reason)
        if reader.read_history(expected_witness, public_key) != (w, committed):
            return WitnessedReview('MEMORY_WITNESS_CHANGED_HOLD')
        return WitnessedReview('D0_WITNESSED_CONTEXT_MATCH_ONLY', True)
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, AttributeError,
            OverflowError, RecursionError, ImportError, InvalidSignature):
        return WitnessedReview('MEMORY_WITNESS_READ_HOLD')
