"""MEM-04 D0 checkpoint: signed audit summary, suffix inspection, no pruning or authority."""
from contextlib import closing
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
import sqlite3

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from app.core.agent_runtime.lifecycle import ClockSample, Scope, token, uint, valid_scope
from app.core.t1_review import digest_ok
from app.core.agent_runtime import memory_witness as w
from app.engines.memory_engine import snapshot_store as s

PROFILE = 'aicos-d0-memory-checkpoint-v1'
MAX_CHECKPOINT_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CheckpointReview:
    reason: str
    suffix_match: bool = False
    snapshot_suffix: int = 0
    witness_suffix: int = 0
    accounted_bytes: int = 0
    retention: str = 'HOLD'
    decision: str = field(default='HOLD', init=False)
    prefix_reaudited: bool = field(default=False, init=False)
    retrieval_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    prune_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)


def _require(ok):
    if not ok:
        raise ValueError('MEMORY_CHECKPOINT_HOLD')


def _separate(path, reader):
    _require(type(reader) in (w.MemoryWitnessReader, w.D0MemoryWitnessStore)
             and not os.path.samefile(path, reader.path))


def _encode(head, key_sha, revisions, retained):
    rows = [[node, revision, digest, parents]
            for (node, revision), (digest, parents) in sorted(revisions.items())]
    body = s._json([PROFILE, w.witness_bytes(head).decode('ascii'), key_sha, retained, rows]).encode('ascii')
    _require(len(body) <= MAX_CHECKPOINT_BYTES)
    return body


def prepare_checkpoint(path, reader, expected, public_key):
    """Full audit before external signing. Caller must independently pin/sign the result."""
    _separate(path, reader)
    head, pins = reader.read_history(expected, public_key)
    _require(head.pending is None)
    with closing(s._connect(path, 'ro')) as db:
        db.execute('BEGIN')
        _require(s._head(db) == head.snapshot)
        snapshot, revisions, retained = s._review_history(db, head.snapshot, pins)
        _require(snapshot.run.scope == head.scope)
        body = _encode(head, expected.key_sha, revisions, retained)
    _require(reader.read_history(expected, public_key) == (head, pins))
    return body


def _decode(body, signature, checkpoint_sha, expected, public_key):
    _require(type(body) is bytes and 0 < len(body) <= MAX_CHECKPOINT_BYTES
             and digest_ok(checkpoint_sha) and sha256(body).hexdigest() == checkpoint_sha
             and type(signature) is bytes and len(signature) == 64
             and type(expected) is w.LatestWitnessPin and digest_ok(expected.record_sha)
             and digest_ok(expected.key_sha) and uint(expected.recovery_epoch)
             and type(public_key) is bytes and len(public_key) == 32
             and sha256(public_key).hexdigest() == expected.key_sha)
    key = Ed25519PublicKey.from_public_bytes(public_key)
    key.verify(signature, body)
    profile, anchor_bytes, key_sha, retained, rows = json.loads(body)
    _require(profile == PROFILE and key_sha == expected.key_sha
             and type(anchor_bytes) is str and uint(retained) and 0 < retained <= s.HISTORY_BYTES
             and type(rows) is list and 0 < len(rows) <= s.HISTORY_LIMIT * 512)
    anchor = w._decode(anchor_bytes.encode('ascii'))
    _require(anchor.pending is None and anchor.snapshot.generation <= s.HISTORY_LIMIT)
    revisions = {}
    for node, revision, digest, parents in rows:
        _require(token(node) and token(revision) and digest_ok(digest)
                 and type(parents) is list and len(parents) <= 512)
        pins = tuple(tuple(p) for p in parents)
        _require(all(len(p) == 3 and token(p[0]) and token(p[1]) and digest_ok(p[2]) for p in pins)
                 and tuple(sorted(pins)) == pins and len({p[0] for p in pins}) == len(pins)
                 and (node, revision) not in revisions)
        revisions[node, revision] = (digest, pins)
    _require(_encode(anchor, key_sha, revisions, retained) == body)
    return anchor, revisions, retained, key


def _prefix_count(db, table, column, anchor):
    # Fixed internal table/column names. No historical payload is fetched.
    count = db.execute(f'SELECT count(*) FROM (SELECT {column} FROM {table} '
                       f'WHERE {column}<? LIMIT ?)', (anchor, anchor)).fetchone()[0]
    minimum = db.execute(f'SELECT min({column}) FROM {table}').fetchone()[0]
    _require(count == anchor - 1 and minimum == 1)


def _witness_suffix(reader, anchor, expected, key):
    with closing(w._connect(reader.path, 'ro')) as db:
        db.execute('BEGIN')
        _prefix_count(db, 'memory_witness', 'sequence', anchor.sequence)
        old, pins, count = None, [], 0
        rows = db.execute('SELECT sequence,digest,CASE WHEN length(body)<=4096 THEN body END,'
                          'CASE WHEN length(signature)=64 THEN signature END FROM memory_witness '
                          'WHERE sequence>=? ORDER BY sequence LIMIT ?',
                          (anchor.sequence, w.MAX_RECORDS - anchor.sequence + 2))
        for seq, digest, body, sig in rows:
            current = w._decode(body)
            _require(seq == current.sequence == anchor.sequence + count
                     and digest == w.witness_sha(current) and type(sig) is bytes and len(sig) == 64)
            key.verify(sig, body)
            if old is None:
                _require(current == anchor)
            else:
                w._transition(old, current)
                if current.snapshot.generation != old.snapshot.generation:
                    pins.append(current.snapshot)
            old, count = current, count + 1
        _require(old is not None and old.pending is None and w.witness_sha(old) == expected.record_sha
                 and old.recovery_epoch == expected.recovery_epoch
                 and old.snapshot.generation == anchor.snapshot.generation + len(pins))
        return old, tuple(pins), count - 1


def _snapshot_suffix(path, anchor, head, pins, revisions, retained):
    with closing(s._connect(path, 'ro')) as db:
        db.execute('BEGIN')
        _require(s._head(db) == head.snapshot and head.snapshot.generation <= s.HISTORY_LIMIT)
        _prefix_count(db, 'snapshots', 'generation', anchor.snapshot.generation)
        row = db.execute('SELECT digest,graph FROM snapshots WHERE generation=?',
                         (anchor.snapshot.generation,)).fetchone()
        _require(row == (anchor.snapshot.digest, anchor.snapshot.graph_digest))
        previous = s._load(db, anchor.snapshot)
        _require(previous.run.scope == anchor.scope)
        initial_count = len(revisions)
        s._bind_revisions(revisions, previous)
        _require(len(revisions) == initial_count)
        for pin in pins:
            row = db.execute('SELECT digest,graph,length(metadata),length(raw) FROM snapshots '
                             'WHERE generation=?', (pin.generation,)).fetchone()
            _require(row is not None and row[:2] == (pin.digest, pin.graph_digest)
                     and all(uint(n) and n <= s.LIMIT for n in row[2:]))
            retained += row[2] + row[3]
            _require(retained <= s.HISTORY_BYTES)
            current = s._load(db, pin)
            s._check_successor(previous, current)
            s._bind_revisions(revisions, current)
            previous = current
        return retained


def inspect_checkpoint_suffix(path, reader, body, signature, checkpoint_sha,
                              expected, public_key, scope, clock):
    """Read-only suffix diagnostic. Retained prefix payloads are NOT re-audited."""
    try:
        _separate(path, reader)
        anchor, revisions, retained, key = _decode(body, signature, checkpoint_sha, expected, public_key)
        head, pins, count = _witness_suffix(reader, anchor, expected, key)
        _require(type(scope) is Scope and valid_scope(scope) and head.scope == scope
                 and type(clock) is ClockSample
                 and all(uint(v) for v in (clock.now_tick, clock.policy_epoch, clock.witness_epoch))
                 and (head.policy_epoch, head.witness_epoch) == (clock.policy_epoch, clock.witness_epoch)
                 and head.issued_tick <= clock.now_tick < head.expires_tick)
        retained = _snapshot_suffix(path, anchor, head, pins, revisions, retained)
        _require(_witness_suffix(reader, anchor, expected, key) == (head, pins, count))
        retention = ('LIMIT_HOLD' if head.snapshot.generation == s.HISTORY_LIMIT
                     or retained == s.HISTORY_BYTES or head.sequence == w.MAX_RECORDS
                     else 'RETAIN_ONLY')
        return CheckpointReview('D0_CHECKPOINT_SUFFIX_MATCH_ONLY', True, len(pins), count,
                                retained, retention)
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, AttributeError,
            OverflowError, RecursionError, InvalidSignature):
        return CheckpointReview('MEMORY_CHECKPOINT_READ_HOLD')
