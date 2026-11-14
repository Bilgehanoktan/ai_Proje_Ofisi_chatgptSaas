"""D14/D16 R1 candidate. Pure reference checks; no external witness or restore writer."""
from dataclasses import dataclass
from .runtime_preview import Scope, valid_scope, token, uint
from .t1_review import digest_ok


@dataclass(frozen=True)
class WitnessSample:
    scope: Scope
    root_id: str
    epoch: int
    sequence: int
    record_digest: str
    observed_tick: int


@dataclass(frozen=True)
class WitnessReview:
    reason: str
    structural_match: bool = False
    decision: str = 'HOLD'
    authoritative: bool = False
    dispatch_allowed: bool = False


def valid_witness(w: object) -> bool:
    return (isinstance(w, WitnessSample) and valid_scope(w.scope) and token(w.root_id)
            and uint(w.epoch) and uint(w.sequence) and w.sequence > 0
            and digest_ok(w.record_digest) and uint(w.observed_tick))


def inspect_witness(sample: WitnessSample | None, reference: WitnessSample | None,
                    scope: Scope, expected_epoch: int, now_tick: int, max_age: int) -> WitnessReview:
    if not valid_scope(scope) or not all(uint(v) for v in (expected_epoch, now_tick, max_age)) or max_age == 0:
        return WitnessReview('WA_CONTEXT_INVALID', decision='DENY')
    if not valid_witness(sample) or not valid_witness(reference):
        return WitnessReview('WA_REFERENCE_MISSING')
    if sample.scope != scope or reference.scope != scope:
        return WitnessReview('WA_SCOPE_MISMATCH', decision='DENY')
    if sample.epoch != expected_epoch or reference.epoch != expected_epoch:
        return WitnessReview('ERR_WA_EPOCH_STALE', decision='DENY')
    if sample != reference:
        return WitnessReview('WA_REFERENCE_MISMATCH', decision='DENY')
    if now_tick < reference.observed_tick or now_tick - reference.observed_tick > max_age:
        return WitnessReview('WA_OBSERVATION_NOT_FRESH')
    return WitnessReview('WA_INDEPENDENT_ROOT_UNPROVEN', structural_match=True)


@dataclass(frozen=True)
class RestoreObservation:
    scope: Scope
    restore_id: str
    backup_revision: str
    old_witness: WitnessSample
    new_witness: WitnessSample
    unknown_effect_keys: tuple[str, ...]


@dataclass(frozen=True)
class RestoreReview:
    reason: str
    structural_match: bool = False
    mode: str = 'RECOVERY_READ_ONLY'
    reopened: bool = False
    old_authority_reusable: bool = False
    replay_allowed: bool = False


def inspect_restore(r: RestoreObservation, reference: WitnessSample | None,
                    now_tick: int, max_age: int) -> RestoreReview:
    if (not isinstance(r, RestoreObservation) or not valid_scope(r.scope) or not token(r.restore_id)
            or not token(r.backup_revision) or not valid_witness(r.old_witness)
            or not valid_witness(r.new_witness) or not isinstance(r.unknown_effect_keys, tuple)
            or len(r.unknown_effect_keys) > 1000 or not all(token(x) for x in r.unknown_effect_keys)
            or len(set(r.unknown_effect_keys)) != len(r.unknown_effect_keys)):
        return RestoreReview('RESTORE_ENVELOPE_INVALID')
    old, new = r.old_witness, r.new_witness
    if old.scope != r.scope or new.scope != r.scope or old.root_id != new.root_id:
        return RestoreReview('RESTORE_SCOPE_OR_ROOT_MISMATCH')
    if new.epoch <= old.epoch or new.sequence <= old.sequence or new.observed_tick < old.observed_tick:
        return RestoreReview('RESTORE_MONOTONIC_FENCE_REQUIRED')
    check = inspect_witness(new, reference, r.scope, new.epoch, now_tick, max_age)
    if not check.structural_match:
        return RestoreReview(check.reason)
    if r.unknown_effect_keys:
        return RestoreReview('UNKNOWN_RECONCILIATION_REQUIRED', structural_match=True)
    return RestoreReview('INDEPENDENT_RESTORE_AND_NEW_ADMISSION_REQUIRED', structural_match=True)
