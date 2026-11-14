"""R07: immutable byte evidence and receipt pin checks; never verify a real signature."""
from dataclasses import dataclass
from hashlib import sha256
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok
from app.core.policy.iv_review import ArtifactPin, IVObservation, IVReview, inspect_iv, valid_pin


@dataclass(frozen=True)
class ReceiptPin:
    receipt_id: str
    artifact: ArtifactPin
    signer_id: str
    issuer_root: str
    key_id: str
    key_revision: int
    readback_digest: str
    valid_from_tick: int
    valid_until_tick: int
    revoked: bool


def valid_receipt(r: object) -> bool:
    return (isinstance(r, ReceiptPin) and valid_pin(r.artifact)
            and all(token(x) for x in (r.receipt_id, r.signer_id, r.issuer_root, r.key_id))
            and all(uint(x) for x in (r.key_revision, r.valid_from_tick, r.valid_until_tick))
            and r.valid_from_tick < r.valid_until_tick and type(r.revoked) is bool
            and digest_ok(r.readback_digest))


def inspect_receipt(o: IVObservation, current: ArtifactPin, receipt: ReceiptPin | None,
                    reference: ReceiptPin | None, raw: bytes, readback: bytes, now_tick: int,
                    tombstone_clear: bool | None) -> IVReview:
    base = inspect_iv(o, current)
    if not base.structural_match:
        return base
    if (not valid_receipt(receipt) or not valid_receipt(reference)
            or receipt != reference or receipt.artifact != current or not uint(now_tick)):
        return IVReview('IV_RECEIPT_REFERENCE_HOLD')
    if (receipt.receipt_id != o.receipt_ref or receipt.signer_id != o.iv.principal_id
            or receipt.issuer_root != o.iv.root_id):
        return IVReview('IV_SIGNER_SCOPE_HOLD')
    if receipt.revoked or not receipt.valid_from_tick <= now_tick < receipt.valid_until_tick:
        return IVReview('IV_KEY_OR_VALIDITY_HOLD')
    if tombstone_clear is not True:
        return IVReview('IV_TOMBSTONE_UNKNOWN_HOLD')
    if (type(raw) is not bytes or type(readback) is not bytes or len(raw) > 1024*1024 or len(readback) > 1024*1024
            or sha256(raw).hexdigest() != current.artifact_digest
            or sha256(readback).hexdigest() != receipt.readback_digest or raw != readback):
        return IVReview('IV_BYTES_READBACK_HOLD')
    return IVReview('IV_SIGNATURE_ROOT_CUSTODY_UNPROVEN', structural_match=True)
