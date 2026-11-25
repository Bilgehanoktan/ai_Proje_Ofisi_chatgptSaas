"""0205-R D0 restore-external reference and quarantine; never execution authority."""
from contextlib import closing
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
import json
import re
import sqlite3
from app.core.event_store.company_coordination import SCOPE, replay_company, inspect_company

_MAX_GENERATIONS = 12000


def _sha(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None


def _uint(v):
    return type(v) is int and 0 <= v < 2**63


def _bytes(profile, value):
    return json.dumps([profile, value], ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


@dataclass(frozen=True)
class CompanyCheckpoint:
    digest: str
    sequence: int
    pool_revision: int


def checkpoint(members, pool, events):
    """Bind explicit roster, fixed caps, initial pool and full ordered history."""
    r = replay_company(members, pool, events)
    if not r.structural_match:
        raise ValueError('D0_RECOVERY_CHECKPOINT_HOLD')
    body = _bytes('aicos-d0-company-checkpoint-v1', {
        'scope': SCOPE,
        'members': [asdict(m) for m in sorted(members, key=lambda x:x.run_id)],
        'pool': {**asdict(pool), 'allocations': [asdict(a) for a in sorted(pool.allocations,key=lambda x:x.project_id)]},
        'events': [asdict(e) for e in events],
        'postimage': [r.event_count,r.pool_revision,r.outstanding_minor,r.project_outstanding]})
    if len(body) > 8*1024*1024:
        raise ValueError('D0_RECOVERY_CHECKPOINT_LIMIT')
    return CompanyCheckpoint(sha256(body).hexdigest(),r.event_count,r.pool_revision)


@dataclass(frozen=True)
class WitnessRecord:
    generation: int
    recovery_epoch: int
    checkpoint_sha: str
    sequence: int
    pool_revision: int
    previous_sha: str | None = None
    pending_sha: str | None = None
    pending_pool_revision: int | None = None


def _valid(w):
    return (type(w) is WitnessRecord and all(_uint(x) for x in (w.generation,w.recovery_epoch,w.sequence,w.pool_revision))
            and 1<=w.generation<=_MAX_GENERATIONS and w.recovery_epoch>0 and w.sequence<=5000 and _sha(w.checkpoint_sha)
            and (w.previous_sha is None or _sha(w.previous_sha))
            and ((w.pending_sha is None and w.pending_pool_revision is None)
                 or (_sha(w.pending_sha) and w.pending_sha!=w.checkpoint_sha and _uint(w.pending_pool_revision)
                     and w.sequence<5000 and w.pending_pool_revision in (w.pool_revision,w.pool_revision+1))))


def witness_bytes(w):
    if not _valid(w): raise ValueError('D0_RECOVERY_WITNESS_FORMAT_HOLD')
    return _bytes('aicos-d0-recovery-witness-v1',asdict(w))


def witness_sha(w):
    return sha256(witness_bytes(w)).hexdigest()


def _base(w):
    return CompanyCheckpoint(w.checkpoint_sha,w.sequence,w.pool_revision)


def _pending(w):
    return CompanyCheckpoint(w.pending_sha,w.sequence+1,w.pending_pool_revision)


def _transition(old,new):
    if not _valid(new): raise ValueError('D0_RECOVERY_WITNESS_FORMAT_HOLD')
    if old is None:
        if new.generation!=1 or new.previous_sha is not None or new.pending_sha is not None:
            raise ValueError('D0_RECOVERY_GENESIS_HOLD')
        return
    if (new.generation!=old.generation+1 or new.previous_sha!=witness_sha(old)):
        raise ValueError('D0_RECOVERY_WITNESS_CHAIN_HOLD')
    if old.pending_sha is not None:
        # Only exact staged target may be published. Absence cannot clear an unknown transaction.
        if (_base(new)!=_pending(old) or new.pending_sha is not None or new.recovery_epoch!=old.recovery_epoch):
            raise ValueError('D0_RECOVERY_PENDING_HOLD')
    elif (_base(new)!=_base(old) or
          not ((new.pending_sha is not None and new.recovery_epoch==old.recovery_epoch)
               or (new.pending_sha is None and new.recovery_epoch==old.recovery_epoch+1))):
        raise ValueError('D0_RECOVERY_MONOTONIC_HOLD')


def genesis(cp, epoch=1):
    if type(cp) is not CompanyCheckpoint: raise ValueError('D0_RECOVERY_CHECKPOINT_HOLD')
    w=WitnessRecord(1,epoch,cp.digest,cp.sequence,cp.pool_revision)
    _transition(None,w);return w


def stage_pending(old,members,pool,events,event):
    """Prepare exact one-event target before attempting a transaction; no DB write."""
    if not _valid(old) or old.pending_sha is not None or checkpoint(members,pool,events)!=_base(old):
        raise ValueError('D0_RECOVERY_PENDING_HOLD')
    target=checkpoint(members,pool,events+(event,))
    w=WitnessRecord(old.generation+1,old.recovery_epoch,old.checkpoint_sha,old.sequence,
                    old.pool_revision,witness_sha(old),target.digest,target.pool_revision)
    _transition(old,w);return w


def advance_recovery_epoch(old):
    """Recovery epoch is distinct from policy/lease witness epoch; no grant refresh."""
    if not _valid(old) or old.pending_sha is not None:
        raise ValueError('D0_RECOVERY_PENDING_HOLD')
    w=WitnessRecord(old.generation+1,old.recovery_epoch+1,old.checkpoint_sha,old.sequence,
                    old.pool_revision,witness_sha(old))
    _transition(old,w);return w


def _latest(db):
    old=None
    for i,(generation,key,body) in enumerate(db.execute('SELECT generation,digest,CASE WHEN length(body)<=4096 THEN body ELSE NULL END FROM recovery_witness ORDER BY generation'),1):
        if i>_MAX_GENERATIONS or type(body) is not bytes or len(body)>4096:
            raise ValueError('D0_RECOVERY_WITNESS_LIMIT')
        obj=json.loads(body)
        if type(obj) is not list or len(obj)!=2 or obj[0]!='aicos-d0-recovery-witness-v1' or type(obj[1]) is not dict:
            raise ValueError('D0_RECOVERY_WITNESS_FORMAT_HOLD')
        new=WitnessRecord(**obj[1]);_transition(old,new)
        if generation!=i or generation!=new.generation or witness_bytes(new)!=body or witness_sha(new)!=key:
            raise ValueError('D0_RECOVERY_WITNESS_CHAIN_HOLD')
        old=new
    return old


class WitnessReader:
    """Read-only external-store adapter. Expected latest SHA must come from outside BOTH databases."""
    def __init__(self,path): self.path=Path(path).resolve()

    def read_latest(self,expected_sha):
        if not _sha(expected_sha): raise ValueError('D0_RECOVERY_EXTERNAL_PIN_HOLD')
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            w=_latest(db)
        if w is None or witness_sha(w)!=expected_sha:
            raise ValueError('D0_RECOVERY_EXTERNAL_PIN_HOLD')
        return w


class D0WitnessStore(WitnessReader):
    """Local fixture append-only CAS; NOT independent/WORM custody, not a signing service."""
    def __init__(self,path):
        super().__init__(path)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('CREATE TABLE IF NOT EXISTS recovery_witness(generation INTEGER PRIMARY KEY,digest TEXT NOT NULL UNIQUE,body BLOB NOT NULL)')
            db.execute("CREATE TRIGGER IF NOT EXISTS witness_no_update BEFORE UPDATE ON recovery_witness BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS witness_no_delete BEFORE DELETE ON recovery_witness BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS witness_no_replace BEFORE INSERT ON recovery_witness WHEN EXISTS(SELECT 1 FROM recovery_witness WHERE generation=NEW.generation OR digest=NEW.digest) BEGIN SELECT RAISE(ABORT,'append only'); END")

    def append(self,w,expected_previous_sha):
        """Only genesis, staged intent, recovery epoch bump. No target publication by writer."""
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('BEGIN IMMEDIATE');old=_latest(db)
            if expected_previous_sha!=(witness_sha(old) if old is not None else None):
                raise ValueError('D0_RECOVERY_WITNESS_CAS_HOLD')
            if old is not None and old.pending_sha is not None:
                raise ValueError('D0_RECOVERY_PENDING_HOLD')
            _transition(old,w)
            db.execute('INSERT INTO recovery_witness VALUES (?,?,?)',(w.generation,witness_sha(w),witness_bytes(w)))
        return witness_sha(w)


@dataclass(frozen=True)
class RecoveryReview:
    reason: str
    checkpoint_match: bool = False
    pending_target_match: bool = False
    recovery_epoch: int | None = None
    mode: str = field(default='RECOVERY_READ_ONLY',init=False)
    decision: str = field(default='HOLD',init=False)
    independent_verified: bool = field(default=False,init=False)
    dispatch_allowed: bool = field(default=False,init=False)
    spend_allowed: bool = field(default=False,init=False)
    replay_allowed: bool = field(default=False,init=False)
    retry_allowed: bool = field(default=False,init=False)
    publish_allowed: bool = field(default=False,init=False)


def review_recovery(cursor,members,pool,events,reader,expected_witness_sha):
    """Caller owns one consistent read-only company snapshot; no mutation or replay.

    An exact pending target is historical evidence, not publication authorization.
    A base match while pending is ambiguous; absence never proves rollback.
    """
    try:
        w=reader.read_latest(expected_witness_sha)
        if not _valid(w) or witness_sha(w)!=expected_witness_sha:
            raise ValueError('D0_RECOVERY_EXTERNAL_PIN_HOLD')
        observed=checkpoint(members,pool,events)
        base_match=observed==_base(w)
        pending_match=w.pending_sha is not None and observed==_pending(w)
        if not (base_match or pending_match):
            return RecoveryReview('D0_RECOVERY_CHECKPOINT_MISMATCH_HOLD')
        if not inspect_company(cursor,members,pool,events).structural_match:
            return RecoveryReview('D0_RECOVERY_READBACK_HOLD')
        if reader.read_latest(expected_witness_sha)!=w:
            return RecoveryReview('D0_RECOVERY_WITNESS_CHANGED_HOLD')
        if w.pending_sha is not None:
            return RecoveryReview('D0_RECOVERY_UNKNOWN_COMMIT_MATCH_ONLY' if pending_match else
                                  'D0_RECOVERY_UNKNOWN_ABSENCE_NOT_PROOF',base_match,pending_match,w.recovery_epoch)
        return RecoveryReview('D0_RECOVERY_CHECKPOINT_MATCH_READ_ONLY',True,False,w.recovery_epoch)
    except Exception:
        return RecoveryReview('D0_RECOVERY_EXTERNAL_OR_READBACK_HOLD')
