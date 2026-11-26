"""D0 registry readback. Labels are not authenticated principals."""
from dataclasses import dataclass, asdict
from .model import PrincipalPin, ReviewScope, digest, scope_digest, valid_scope, valid_roster
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok

@dataclass(frozen=True)
class RegistrySnapshot:
    scope_sha256: str
    revision: int
    issuer: str
    issuer_custody: str
    roster: tuple[PrincipalPin, ...]
    policy_epoch: int
    witness_epoch: int


def registry_digest(r: RegistrySnapshot) -> str:
    return digest({'profile': 'registry.v0-D0', 'registry': asdict(r)})


def inspect_registry(r: RegistrySnapshot, reference: RegistrySnapshot, expected: str,
                     scope: ReviewScope) -> bool:
    if (type(r) is not RegistrySnapshot or type(reference) is not RegistrySnapshot
            or not valid_scope(scope) or not digest_ok(expected) or not valid_roster(r.roster)
            or not uint(r.revision) or r.revision == 0 or not token(r.issuer)
            or not token(r.issuer_custody) or not uint(r.policy_epoch) or not uint(r.witness_epoch)):
        return False
    if r.scope_sha256 != scope_digest(scope) or (r.policy_epoch, r.witness_epoch) != (scope.policy_epoch, scope.witness_epoch):
        return False
    if r.issuer in {p.principal_id for p in r.roster} or r.issuer_custody in {p.custody_id for p in r.roster}:
        return False
    return r == reference and registry_digest(r) == expected
