"""SQLite staging candidate: immutable batches, not canonical T1 or trusted evidence."""
from dataclasses import asdict
import sqlite3
from .model import ReviewScope, digest, scope_digest
from .planner import ReviewPlan
from .evidence import Observation, inspect_evidence

DDL = """
CREATE TABLE IF NOT EXISTS development_evidence_d0 (
 scope_sha TEXT NOT NULL, plan_sha TEXT NOT NULL, seq INTEGER NOT NULL CHECK(seq BETWEEN 1 AND 7),
 evidence_id TEXT NOT NULL, previous_sha TEXT NOT NULL, entry_sha TEXT NOT NULL, body TEXT NOT NULL,
 PRIMARY KEY(scope_sha, seq), UNIQUE(scope_sha, evidence_id), UNIQUE(scope_sha, entry_sha));
CREATE TRIGGER IF NOT EXISTS development_evidence_no_update BEFORE UPDATE ON development_evidence_d0
 BEGIN SELECT RAISE(ABORT, 'IMMUTABLE_EVIDENCE'); END;
CREATE TRIGGER IF NOT EXISTS development_evidence_no_delete BEFORE DELETE ON development_evidence_d0
 BEGIN SELECT RAISE(ABORT, 'IMMUTABLE_EVIDENCE'); END;
"""
GENESIS = '0' * 64


def initialize_staging(db: sqlite3.Connection) -> None:
    """Explicit caller-owned isolated D0 connection only; never called on import."""
    if db.in_transaction:
        raise ValueError('STAGING_TRANSACTION_ACTIVE')
    db.executescript(DDL)


def stage_batch(db: sqlite3.Connection, scope: ReviewScope, reference: ReviewScope,
                plan: ReviewPlan, observations: tuple[Observation, ...],
                reference_observations: tuple[Observation, ...], outputs: tuple[bytes, ...],
                policy_epoch: int, witness_epoch: int, revoked: bool | None) -> str:
    import json
    review = inspect_evidence(scope, reference, plan, observations, reference_observations,
                              policy_epoch, witness_epoch, revoked, outputs)
    if not review.structural_match or db.in_transaction:
        return 'STAGING_HOLD'
    stream = scope_digest(scope)
    try:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM development_evidence_d0 WHERE scope_sha=? LIMIT 1', (stream,)).fetchone():
            db.rollback()
            return 'STAGING_DUPLICATE_HOLD'
        previous = GENESIS
        for seq, observation in enumerate(observations, 1):
            body = json.dumps(asdict(observation), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
            entry = digest({'scope': stream, 'plan': plan.plan_sha256, 'seq': seq, 'previous': previous, 'body': body})
            db.execute('INSERT INTO development_evidence_d0 VALUES (?,?,?,?,?,?,?)',
                       (stream, plan.plan_sha256, seq, observation.evidence_id, previous, entry, body))
            previous = entry
        db.commit()
        return 'D0_BATCH_STAGED_NOT_AUTHORITY'
    except sqlite3.Error:
        if db.in_transaction:
            db.rollback()
        return 'STAGING_DB_HOLD'


def inspect_staged(db: sqlite3.Connection, scope: ReviewScope, reference: ReviewScope,
                   plan: ReviewPlan, expected: tuple[Observation, ...],
                   evidence_reference: tuple[Observation, ...], outputs: tuple[bytes, ...],
                   policy_epoch: int, witness_epoch: int, revoked: bool | None) -> str:
    import json
    from .evidence import observation_digest
    review = inspect_evidence(scope, reference, plan, expected, evidence_reference,
                              policy_epoch, witness_epoch, revoked, outputs)
    if not review.structural_match or db.in_transaction:
        return 'STAGING_REFERENCE_HOLD'
    stream = scope_digest(scope)
    try:
        rows = db.execute('SELECT plan_sha,seq,evidence_id,previous_sha,entry_sha,body FROM development_evidence_d0 WHERE scope_sha=? ORDER BY seq', (stream,)).fetchall()
    except sqlite3.Error:
        return 'STAGING_DB_HOLD'
    if len(rows) != 7:
        return 'STAGING_INCOMPLETE_HOLD'
    previous = GENESIS
    for seq, (row, o, task) in enumerate(zip(rows, expected, plan.tasks), 1):
        body = json.dumps(asdict(o), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        entry = digest({'scope': stream, 'plan': plan.plan_sha256, 'seq': seq, 'previous': previous, 'body': body})
        if (o.task_id != task.id or o.scope_sha256 != stream or o.plan_sha256 != plan.plan_sha256
                or observation_digest(o) != o.evidence_sha256 or tuple(row) != (plan.plan_sha256, seq, o.evidence_id, previous, entry, body)):
            return 'STAGING_READBACK_HOLD'
        previous = entry
    return 'D0_STAGING_READBACK_MATCH_ONLY'
