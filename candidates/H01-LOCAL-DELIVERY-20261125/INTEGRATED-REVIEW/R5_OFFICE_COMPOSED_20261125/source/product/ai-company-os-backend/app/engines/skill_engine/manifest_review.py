"""R08 D08: disabled skill manifest review; no install, loader or capability grant."""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import Scope, valid_scope, token
from app.core.transaction.review import digest_ok


@dataclass(frozen=True)
class SkillManifestSample:
    scope: Scope
    skill_id: str
    version: str
    manifest_digest: str
    input_schema_digest: str
    output_schema_digest: str
    tool_ids: tuple[str, ...]
    g7_ref: str | None = None
    g8_ref: str | None = None
    enabled: bool = False


@dataclass(frozen=True)
class SkillReview:
    reason: str
    structural_match: bool = False
    status: str = 'QUARANTINED'
    enabled: bool = False
    grant_created: bool = False
    tool_allowed: bool = False


def valid_manifest(m: object) -> bool:
    return (isinstance(m,SkillManifestSample) and valid_scope(m.scope)
            and all(token(x) for x in (m.skill_id,m.version))
            and all(digest_ok(x) for x in (m.manifest_digest,m.input_schema_digest,m.output_schema_digest))
            and isinstance(m.tool_ids,tuple) and len(m.tool_ids) <= 128
            and all(token(x) for x in m.tool_ids) and len(set(m.tool_ids)) == len(m.tool_ids)
            and all(x is None or token(x) for x in (m.g7_ref,m.g8_ref)) and type(m.enabled) is bool)


def inspect_skill(m: SkillManifestSample, reference: SkillManifestSample | None,
                  expected_scope: Scope) -> SkillReview:
    if not valid_scope(expected_scope) or not valid_manifest(m) or not valid_manifest(reference):
        return SkillReview('SKILL_MANIFEST_REFERENCE_INVALID')
    if m.scope != expected_scope or reference.scope != expected_scope or m != reference:
        return SkillReview('SKILL_PIN_SCOPE_MISMATCH')
    if m.enabled:
        return SkillReview('SKILL_ENABLE_PROHIBITED')
    return SkillReview('F0_REVIEW_RECEIPT_ABSENT', structural_match=True)
