"""D0 model invocation envelope; immutable request reference, no execution or grant."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import (
    RunObservation, RunState, LeaseObservation, valid_scope, valid_lease, uint, token, inspect_lease,
)
from app.core.t1_review import digest_ok
from .provider_contract import ProviderRequest, ProviderReview, inspect_provider_request
from .registry import AdapterPin


@dataclass(frozen=True)
class InvocationEnvelope:
    run: RunObservation
    lease: LeaseObservation
    request: ProviderRequest
    primary: AdapterPin
    alternate: AdapterPin
    reservation_ref: str
    idempotency_key: str
    sample_cost_ceiling_minor: int


def _run_ok(run):
    return (isinstance(run, RunObservation) and valid_scope(run.scope)
            and run.state is RunState.RUNNING and uint(run.version) and uint(run.attempt))


def _shape_ok(envelope):
    return (isinstance(envelope, InvocationEnvelope) and _run_ok(envelope.run)
            and valid_lease(envelope.lease) and envelope.lease.scope == envelope.run.scope
            and isinstance(envelope.request, ProviderRequest) and envelope.request.scope == envelope.run.scope
            and token(envelope.reservation_ref) and token(envelope.idempotency_key)
            and uint(envelope.sample_cost_ceiling_minor) and envelope.sample_cost_ceiling_minor > 0)


def _digest(envelope, registry):
    body = dict(version='D0_MODEL_INVOCATION_V1', envelope=asdict(envelope),
                registry=[asdict(p) for p in registry])
    # Exact tuple order is part of this provisional binding profile.
    return sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def invocation_digest(envelope, registry):
    """Compute a candidate pin; this function cannot issue a trusted receipt."""
    if not _shape_ok(envelope):
        raise ValueError('MODEL_INVOCATION_SHAPE_HOLD')
    review = inspect_provider_request(envelope.request, envelope.primary, envelope.alternate, registry)
    if not review.structural_match:
        raise ValueError(review.reason)
    return _digest(envelope, registry)


def inspect_invocation(envelope, registry, expected_digest, current_run, current_lease, clock, raw):
    if not _shape_ok(envelope) or not digest_ok(expected_digest):
        return ProviderReview('MODEL_INVOCATION_SHAPE_HOLD')
    if not _run_ok(current_run) or envelope.run != current_run:
        return ProviderReview('MODEL_RUN_REFERENCE_HOLD')
    lease = inspect_lease(envelope.lease, current_lease, clock)
    if lease.freshness != 'FRESH':
        return ProviderReview('MODEL_LEASE_HOLD')
    review = inspect_provider_request(envelope.request, envelope.primary, envelope.alternate, registry)
    if not review.structural_match:
        return review
    if type(raw) is not bytes or len(raw) > 1024 * 1024 or sha256(raw).hexdigest() != envelope.request.input_digest:
        return ProviderReview('MODEL_INPUT_DIGEST_HOLD')
    if _digest(envelope, registry) != expected_digest:
        return ProviderReview('MODEL_INVOCATION_DIGEST_HOLD')
    # The reservation reference and ceiling are pinned labels, not a ledger observation.
    return ProviderReview('D0_MODEL_INVOCATION_MATCH_ONLY', True)
