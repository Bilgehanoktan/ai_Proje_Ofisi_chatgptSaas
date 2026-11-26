"""R04/R05: synthetic projection freshness; no canonical owner or live join."""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok


@dataclass(frozen=True)
class ProjectionPin:
    tenant_id: str
    world_id: str
    environment_id: str
    layout_revision: str
    snapshot_sequence: int
    policy_epoch: int
    witness_epoch: int
    payload_digest: str
    observed_tick: int


@dataclass(frozen=True)
class ProjectionReview:
    reason: str
    structural_match: bool = False
    render_live_allowed: bool = False
    fallback: str = 'STATIC_LIST_OR_SVG'


def valid_projection(p: object) -> bool:
    return (isinstance(p, ProjectionPin) and p.tenant_id == 'synthetic-tenant'
            and p.environment_id == 'A0_SAMPLE_ONLY' and token(p.world_id) and token(p.layout_revision)
            and all(uint(x) for x in (p.snapshot_sequence, p.policy_epoch, p.witness_epoch, p.observed_tick))
            and digest_ok(p.payload_digest))


def inspect_projection(p: ProjectionPin, reference: ProjectionPin, layout_revision: str,
                       now_tick: int, max_age: int) -> ProjectionReview:
    if not valid_projection(p) or not valid_projection(reference) or not uint(now_tick) or not uint(max_age) or max_age == 0:
        return ProjectionReview('PROJECTION_REFERENCE_UNKNOWN')
    if p != reference:
        return ProjectionReview('PROJECTION_SCOPE_SEQUENCE_EPOCH_HOLD')
    if not token(layout_revision) or p.layout_revision != layout_revision:
        return ProjectionReview('LAYOUT_REVISION_HOLD')
    if now_tick < p.observed_tick or now_tick - p.observed_tick > max_age:
        return ProjectionReview('PROJECTION_STALE_HOLD')
    return ProjectionReview('CANONICAL_OWNER_UNPROVEN', True)
