"""T1 adapter contract; physical mapping remains unratified."""
from dataclasses import dataclass
from typing import Protocol, NoReturn, Callable
from contextlib import AbstractContextManager
from app.core.transaction.review import (LogicalIntent, valid_intent, required_roles,
                                         WorkItemRequestDraft, T1Review, inspect_workitem_request)

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

@dataclass(frozen=True)
class CommitReceipt:
    transaction_ref: str
    committed_version: int
    request_digest: str

class TransactionSession(Protocol):
    def lock_and_validate(self, intent: LogicalIntent) -> None: ...
    def write_role(self, role: str, intent: LogicalIntent) -> None: ...
    def verify_write_set(self, intent: LogicalIntent, roles: frozenset[str]) -> CommitReceipt: ...
    def lock_transition(self, intent: LogicalIntent): ...
    def write_transition_role(self, role: str, intent: LogicalIntent, before, target) -> None: ...
    def read_transition(self, intent: LogicalIntent): ...

class LogicalT1Coordinator:
    """One transaction; no default mapping, runtime grant or independent acceptance."""
    def __init__(self, transaction: Callable[[], AbstractContextManager[TransactionSession]]):
        self._transaction = transaction

    def review_workitem_request(self, draft: WorkItemRequestDraft) -> T1Review:
        """Direction A review only; deliberately never calls the transaction factory."""
        return inspect_workitem_request(draft)

    def commit(self, intent: LogicalIntent) -> CommitReceipt:
        return self._commit(intent)

    def commit_transition(self, intent: LogicalIntent, before, target) -> CommitReceipt:
        from app.core.agent_runtime.transition_command import validate_transition
        validate_transition(before, target, intent)
        return self._commit(intent, (before, target))

    def _commit(self, intent, transition=None):
        if not valid_intent(intent):
            raise ValueError("T1_INTENT_INVALID")
        roles = required_roles(intent)
        if "BUDGET" in roles and not intent.budget_ref:
            raise ValueError("T1_BUDGET_REFERENCE_MISSING")
        with self._transaction() as session:
            session.lock_and_validate(intent)
            if transition is not None:
                from app.core.agent_runtime.transition_command import validate_transition
                from app.core.agent_runtime.lifecycle import RunObservation
                before, target = transition
                persisted = session.lock_transition(intent)
                if not isinstance(persisted, RunObservation) or persisted != before:
                    raise ValueError("T1_TRANSITION_PREIMAGE_MISMATCH")
                validate_transition(persisted, target, intent)
            for role in ("HEAD", "ADMISSION", "LEASE", "BUDGET", "MUTATION",
                         "FENCE", "EVENT", "OUTBOX", "AUDIT"):
                if role in roles:
                    if transition is None:
                        session.write_role(role, intent)
                    else:
                        session.write_transition_role(role, intent, before, target)
            if transition is not None:
                expected = RunObservation(before.scope, target, before.version+1, before.attempt)
                after = session.read_transition(intent)
                if not isinstance(after, RunObservation) or after != expected:
                    raise ValueError("T1_TRANSITION_POSTIMAGE_MISMATCH")
            receipt = session.verify_write_set(intent, roles)
            if (not isinstance(receipt, CommitReceipt)
                    or not isinstance(receipt.transaction_ref, str)
                    or not receipt.transaction_ref
                    or type(receipt.committed_version) is not int
                    or receipt.committed_version != intent.expected_version + 1
                    or receipt.request_digest != intent.request_digest):
                raise ValueError("T1_RECEIPT_MISMATCH")
        return receipt
