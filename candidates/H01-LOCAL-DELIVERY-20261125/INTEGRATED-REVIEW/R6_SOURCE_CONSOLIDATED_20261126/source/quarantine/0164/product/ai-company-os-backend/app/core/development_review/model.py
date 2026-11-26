"""Local review vocabulary; not a canonical contract or authenticated identity."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import re
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok

PROFILE = 'development-review.v0-D0'
ROLES = ('orchestrator', 'research', 'engineer', 'qa', 'security', 'independent-verifier', 'policy-review')
# Only the new review module and its candidate test. No glob, arbitrary path or runtime policy edits.
TARGETS = frozenset('app/core/development_review/' + p for p in (
    '__init__.py', 'model.py', 'planner.py', 'policy.py', 'evidence.py')) | {'tests/test_development_review_0164.py'}


def digest(value: object) -> str:
    """D0 Python serialization profile only; not an interoperable signing format."""
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class FilePin:
    path: str
    old_sha256: str | None
    new_sha256: str


@dataclass(frozen=True)
class ReviewScope:
    tenant_id: str
    company_id: str
    environment_id: str
    review_id: str
    parent_commit: str
    parent_manifest_sha256: str
    policy_epoch: int
    witness_epoch: int
    files: tuple[FilePin, ...]


@dataclass(frozen=True)
class PrincipalPin:
    role: str
    principal_id: str
    custody_id: str
    execution_id: str


def valid_file(p: object) -> bool:
    return (type(p) is FilePin and type(p.path) is str and p.path in TARGETS
            and (p.old_sha256 is None or digest_ok(p.old_sha256))
            and digest_ok(p.new_sha256) and p.old_sha256 != p.new_sha256)


def valid_scope(s: object) -> bool:
    return (type(s) is ReviewScope and s.tenant_id == 'synthetic-tenant'
            and s.company_id == 'synthetic-company' and s.environment_id == 'A0_SAMPLE_ONLY'
            and token(s.review_id) and type(s.parent_commit) is str
            and re.fullmatch(r'[0-9a-f]{40}', s.parent_commit) is not None
            and digest_ok(s.parent_manifest_sha256) and uint(s.policy_epoch) and uint(s.witness_epoch)
            and type(s.files) is tuple and 1 <= len(s.files) <= len(TARGETS)
            and all(valid_file(p) for p in s.files)
            and tuple(p.path for p in s.files) == tuple(sorted({p.path for p in s.files})))


def scope_digest(s: ReviewScope) -> str:
    if not valid_scope(s):
        raise ValueError('REVIEW_SCOPE_INVALID')
    return digest({'profile': PROFILE, 'scope': asdict(s)})


def valid_principal(p: object) -> bool:
    return (type(p) is PrincipalPin and type(p.role) is str and p.role in ROLES
            and all(token(v) and v.startswith('demo-') for v in
                    (p.principal_id, p.custody_id, p.execution_id)))


def valid_roster(roster: object) -> bool:
    if type(roster) is not tuple or len(roster) != len(ROLES) or not all(valid_principal(p) for p in roster):
        return False
    return (tuple(p.role for p in roster) == ROLES
            and all(len({getattr(p, a) for p in roster}) == len(ROLES)
                    for a in ('principal_id', 'custody_id', 'execution_id')))
