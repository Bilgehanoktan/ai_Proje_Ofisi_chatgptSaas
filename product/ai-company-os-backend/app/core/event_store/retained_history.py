"""0201-R: D0 content-addressed history retention. No independent custody or grant."""
from contextlib import closing
from copy import deepcopy
from dataclasses import fields, is_dataclass, dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
import json
from importlib import import_module
import re
import sqlite3

MAX_BYTES = 8 * 1024 * 1024
_TYPES = {
    'app.core.agent_runtime.lifecycle': {'Scope', 'RunObservation', 'LeaseObservation', 'RunState'},
    'app.core.transaction.review': {'LogicalIntent', 'Operation'},
    'app.core.transaction.postgres_admission_mapping': {'SampleBudget', 'ClaimSpec'},
    'app.core.transaction.postgres_lifecycle_mapping': {'AdmissionBinding', 'LifecycleSpec'},
    'app.core.event_store.history_readback': {'OrdinaryPin', 'LifecyclePin'},
    'app.core.event_store.plan_history_review': {'RunHistoryPin'},
}


def _encode(value, depth=0, budget=None):
    if budget is None: budget = [200000, MAX_BYTES]
    budget[0] -= 1
    if type(value) is str: budget[1] -= len(value)
    if depth > 32 or min(budget) < 0:
        raise ValueError('D0_REFERENCE_DEPTH_HOLD')
    typ = type(value)
    def child(v): return _encode(v, depth + 1, budget)
    if typ is type(None): return ['null']
    if typ is bool: return ['bool', value]
    if typ is int and -(2**63) <= value < 2**63: return ['int', value]
    if typ is str and len(value) <= 4096: return ['str', value]
    if typ in (tuple, list) and len(value) <= 5000:
        return [typ.__name__, [child(v) for v in value]]
    if typ is dict and len(value) <= 5000 and all(type(k) is str and len(k) <= 4096 for k in value):
        budget[1] -= sum(len(k) for k in value)
        if budget[1] < 0: raise ValueError('D0_REFERENCE_SIZE_HOLD')
        return ['dict', [[k, child(value[k])] for k in sorted(value)]]
    if (typ.__name__ in _TYPES.get(typ.__module__, ())
            and getattr(import_module(typ.__module__), typ.__name__, None) is typ):
        name = typ.__module__ + '.' + typ.__name__
        if isinstance(value, Enum): return ['enum', name, child(value.value)]
        if is_dataclass(value): return ['record', name, [[f.name, child(getattr(value, f.name))] for f in fields(value)]]
    raise ValueError('D0_REFERENCE_TYPE_HOLD')


def reference_bytes(kind, value):
    if kind not in ('plan-history-v1', 'terminal-command-v1'):
        raise ValueError('D0_REFERENCE_KIND_HOLD')
    data = json.dumps(['aicos-d0-retained-v1', kind, _encode(value)], ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')
    if len(data) > MAX_BYTES: raise ValueError('D0_REFERENCE_SIZE_HOLD')
    return data


def digest(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError('D0_REFERENCE_SIZE_HOLD')
    return sha256(data).hexdigest()


class ReferenceReader:
    """Read-only connection; independent custody remains an external prerequisite."""
    def __init__(self, path):
        self.path = Path(path).resolve()

    def read(self, expected):
        if type(expected) is not str or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('D0_REFERENCE_DIGEST_HOLD')
        with closing(sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)) as db:
            row = db.execute('SELECT body FROM reference_objects WHERE digest=? AND length(body) BETWEEN 1 AND ?', (expected, MAX_BYTES)).fetchone()
        if row is None or digest(row[0]) != expected:
            raise ValueError('D0_REFERENCE_MISSING_OR_CORRUPT')
        return row[0]


class ReferenceStore(ReferenceReader):
    """Separate local SQLite archive; ordinary app writes append only, not WORM."""
    def __init__(self, path):
        super().__init__(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS reference_objects (digest TEXT PRIMARY KEY, body BLOB NOT NULL)')
            db.execute("CREATE TRIGGER IF NOT EXISTS reference_no_update BEFORE UPDATE ON reference_objects BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS reference_no_delete BEFORE DELETE ON reference_objects BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS reference_no_replace BEFORE INSERT ON reference_objects WHEN EXISTS(SELECT 1 FROM reference_objects WHERE digest=NEW.digest) BEGIN SELECT RAISE(ABORT,'append only'); END")

    def put(self, body):
        key = digest(body)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT body FROM reference_objects WHERE digest=?', (key,)).fetchone()
            if row is None:
                db.execute('INSERT INTO reference_objects VALUES (?,?)', (key, body))
            elif row[0] != body:
                raise ValueError('D0_REFERENCE_COLLISION_HOLD')
        return key


def history_reference(plan, revision, pins, anchors=None):
    if type(plan) is not dict or type(revision) is not str or type(pins) is not tuple or len(pins)>100:
        raise ValueError('D0_REFERENCE_ENVELOPE_HOLD')
    if anchors is not None and (type(anchors) is not tuple or len(anchors)>100):
        raise ValueError('D0_REFERENCE_ANCHORS_HOLD')
    return reference_bytes('plan-history-v1', (plan, revision, pins, anchors))


@dataclass(frozen=True)
class RetainedReview:
    reason: str
    history: object = None
    failure_commands: tuple = ()
    reference_match: bool = False
    atomic_anchor_match: bool = False
    decision: str = field(default='HOLD', init=False)
    independent_verified: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)


def review_retained_snapshot(store, connect, plan, revision, pins, expected, *, anchors=None, terminal_refs=(), require_terminal_anchors=False):
    """Caller supplies separately retained expected digests. Never mint trust from the archive."""
    try:
        if type(require_terminal_anchors) is not bool: raise ValueError("D0_ANCHOR_MODE_HOLD")
        from app.core.event_store.postgres_snapshot import read_plan_snapshot
        from app.core.event_store.history_readback import LifecyclePin
        from app.core.transaction.postgres_lifecycle_mapping import FAILURE
        from app.core.transaction.postgres_transition_mapping import transaction_ref
        # Encode before copying: reject unsupported object types before invoking copy.
        original = history_reference(plan, revision, pins, anchors)
        if type(terminal_refs) is not tuple or len(terminal_refs)>100 or any(type(v) is not tuple or len(v) != 2 or any(type(x) is not str for x in v) for v in terminal_refs):
            raise ValueError('D0_TERMINAL_EXTERNAL_PIN_HOLD')
        plan, pins, anchors, terminal_refs = deepcopy((plan, pins, anchors, terminal_refs))
        if original != history_reference(plan, revision, pins, anchors):
            raise ValueError('D0_REFERENCE_CHANGED')
        if store.read(expected) != original:
            raise ValueError('D0_REFERENCE_MISMATCH')
        failures = []
        for pin in pins:
            for cmd in pin.commands:
                if isinstance(cmd, LifecyclePin) and cmd.spec.renewal is None:
                    if cmd.spec.outcome != FAILURE: raise ValueError('D0_TERMINAL_UNSUPPORTED')
                    key = digest(reference_bytes('terminal-command-v1', cmd))
                    if store.read(key) != reference_bytes('terminal-command-v1', cmd):
                        raise ValueError('D0_TERMINAL_REFERENCE_HOLD')
                    failures.append((pin.initial.scope.run_id, key, transaction_ref(cmd.intent)))
        expected_failures = tuple(sorted((r, k) for r, k, _ in failures))
        if type(terminal_refs) is not tuple or terminal_refs != expected_failures:
            raise ValueError('D0_TERMINAL_EXTERNAL_PIN_HOLD')
        mode = {"require_terminal_anchors": True} if require_terminal_anchors else {}
        review = read_plan_snapshot(connect, plan, revision, pins, exclusive_budget_anchors=anchors, **mode)
        if not review.structural_match: return RetainedReview('D0_RETAINED_READBACK_HOLD')
        return RetainedReview('D0_RETAINED_REFERENCE_MATCH_ONLY', review, tuple(sorted(failures)), True, require_terminal_anchors)
    except Exception:
        return RetainedReview('D0_RETAINED_REFERENCE_HOLD')
