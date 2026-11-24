"""R08: diagnostic capability intersection is not an effective grant."""
from dataclasses import dataclass
from ...core.runtime_preview import Scope, valid_scope, token
from ...core.skill_review import SkillManifestSample, inspect_skill
from ...core.t1_review import digest_ok
from ..model_gateway.registry import AdapterPin, exact_pin, valid_set


@dataclass(frozen=True)
class SourcePin:
    source_id: str
    revision: str
    raw_digest: str
    license_ref: str
    custody_ref: str


@dataclass(frozen=True)
class CapabilityReview:
    reason: str
    diagnostic_overlap: tuple[str, ...] = ()
    effective_tools: tuple[str, ...] = ()
    status: str = 'QUARANTINED'
    enabled: bool = False


def valid_source(p: object) -> bool:
    return (isinstance(p, SourcePin) and digest_ok(p.raw_digest)
            and all(token(v) for v in (p.source_id, p.revision, p.license_ref, p.custody_ref)))


def inspect_capabilities(skill: SkillManifestSample, reference: SkillManifestSample,
                         scope: Scope, source: SourcePin, expected_source: SourcePin,
                         adapter: AdapterPin, registry: tuple[AdapterPin, ...],
                         requested: tuple[str, ...], policy_tools: tuple[str, ...]) -> CapabilityReview:
    if not valid_scope(scope) or not inspect_skill(skill, reference, scope).structural_match:
        return CapabilityReview('SKILL_PIN_SCOPE_HOLD')
    if (not valid_source(source) or not valid_source(expected_source)
            or source != expected_source or source.raw_digest != skill.manifest_digest):
        return CapabilityReview('SKILL_SOURCE_PIN_HOLD')
    if not exact_pin(adapter, registry) or adapter.scope != scope:
        return CapabilityReview('ADAPTER_SCOPE_HOLD')
    if not valid_set(requested) or not valid_set(policy_tools):
        return CapabilityReview('CAPABILITY_REQUEST_INVALID')
    overlap = tuple(sorted(set(requested) & set(skill.tool_ids) & set(adapter.capabilities) & set(policy_tools)))
    if set(overlap) != set(requested):
        return CapabilityReview('CAPABILITY_HOLD', overlap)
    return CapabilityReview('INDEPENDENT_RECEIPTS_ABSENT', overlap)
