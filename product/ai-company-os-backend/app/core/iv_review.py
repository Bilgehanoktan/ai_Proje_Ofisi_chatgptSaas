"""R07 D11: independent trust-plane shape checks, never issue receipt or release."""
from dataclasses import dataclass
from .runtime_preview import Scope, valid_scope, token, uint
from .t1_review import digest_ok


@dataclass(frozen=True)
class TrustPlane:
    principal_id: str
    root_id: str
    admin_id: str
    recovery_id: str


@dataclass(frozen=True)
class ArtifactPin:
    scope: Scope
    artifact_digest: str
    revision: int
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class IVObservation:
    artifact: ArtifactPin
    readback: ArtifactPin
    qa: TrustPlane
    iv: TrustPlane
    release: TrustPlane
    receipt_ref: str | None = None


@dataclass(frozen=True)
class IVReview:
    reason: str
    structural_match: bool = False
    decision: str = 'INCONCLUSIVE'
    independent_proven: bool = False
    receipt_issued: bool = False
    release_ready: bool = False


def valid_pin(p: object) -> bool:
    return (isinstance(p,ArtifactPin) and valid_scope(p.scope) and digest_ok(p.artifact_digest)
            and all(uint(x) for x in (p.revision,p.policy_epoch,p.witness_epoch)))


def plane_ids(p: TrustPlane) -> tuple[str, ...]:
    return p.principal_id,p.root_id,p.admin_id,p.recovery_id


def valid_plane(p: object) -> bool:
    return isinstance(p,TrustPlane) and all(token(x) for x in plane_ids(p))


def inspect_iv(o: IVObservation, current: ArtifactPin | None) -> IVReview:
    if (not isinstance(o,IVObservation) or not valid_pin(o.artifact) or not valid_pin(o.readback)
            or not valid_pin(current) or not all(valid_plane(p) for p in (o.qa,o.iv,o.release))
            or (o.receipt_ref is not None and not token(o.receipt_ref))):
        return IVReview('IV_ENVELOPE_INVALID')
    if o.artifact != o.readback or o.artifact != current:
        return IVReview('IV_ARTIFACT_READBACK_CAS_MISMATCH')
    # Reject shared identifiers across planes, including cross-category collisions.
    a,b,c = (set(plane_ids(p)) for p in (o.qa,o.iv,o.release))
    if a & b or a & c or b & c:
        return IVReview('IV_TRUST_PLANE_COLLISION')
    return IVReview('IV_TRUST_ROOT_UNPROVEN', structural_match=True)
