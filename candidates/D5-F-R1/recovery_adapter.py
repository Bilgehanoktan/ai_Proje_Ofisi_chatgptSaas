"""D5-F-R1: opt-in diagnostic composition of original 0205-R and D5-E.

SQLite fixture only. No new authority, writer, checkpoint format, recovery
orchestration or independent custody. All results are HOLD.
"""
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
import os
import sqlite3

from app.core.event_store.company_coordination import SCOPE
from app.core.event_store.company_recovery import WitnessReader, review_recovery


@dataclass(frozen=True)
class PublicationRecoveryReview:
    reason: str
    company_reason: str | None = None
    local_match: bool = False
    mode: str = field(default='RECOVERY_READ_ONLY', init=False)
    decision: str = field(default='HOLD', init=False)
    independent_verified: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    replay_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    publish_allowed: bool = field(default=False, init=False)
    finalize_allowed: bool = field(default=False, init=False)


def _ro(path):
    p = Path(path)
    if not p.is_absolute() or p.resolve() != p or not p.is_file():
        raise ValueError('D5FR1_PATH_HOLD')
    db = sqlite3.connect(p.as_uri()+'?mode=ro', uri=True, timeout=2)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('BEGIN')
    except Exception:
        db.close()
        raise
    return db


def _observation(authority, owner_path):
    # Reuse exact D5-E history validation, on a read-only snapshot.
    with closing(_ro(authority.path)) as db:
        if db.execute('SELECT count(*) FROM publication_versions').fetchone()[0] > 5000:
            raise ValueError('D5FR1_HISTORY_LIMIT_HOLD')
        if db.execute('SELECT count(*) FROM publication_final').fetchone()[0] > 5000:
            raise ValueError('D5FR1_HISTORY_LIMIT_HOLD')
        root_seq, root = authority._head(db)
        if root_seq != 1 or db.execute('SELECT count(*) FROM roots').fetchone() != (1,):
            raise ValueError('D5FR1_ROOT_HISTORY_HOLD')
        pin, pending = authority._publication_state(db, root_seq)
        parent = db.execute('SELECT parent_sha FROM publication_versions WHERE seq=?', (pin.sequence,)).fetchone()[0]
    with closing(_ro(owner_path)) as db:
        owners = db.execute('SELECT sha FROM owner_state LIMIT 2').fetchall()
        if len(owners) != 1 or type(owners[0][0]) is not str:
            raise ValueError('D5FR1_OWNER_READBACK_HOLD')
        owner = owners[0][0]
    return root, pin, pending, parent, owner


def review_publication_recovery(*, authority, owner_path, company_cursor,
        members, pool, events, witness_reader, expected_witness_sha,
        expected_company_epoch, expected_root, expected_publication, expected_scope):
    """Two separately pinned observations; never a joint atomic snapshot.

    Caller owns a consistent read-only company cursor and retains both pins
    outside restored stores. The adapter cannot prove their custody or bind the
    company witness to IAM publication. D5-E is the exact derived fixture,
    not the product writer. Its owner_state is synthetic. No callbacks to mutate.
    """
    try:
        if (expected_scope != SCOPE or type(expected_scope) is not tuple
                or type(expected_company_epoch) is not int or expected_company_epoch <= 0
                or type(witness_reader) is not WitnessReader):
            return PublicationRecoveryReview('D5FR1_INPUT_HOLD')
        # Root and company epochs/digests are independent, not aliases.
        expected_root.validate(); expected_publication.validate()
        paths = [authority.path, Path(owner_path), witness_reader.path]
        if any(os.path.samefile(a,b) for i,a in enumerate(paths) for b in paths[i+1:]):
            return PublicationRecoveryReview('D5FR1_STORE_ALIAS_HOLD')
        before = _observation(authority, owner_path)
        company = review_recovery(company_cursor,members,pool,events,witness_reader,expected_witness_sha)
        after = _observation(authority, owner_path)
        if before != after:
            return PublicationRecoveryReview('D5FR1_OBSERVATION_DRIFT_HOLD', company.reason)
        if company.recovery_epoch != expected_company_epoch:
            return PublicationRecoveryReview('D5FR1_COMPANY_PIN_HOLD', company.reason)
        # Additional witness read detects a change after the company review.
        if witness_reader.read_latest(expected_witness_sha).recovery_epoch != expected_company_epoch:
            return PublicationRecoveryReview('D5FR1_COMPANY_PIN_HOLD', company.reason)
        root, pin, pending, parent, owner = after
        if type(expected_root) is not type(root) or root != expected_root:
            return PublicationRecoveryReview('D5FR1_ROOT_PIN_HOLD', company.reason)
        if type(expected_publication) is not type(pin) or pin != expected_publication:
            return PublicationRecoveryReview('D5FR1_PUBLICATION_PIN_HOLD', company.reason)
        if pending:
            reason = ('D5FR1_PENDING_TARGET_MATCH_ONLY' if owner == pin.owner_sha else
                      'D5FR1_PENDING_BASE_ABSENCE_NOT_PROOF' if owner == parent else
                      'D5FR1_PENDING_OWNER_MISMATCH_HOLD')
            return PublicationRecoveryReview(reason, company.reason)
        if owner != pin.owner_sha:
            return PublicationRecoveryReview('D5FR1_OWNER_READBACK_HOLD', company.reason)
        if company.reason != 'D0_RECOVERY_CHECKPOINT_MATCH_READ_ONLY' or not company.checkpoint_match:
            return PublicationRecoveryReview('D5FR1_COMPANY_UNKNOWN_HOLD', company.reason)
        return PublicationRecoveryReview('D5FR1_LOCAL_MATCH_ONLY', company.reason, True)
    except Exception:
        return PublicationRecoveryReview('D5FR1_EXTERNAL_OR_READBACK_HOLD')
