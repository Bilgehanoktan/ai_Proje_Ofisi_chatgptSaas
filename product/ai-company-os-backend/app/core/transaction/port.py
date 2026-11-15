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


# 0191: transaction orchestration contract; physical mapping remains unratified.
from contextlib import AbstractContextManager
from typing import Callable
from app.core.transaction.review import LogicalIntent, valid_intent, required_roles

@dataclass(frozen=True)
class CommitReceipt:
    transaction_ref: str
    committed_version: int
    request_digest: str

class TransactionSession(Protocol):
    def lock_and_validate(self, intent: LogicalIntent) -> None:
        """Lock head and validate authoritative scope, grant, epochs, lease and budget."""
        ...
    def write_role(self, role: str, intent: LogicalIntent) -> None:
        """Write within this session only; never commit independently."""
        ...
    def verify_write_set(self, intent: LogicalIntent, roles: frozenset[str]) -> CommitReceipt:
        """Read back exact persisted bindings inside the same transaction."""
        ...

class LogicalT1Coordinator:
    """Executable sequencing for isolated adapters; not a runtime grant or PG mapping.

    The supplied context manager must rollback on exceptions and commit on normal
    exit. No default adapter is installed. A receipt is returned only after exit.
    """
    def __init__(self, transaction: Callable[[], AbstractContextManager[TransactionSession]]):
        self._transaction = transaction

    def commit(self, intent: LogicalIntent) -> CommitReceipt:
        if not valid_intent(intent):
            raise ValueError("T1_INTENT_INVALID")
        roles = required_roles(intent)
        if "BUDGET" in roles and not intent.budget_ref:
            raise ValueError("T1_BUDGET_REFERENCE_MISSING")
        with self._transaction() as session:
            session.lock_and_validate(intent)
            for role in ("HEAD", "ADMISSION", "LEASE", "BUDGET", "MUTATION",
                         "FENCE", "EVENT", "OUTBOX", "AUDIT"):
                if role in roles:
                    session.write_role(role, intent)
            receipt = session.verify_write_set(intent, roles)
            if (not isinstance(receipt, CommitReceipt)
                    or not isinstance(receipt.transaction_ref, str)
                    or not receipt.transaction_ref
                    or type(receipt.committed_version) is not int
                    or receipt.committed_version != intent.expected_version + 1
                    or receipt.request_digest != intent.request_digest):
                raise ValueError("T1_RECEIPT_MISMATCH")
        return receipt
