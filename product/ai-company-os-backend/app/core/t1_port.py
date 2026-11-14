"""Future T1 adapter contract only. No database implementation or usable writer."""
from dataclasses import dataclass
from typing import Protocol, NoReturn

@dataclass(frozen=True)
class CommitIntent:
    tenant_id: str
    company_id: str
    environment_id: str
    aggregate_id: str
    expected_version: int
    idempotency_key: str
    intent_digest: str
    grant_ref: str
    policy_epoch: int
    witness_epoch: int
    lease_ref: str

class T1Port(Protocol):
    def commit(self, intent: CommitIntent) -> str:
        """Future: state CAS + fence + event + audit + outbox in one local commit."""
        ...

class DisabledT1:
    def commit(self, intent: CommitIntent) -> NoReturn:
        raise PermissionError("T1_DISABLED_NO_DEV_NO_F3")
