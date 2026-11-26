"""Compose the original review with trust and staging readback; never promote or dispatch."""
from dataclasses import dataclass, field
from .model import ReviewScope
from .planner import ReviewPlan
from .identity_registry import RegistrySnapshot
from .trusted_policy import PolicySnapshot
from .policy import FileReadback, inspect_patch_bytes
from .evidence import Observation
from .trust_boundary import TrustPin, inspect_trust
from .staging_readback import BatchPin, StagedRow, ReplayPin, inspect_batch


@dataclass(frozen=True)
class ReadbackReview:
    reason: str
    matched: tuple[str, ...] = ()
    batch_sha: str | None = None
    decision: str = 'HOLD'
    source_write_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)


def inspect_readback(scope: ReviewScope, reference: ReviewScope, plan: ReviewPlan,
                     registry: RegistrySnapshot, registry_ref: RegistrySnapshot,
                     policy: PolicySnapshot, policy_ref: PolicySnapshot,
                     trust: TrustPin, trust_ref: TrustPin, trust_sha: str,
                     now: int, max_age: int, pe: int, we: int, revoked: bool | None,
                     parent_manifest: bytes, files: tuple[FileReadback, ...],
                     observations: tuple[Observation, ...], observation_ref: tuple[Observation, ...],
                     outputs: tuple[bytes, ...], batch: BatchPin, batch_ref: BatchPin,
                     rows: tuple[StagedRow, ...], schema: bytes, schema_sha: str,
                     replay: tuple[ReplayPin, ...], replay_ref: tuple[ReplayPin, ...]) -> ReadbackReview:
    t = inspect_trust(trust, trust_ref, trust_sha, scope, plan, registry, registry_ref,
                      policy, policy_ref, now, max_age, pe, we, revoked)
    if not t.structural_match:
        return ReadbackReview(t.reason)
    p = inspect_patch_bytes(scope, reference, parent_manifest, files)
    if not p.structural_match:
        return ReadbackReview(p.reason, ('trust-shape',))
    b = inspect_batch(scope, reference, plan, observations, observation_ref, outputs, trust,
                      batch, batch_ref, rows, schema, schema_sha, replay, replay_ref, pe, we, revoked)
    if not b.structural_match:
        return ReadbackReview(b.reason, ('trust-shape', 'patch-shape'))
    return ReadbackReview('READBACK_MATCH_NO_AUTHORITY', ('trust-shape', 'patch-shape', 'staging-shape'), b.batch_sha)


def project_readback(r: ReadbackReview) -> dict:
    # Never treats structural matches as test PASS or a live status.
    return {'profile': 'development-readback.v0-D0', 'data_status': 'SYNTHETIC_ONLY',
            'decision': 'HOLD', 'matched_shapes': list(r.matched) if type(r) is ReadbackReview else [],
            'runtime': 'NOT_RUN', 'actual_agent_count': None, 'release_allowed': False}
