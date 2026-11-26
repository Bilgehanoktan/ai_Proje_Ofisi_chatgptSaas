"""0209 opt-in D0 T1 verification transition decorator; no provider/effect grant."""
from dataclasses import asdict
from hashlib import sha256
import json

from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import validate_transition
from app.core.agent_runtime.joint_context import joint_context_digest
from app.core.agent_runtime.memory_witness import LatestWitnessPin, inspect_witnessed_context
from app.core.transaction.review import valid_intent, digest_ok, required_roles
from app.core.transaction.port import CommitReceipt


def binding_digest(intent, context, registry, witness):
    """Pin the original intent without changing its transition-digest profile."""
    if not valid_intent(intent) or type(witness) is not LatestWitnessPin:
        raise ValueError('WITNESSED_T1_BINDING_HOLD')
    e = context.invocation
    validate_transition(e.run, RunState.VERIFYING, intent)
    if (e.run.state is not RunState.RUNNING or intent.lease_or_budget_changes
            or intent.budget_ref is not None or intent.lease_ref != e.lease.lease_id
            or intent.grant_ref != e.lease.grant_id or intent.idempotency_key != e.idempotency_key
            or (intent.policy_epoch, intent.witness_epoch) != (e.lease.policy_epoch, e.lease.witness_epoch)
            or not digest_ok(witness.record_sha) or not digest_ok(witness.key_sha)):
        raise ValueError('WITNESSED_T1_BINDING_HOLD')
    body = ['aicos-d0-witnessed-t1-v1', asdict(intent), joint_context_digest(context, registry), asdict(witness)]
    return sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


class WitnessedTransitionMapping:
    """Compose with original T1 ordinary mapping; restrict RUNNING -> VERIFYING.

    observe(cursor) supplies fresh synthetic lease, clock and external latest pin.
    Two checks are inside the original transaction, before roles and before receipt.
    Post-check refers to the locked *preimage*, not a claim of a RUNNING postimage.
    No real ledger reservation or atomic external effect proof. No default wiring.
    """
    def __init__(self, mapping, context, registry, witness, expected_binding,
                 memory_path, reader, public_key, raw, observe):
        self._mapping = mapping
        self._context, self._registry, self._witness = context, registry, witness
        self._expected_binding, self._memory_path, self._reader = expected_binding, memory_path, reader
        self._public_key, self._raw, self._observe = public_key, raw, observe
        self._intent = self._before = None
        self._post_read = self._finished = False

    def _guard(self, i):
        if self._intent is None or self._intent != i or self._finished:
            raise ValueError('WITNESSED_T1_INTENT_HOLD')

    def _check(self, c):
        lease, clock, latest = self._observe(c)
        if latest != self._witness:
            raise ValueError('WITNESSED_T1_LATEST_HOLD')
        r = inspect_witnessed_context(self._context, self._registry,
            joint_context_digest(self._context, self._registry), self._memory_path,
            self._before, lease, clock, self._raw, self._reader, latest, self._public_key)
        if not r.structural_match or r.reason != 'D0_WITNESSED_CONTEXT_MATCH_ONLY':
            raise ValueError(r.reason)

    def lock_and_validate(self, c, i):
        if self._intent is not None or binding_digest(i, self._context, self._registry, self._witness) != self._expected_binding:
            raise ValueError('WITNESSED_T1_BINDING_HOLD')
        self._mapping.lock_and_validate(c, i)
        self._intent = i

    def write_role(self, c, role, i):
        raise ValueError('WITNESSED_T1_TRANSITION_ONLY')

    def lock_transition(self, c, i):
        self._guard(i)
        if self._before is not None:
            raise ValueError('WITNESSED_T1_REUSE_HOLD')
        before = self._mapping.lock_transition(c, i)
        if before != self._context.invocation.run:
            raise ValueError('WITNESSED_T1_PREIMAGE_HOLD')
        self._before = before
        self._check(c)
        return before

    def write_transition_role(self, c, role, i, before, target):
        self._guard(i)
        if self._before is None or before != self._before or target is not RunState.VERIFYING or self._post_read:
            raise ValueError('WITNESSED_T1_TRANSITION_HOLD')
        self._mapping.write_transition_role(c, role, i, before, target)

    def read_transition(self, c, i):
        self._guard(i)
        if self._before is None or self._post_read:
            raise ValueError('WITNESSED_T1_TRANSITION_HOLD')
        after = self._mapping.read_transition(c, i)
        self._post_read = True
        return after

    def verify_write_set(self, c, i, roles):
        self._guard(i)
        if not self._post_read or roles != required_roles(i):
            raise ValueError('WITNESSED_T1_WRITE_SET_HOLD')
        receipt = self._mapping.verify_write_set(c, i, roles)
        if (type(receipt) is not CommitReceipt or receipt.request_digest != i.request_digest
                or type(receipt.committed_version) is not int or receipt.committed_version != i.expected_version+1):
            raise ValueError('WITNESSED_T1_RECEIPT_HOLD')
        self._check(c)
        self._finished = True
        return receipt
