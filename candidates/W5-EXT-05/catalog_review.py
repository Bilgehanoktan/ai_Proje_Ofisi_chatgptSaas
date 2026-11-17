"""EXT-05 candidate: exact byte pins into existing Skill Engine; no loader or grants.
Trusted reference and scope are supplied by a local review harness, not authenticated.
Only trusted Python data objects; do not expose as a runtime API.
"""
from dataclasses import dataclass
from hashlib import sha1, sha256
import json
from app.core.agent_runtime.lifecycle import Scope, valid_scope
from app.engines.skill_engine.manifest_review import SkillManifestSample, inspect_skill
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities
from app.engines.model_gateway.registry import AdapterPin
from app.core.transaction.review import digest_ok

MAX_BYTES = 262144

@dataclass(frozen=True)
class Bundle:
    manifest: bytes
    input_schema: bytes
    output_schema: bytes
    artifact: bytes

@dataclass(frozen=True)
class CatalogReference:
    skill_id: str
    version: str
    manifest_sha256: str
    input_schema_sha256: str
    output_schema_sha256: str
    artifact_sha256: str
    artifact_git_blob: str
    source_path: str
    source_commit: str

@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool = False
    diagnostic_overlap: tuple[str, ...] = ()
    status: str = 'QUARANTINED'
    decision: str = 'HOLD'
    enabled: bool = False
    effective_tools: tuple[str, ...] = ()
    grant_created: bool = False
    dispatch_allowed: bool = False
    independent_verified: bool = False


def _hash(raw):
    return sha256(raw).hexdigest()


def _json(raw):
    obj = json.loads(raw)
    canonical = (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')
    if canonical != raw or type(obj) is not dict:
        raise ValueError('NONCANONICAL_JSON')
    return obj


def review_candidate(bundle, ref, request, scope, expected_scope, expected_role,
                     adapter, registry, requested, policy_tools):
    if type(bundle) is not Bundle or type(ref) is not CatalogReference:
        return Review('REFERENCE_HOLD')
    raws = (bundle.manifest,bundle.input_schema,bundle.output_schema,bundle.artifact)
    pins = (ref.manifest_sha256,ref.input_schema_sha256,ref.output_schema_sha256,ref.artifact_sha256)
    if any(type(b) is not bytes or not 0 < len(b) <= MAX_BYTES for b in raws):
        return Review('BYTE_LIMIT_HOLD')
    if any(not digest_ok(d) for d in pins) or tuple(map(_hash,raws)) != pins:
        return Review('BYTE_PIN_MISMATCH')
    if type(scope) is not Scope or type(expected_scope) is not Scope or not valid_scope(scope) or scope != expected_scope:
        return Review('SCOPE_HOLD')
    try:
        m, inp, out = map(_json,raws[:3])
        if set(m) != {'profile','skill_id','version','source','input_schema_sha256','output_schema_sha256','role_hints','tool_ids','tool_ids_semantics','enabled','g7_ref','g8_ref','license_ref','custody_ref'}:
            return Review('MANIFEST_SHAPE_HOLD')
        if (m['profile'] != 'EXT05_CATALOG_REVIEW_ONLY' or m['enabled'] is not False or
                m['g7_ref'] is not None or m['g8_ref'] is not None or
                m['tool_ids_semantics'] != 'DIAGNOSTIC_ONLY_NOT_REGISTERED'):
            return Review('AUTHORITY_HOLD')
        if (m['skill_id'],m['version']) != (ref.skill_id,ref.version):
            return Review('VERSION_HOLD')
        source = m['source']
        if (type(source) is not dict or set(source) != {'path','commit','git_blob','sha256','bytes','upstream_commit'} or
                source['path'] != ref.source_path or source['commit'] != ref.source_commit or
                source['git_blob'] != ref.artifact_git_blob or
                sha1(b'blob '+str(len(bundle.artifact)).encode()+b'\0'+bundle.artifact).hexdigest() != ref.artifact_git_blob or
                source['sha256'] != ref.artifact_sha256 or
                type(source['bytes']) is not int or source['bytes'] != len(bundle.artifact) or
                m['input_schema_sha256'] != ref.input_schema_sha256 or m['output_schema_sha256'] != ref.output_schema_sha256):
            return Review('SCHEMA_OR_SOURCE_BINDING_HOLD')
        roles, tools = m['role_hints'], m['tool_ids']
        if (type(roles) is not list or not roles or any(type(x) is not str for x in roles) or
                len(set(roles)) != len(roles) or type(tools) is not list or len(tools) != 1 or
                type(tools[0]) is not str):
            return Review('ROLE_OR_TOOL_SHAPE_HOLD')
        if (type(request) is not dict or set(request) != {'skill_id','version','role'} or
                request != {'skill_id':ref.skill_id,'version':ref.version,'role':expected_role} or
                type(expected_role) is not str or expected_role not in roles or
                scope.agent_instance_id != 'demo-ext05-'+expected_role or
                scope.principal_id != 'demo-ext05-principal-'+expected_role):
            return Review('ROLE_REQUEST_HOLD')
        if (inp['properties'] != {'skill_id':{'const':ref.skill_id},'version':{'const':ref.version},'role':{'enum':roles}} or
                inp['additionalProperties'] is not False or
                out['properties']['enabled'] != {'const':False} or
                out['properties']['effective_tools'] != {'const':[]}):
            return Review('SCHEMA_PROFILE_HOLD')
        manifest = SkillManifestSample(scope,ref.skill_id,ref.version,ref.manifest_sha256,
                                       ref.input_schema_sha256,ref.output_schema_sha256,tuple(tools))
        reference = SkillManifestSample(expected_scope,ref.skill_id,ref.version,ref.manifest_sha256,
                                        ref.input_schema_sha256,ref.output_schema_sha256,tuple(tools))
        pin = SourcePin(ref.skill_id,ref.version,ref.manifest_sha256,m['license_ref'],m['custody_ref'])
        base = inspect_skill(manifest,reference,expected_scope)
        if not base.structural_match:
            return Review(base.reason)
        if type(adapter) is not AdapterPin or adapter.effect_ceiling != ():
            return Review('ADAPTER_EFFECT_CEILING_HOLD')
        if requested == ():
            return Review('CAPABILITY_REQUEST_INVALID')
        # This is the existing resolver, not a new effective tool registry.
        cap = inspect_capabilities(manifest,reference,scope,pin,pin,adapter,registry,requested,policy_tools)
        return Review(cap.reason,cap.reason == 'INDEPENDENT_RECEIPTS_ABSENT',cap.diagnostic_overlap)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError):
        return Review('INVALID_CANDIDATE_HOLD')
