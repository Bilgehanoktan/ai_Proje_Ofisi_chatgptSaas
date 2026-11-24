"""MEM-05D full-history recovery observation, never a writer or recovery authority."""
from contextlib import closing
from dataclasses import dataclass, field

from app.core.agent_runtime import memory_checkpoint as c, memory_witness as w
from app.core.agent_runtime.lifecycle import ClockSample, RunObservation, LeaseObservation, inspect_lease, uint
from app.engines.memory_engine import snapshot_store as s


@dataclass(frozen=True)
class MemoryRecoveryReview:
    reason: str
    history_match: bool = False
    checkpoint_match: bool = False
    pending_observation: str = 'UNVERIFIED'
    decision: str = field(default='HOLD', init=False)
    quarantine_required: bool = field(default=True, init=False)
    retrieval_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    transition_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    replay_allowed: bool = field(default=False, init=False)
    publish_allowed: bool = field(default=False, init=False)
    clear_pending_allowed: bool = field(default=False, init=False)
    prune_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)
    atomicity_verified: bool = field(default=False, init=False)


class _RecoveryHold(Exception):
    """Internal fixed diagnostic; never expose exception strings from owner readers."""


def _anchor_in_chain(reader, anchor, public_key, observation):
    """Use original full-chain verification and exact anchor membership in one read."""
    committed = []
    with closing(w._connect(reader.path, 'ro')) as db:
        db.execute('BEGIN')
        head = w._latest(db, public_key, committed)
        row = db.execute('SELECT digest,CASE WHEN length(body)<=4096 THEN body END '
                         'FROM memory_witness WHERE sequence=?', (anchor.sequence,)).fetchone()
        return ((head, tuple(committed)) == observation
                and row == (w.witness_sha(anchor), w.witness_bytes(anchor)))


def _checkpoint_prefix_matches(db, anchor, key_sha, pins, body):
    """Rebuild the original checkpoint summary from the already audited prefix."""
    revisions, retained = {}, 0
    for pin in pins[:anchor.snapshot.generation]:
        current = s._load(db, pin)
        metadata, _ = s._encode(current)
        retained += len(metadata) + len(current.raw)
        s._bind_revisions(revisions, current)
    return c._encode(anchor, key_sha, revisions, retained) == body


def _observe_memory(path, head, pins, anchor, key_sha, body, current_run):
    """One read-only transaction: exact observed head, entire history and anchor."""
    with closing(s._connect(path, 'ro')) as db:
        db.execute('BEGIN')
        observed = s._head(db)
        if observed == head.snapshot:
            history = pins
            state = 'BASE_ONLY' if head.pending is not None else 'NONE_OBSERVED'
        elif head.pending is not None and observed == head.pending:
            history = pins + (head.pending,)
            state = 'TARGET_OBSERVED'
        else:
            raise _RecoveryHold('MEMORY_RECOVERY_HEAD_MISMATCH_HOLD')
        snapshot, _, _ = s._review_history(db, observed, history)
        if snapshot.run != current_run or snapshot.run.scope != head.scope:
            raise _RecoveryHold('MEMORY_RECOVERY_RUNTIME_HOLD')
        if (snapshot.acl.policy_epoch, snapshot.acl.witness_epoch) != (head.policy_epoch, head.witness_epoch):
            raise _RecoveryHold('MEMORY_RECOVERY_RUNTIME_HOLD')
        if not _checkpoint_prefix_matches(db, anchor, key_sha, pins, body):
            raise _RecoveryHold('MEMORY_RECOVERY_CHECKPOINT_HOLD')
        return state


def _witness_unchanged(reader, expected, public_key, observation):
    try:
        return reader.read_history(expected, public_key) == observation
    except Exception:
        return False


def inspect_memory_recovery(path, reader, expected_witness, public_key,
                            checkpoint_body, checkpoint_signature, checkpoint_sha,
                            current_run, current_lease, lease_reference, clock):
    """Classify only Memory's observed state against externally supplied references.

    A matching pending target is historical evidence, not proof of T1 commit or
    permission to finalize. Base-only is absence, not proof of rollback. Full
    signed history is mandatory; the suffix-only fast path is never substituted.
    Repeated read-only observations detect some interleavings, not atomicity.
    If both stores AND all external references roll back, no local proof exists.
    """
    try:
        c._separate(path, reader)
        anchor, _, _, _ = c._decode(checkpoint_body, checkpoint_signature, checkpoint_sha,
                                    expected_witness, public_key)
        observation = reader.read_history(expected_witness, public_key)
        head, pins = observation
        if (type(current_run) is not RunObservation or not s._valid_run(current_run)
                or type(current_lease) is not LeaseObservation or type(lease_reference) is not LeaseObservation
                or type(clock) is not ClockSample or current_run.scope != head.scope
                or current_lease.scope != head.scope or lease_reference.scope != head.scope
                or not all(uint(v) for v in (clock.now_tick, clock.policy_epoch, clock.witness_epoch))
                or (head.policy_epoch, head.witness_epoch) != (clock.policy_epoch, clock.witness_epoch)
                or not head.issued_tick <= clock.now_tick < head.expires_tick
                or inspect_lease(current_lease, lease_reference, clock).freshness != 'FRESH'):
            return MemoryRecoveryReview('MEMORY_RECOVERY_RUNTIME_HOLD')
        if (anchor.scope != head.scope or anchor.sequence > head.sequence
                or anchor.recovery_epoch > head.recovery_epoch
                or anchor.snapshot.generation > len(pins)
                or pins[anchor.snapshot.generation - 1] != anchor.snapshot
                or not _anchor_in_chain(reader, anchor, public_key, observation)):
            return MemoryRecoveryReview('MEMORY_RECOVERY_CHECKPOINT_HOLD')
        args = (path, head, pins, anchor, expected_witness.key_sha, checkpoint_body, current_run)
        state = _observe_memory(*args)
        if not _witness_unchanged(reader, expected_witness, public_key, observation):
            return MemoryRecoveryReview('MEMORY_RECOVERY_CHANGED_HOLD')
        if _observe_memory(*args) != state or not _witness_unchanged(reader, expected_witness, public_key, observation):
            return MemoryRecoveryReview('MEMORY_RECOVERY_CHANGED_HOLD')
        reasons = {'NONE_OBSERVED': 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY',
                   'BASE_ONLY': 'D0_MEMORY_RECOVERY_PENDING_BASE_ABSENCE_NOT_PROOF',
                   'TARGET_OBSERVED': 'D0_MEMORY_RECOVERY_PENDING_TARGET_MATCH_ONLY'}
        return MemoryRecoveryReview(reasons[state], True, True, state)
    except _RecoveryHold as hold:
        return MemoryRecoveryReview(hold.args[0])
    except Exception:
        # Do not leak stored bytes or exceptions; never manufacture rollback proof.
        return MemoryRecoveryReview('MEMORY_RECOVERY_READ_HOLD')
