"""0196-M disposable synthetic snapshot store; no authority or content release."""
from contextlib import closing
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3

from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, valid_scope, uint
from app.core.t1_review import digest_ok
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan, inspect_span
from .retrieval import Node, TombstoneView, inspect_retrieval
from .runtime_binding import (MemoryAclEntry, MemoryAclView, MemoryAccessReview,
                              _valid_acl, _valid_run, inspect_run_memory_access)

LIMIT = 1024 * 1024
# Bounded D0 replay, not a production retention or migration policy.
HISTORY_LIMIT = 512
HISTORY_BYTES = 64 * LIMIT


@dataclass(frozen=True)
class Snapshot:
    run: RunObservation
    nodes: tuple[Node, ...]
    target: str
    tombstone: TombstoneView
    acl: MemoryAclView
    source: SourceVersion
    span: ClaimSpan
    raw: bytes


@dataclass(frozen=True)
class SnapshotPin:
    generation: int
    digest: str
    graph_digest: str


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def _hash(value):
    return sha256(value.encode('ascii')).hexdigest()


def _pin_ok(pin):
    return (isinstance(pin, SnapshotPin) and uint(pin.generation) and pin.generation > 0
            and digest_ok(pin.digest) and digest_ok(pin.graph_digest))


def _encode(s):
    if not isinstance(s, Snapshot) or not _valid_run(s.run) or s.run.state is not RunState.RUNNING:
        raise ValueError('MEMORY_SNAPSHOT_RUN_HOLD')
    lineage = inspect_retrieval(s.run.scope, s.nodes, s.target, s.tombstone, s.tombstone)
    if lineage.reason not in ('D0_LINEAGE_MATCH_ONLY', 'STALE_HOLD'):
        raise ValueError(lineage.reason)
    if (not _valid_acl(s.acl, s.run) or
            (s.acl.tombstone_epoch, s.acl.tombstone_sequence) != (s.tombstone.epoch, s.tombstone.sequence)):
        raise ValueError('MEMORY_SNAPSHOT_ACL_HOLD')
    if inspect_span(s.span, s.source, s.raw) != 'D0_SPAN_MATCH_ONLY' or s.source.scope != s.run.scope:
        raise ValueError('MEMORY_SNAPSHOT_SOURCE_HOLD')
    graph = [asdict(replace(n, parents=tuple(sorted(n.parents)))) for n in sorted(s.nodes, key=lambda n: n.node_id)]
    metadata = _json(dict(run=asdict(s.run), nodes=graph, target=s.target,
                          tombstone=asdict(replace(s.tombstone, keys=tuple(sorted(s.tombstone.keys)))),
                          acl=asdict(replace(s.acl, entries=tuple(sorted(s.acl.entries, key=lambda e: e.node_id)))),
                          source=asdict(s.source), span=asdict(s.span)))
    if len(metadata) > LIMIT:
        raise ValueError('MEMORY_SNAPSHOT_SIZE_HOLD')
    return metadata, _hash(_json(graph))


def _decode(metadata, raw):
    if type(metadata) is not str or len(metadata) > LIMIT or type(raw) is not bytes or len(raw) > LIMIT:
        raise ValueError('MEMORY_SNAPSHOT_SIZE_HOLD')
    d = json.loads(metadata)
    run = d['run']; run['scope'] = Scope(**run['scope']); run['state'] = RunState(run['state'])
    nodes = tuple(Node(**dict(n, scope=Scope(**n['scope']), parents=tuple(n['parents']))) for n in d['nodes'])
    v = d['tombstone']; v['scope'] = Scope(**v['scope']); v['keys'] = tuple(v['keys'])
    a = d['acl']; a['scope'] = Scope(**a['scope']); a['entries'] = tuple(MemoryAclEntry(**e) for e in a['entries'])
    def source(x):
        return SourceVersion(**dict(x, scope=Scope(**x['scope'])))
    span = d['span']; span['source'] = source(span['source'])
    s = Snapshot(RunObservation(**run), nodes, d['target'], TombstoneView(**v), MemoryAclView(**a),
                 source(d['source']), ClaimSpan(**span), raw)
    canonical, graph = _encode(s)
    if canonical != metadata:
        raise ValueError('MEMORY_SNAPSHOT_CANONICAL_HOLD')
    return s, graph


def _path(path):
    p = Path(os.path.abspath(path))
    if not p.name.endswith('.d0.sqlite') or any(x.is_symlink() for x in (p, *p.parents)) or p.resolve() != p:
        raise ValueError('MEMORY_SNAPSHOT_PATH_HOLD')
    return p


def _connect(path, mode):
    db = sqlite3.connect(_path(path).as_uri() + '?mode=' + mode, uri=True, timeout=5, isolation_level=None)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        if mode == 'ro':
            db.execute('PRAGMA query_only=ON')
        return db
    except BaseException:
        db.close()
        raise


def create_store(path):
    """Explicit new disposable file; never replace an existing store."""
    p = _path(path)
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    with closing(_connect(p, 'rw')) as db:
        db.execute('CREATE TABLE snapshots (generation INTEGER PRIMARY KEY CHECK(generation>0), '
                   'digest TEXT NOT NULL, graph TEXT NOT NULL, metadata TEXT NOT NULL, raw BLOB NOT NULL)')


def _head(db):
    row = db.execute('SELECT generation,digest,graph FROM snapshots ORDER BY generation DESC LIMIT 1').fetchone()
    if row is None:
        return None
    pin = SnapshotPin(*row)
    if not _pin_ok(pin):
        raise ValueError('MEMORY_SNAPSHOT_HEAD_HOLD')
    return pin


def _load(db, pin):
    row = db.execute('SELECT metadata,raw FROM snapshots WHERE generation=? '
                     'AND length(metadata)<=? AND length(raw)<=?', (pin.generation, LIMIT, LIMIT)).fetchone()
    if row is None or type(row[0]) is not str or _hash(row[0]) != pin.digest:
        raise ValueError('MEMORY_SNAPSHOT_DIGEST_HOLD')
    snapshot, graph = _decode(*row)
    if graph != pin.graph_digest:
        raise ValueError('MEMORY_SNAPSHOT_GRAPH_HOLD')
    return snapshot


def _check_successor(old, snapshot):
    a, b = old.tombstone, snapshot.tombstone
    if (old.run != snapshot.run or old.target != snapshot.target or a.epoch != b.epoch
            or b.sequence < a.sequence or not set(a.keys) <= set(b.keys)
            or (set(a.keys) != set(b.keys) and b.sequence == a.sequence)
            or snapshot.acl.acl_revision <= old.acl.acl_revision
            or snapshot.acl.policy_epoch < old.acl.policy_epoch
            or snapshot.acl.witness_epoch < old.acl.witness_epoch):
        raise ValueError('MEMORY_SNAPSHOT_MONOTONIC_HOLD')


def _bind_revisions(revisions, snapshot):
    """A node revision is immutable, including the exact parent revisions.

    The graph is already validated by _encode/_load. Direct parent pins plus
    the same invariant for every node bind the transitive lineage. ACL and
    tombstone state may advance without changing the content revision.
    """
    by_id = {n.node_id: n for n in snapshot.nodes}
    for n in snapshot.nodes:
        key = (n.node_id, n.revision)
        parents = tuple(sorted((p, by_id[p].revision, by_id[p].digest) for p in n.parents))
        value = (n.digest, parents)
        if revisions.setdefault(key, value) != value:
            raise ValueError('MEMORY_SNAPSHOT_REVISION_IMMUTABLE_HOLD')


def _review_history(db, head, expected_history=None):
    """Replay retained history within the caller's single SQLite transaction.

    Optional committed pins originate from the existing verified Witness chain.
    Compare them in this same read transaction, not in a separate preflight.
    A coherent rewrite including all external trust pins remains out of scope.
    """
    if expected_history is not None and (
            type(expected_history) is not tuple or head is None
            or len(expected_history) != head.generation
            or not 1 <= len(expected_history) <= HISTORY_LIMIT
            or expected_history[-1] != head):
        raise ValueError('MEMORY_SNAPSHOT_WITNESS_HISTORY_HOLD')
    if head is None:
        return None, {}, 0
    if head.generation > HISTORY_LIMIT:
        raise ValueError('MEMORY_SNAPSHOT_HISTORY_LIMIT_HOLD')
    rows = db.execute('SELECT generation,digest,graph,length(metadata),length(raw) '
                      'FROM snapshots ORDER BY generation LIMIT ?', (HISTORY_LIMIT + 1,)).fetchall()
    if len(rows) != head.generation or rows[-1][:3] != (head.generation, head.digest, head.graph_digest):
        raise ValueError('MEMORY_SNAPSHOT_HISTORY_HOLD')
    revisions, previous, retained_bytes = {}, None, 0
    for generation, row in enumerate(rows, 1):
        pin = SnapshotPin(*row[:3])
        if not _pin_ok(pin) or pin.generation != generation:
            raise ValueError('MEMORY_SNAPSHOT_HISTORY_HOLD')
        if expected_history is not None:
            signed_pin = expected_history[generation - 1]
            if not _pin_ok(signed_pin) or signed_pin != pin:
                raise ValueError('MEMORY_SNAPSHOT_WITNESS_HISTORY_HOLD')
        if not all(uint(size) and size <= LIMIT for size in row[3:]):
            raise ValueError('MEMORY_SNAPSHOT_HISTORY_LIMIT_HOLD')
        retained_bytes += row[3] + row[4]
        if retained_bytes > HISTORY_BYTES:
            raise ValueError('MEMORY_SNAPSHOT_HISTORY_LIMIT_HOLD')
        current = _load(db, pin)
        if previous is not None:
            _check_successor(previous, current)
        _bind_revisions(revisions, current)
        previous = current
    return previous, revisions, retained_bytes


def publish_snapshot(path, snapshot, expected):
    """Append a synthetic observation with exact head CAS; no real memory write grant."""
    metadata, graph = _encode(snapshot)
    if expected is not None and not _pin_ok(expected):
        raise ValueError('MEMORY_SNAPSHOT_PIN_HOLD')
    with closing(_connect(path, 'rw')) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            head = _head(db)
            if head != expected:
                raise ValueError('MEMORY_SNAPSHOT_CAS_HOLD')
            old, revisions, retained_bytes = _review_history(db, head)
            if old is not None:
                _check_successor(old, snapshot)
            if ((head is not None and head.generation >= HISTORY_LIMIT)
                    or retained_bytes + len(metadata) + len(snapshot.raw) > HISTORY_BYTES):
                raise ValueError('MEMORY_SNAPSHOT_HISTORY_LIMIT_HOLD')
            _bind_revisions(revisions, snapshot)
            generation = 1 if head is None else head.generation + 1
            if not uint(generation):
                raise ValueError('MEMORY_SNAPSHOT_GENERATION_HOLD')
            pin = SnapshotPin(generation, _hash(metadata), graph)
            db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)',
                       (generation, pin.digest, graph, metadata, snapshot.raw))
            db.execute('COMMIT')
            return pin
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise


def inspect_stored_memory(path, expected, run, lease, lease_reference, clock):
    """One read-only DB snapshot, exact external pin; returns diagnostics only."""
    if not _pin_ok(expected) or not _valid_run(run) or not valid_scope(run.scope):
        return MemoryAccessReview('MEMORY_SNAPSHOT_PIN_HOLD')
    try:
        with closing(_connect(path, 'ro')) as db:
            db.execute('BEGIN')
            if _head(db) != expected:
                return MemoryAccessReview('MEMORY_SNAPSHOT_CAS_HOLD')
            s, _, _ = _review_history(db, expected)
            result = inspect_run_memory_access(s.run, run, s.nodes, s.target, s.tombstone, s.tombstone,
                                               s.acl, s.acl, lease, lease_reference, clock, s.source, s.span, s.raw)
            return result
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        return MemoryAccessReview('MEMORY_SNAPSHOT_READ_HOLD')


def inspect_stored_memory_input(path, pin, run, lease, lease_reference, clock, raw, expected_history=None):
    """One consistent read-only snapshot; compare exact bytes without returning them."""
    if not _pin_ok(pin) or not _valid_run(run) or type(raw) is not bytes or len(raw) > LIMIT:
        return 'MEMORY_SNAPSHOT_PIN_HOLD'
    try:
        with closing(_connect(path, 'ro')) as db:
            db.execute('BEGIN')
            if _head(db) != pin:
                return 'MEMORY_SNAPSHOT_CAS_HOLD'
            s, _, _ = _review_history(db, pin, expected_history)
            review = inspect_run_memory_access(s.run, run, s.nodes, s.target,
                s.tombstone, s.tombstone, s.acl, s.acl, lease, lease_reference, clock,
                s.source, s.span, s.raw)
            if not review.structural_match or review.reason != 'D0_MEMORY_ACCESS_MATCH_ONLY':
                return review.reason
            if raw != s.raw[s.span.start:s.span.end]:
                return 'JOINT_INPUT_SPAN_HOLD'
            return 'D0_MEMORY_INPUT_MATCH_ONLY'
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, AttributeError,
            OverflowError, RecursionError):
        return 'MEMORY_SNAPSHOT_READ_HOLD'
