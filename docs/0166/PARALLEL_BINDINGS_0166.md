# Parallel D01–D07 binding plan — 0166
Source: exact 0162-C ZIP candidates, 0162-D findings; all open, no source modification or independent acceptance. Required fields below are proposals, not ratified canonical fields.

|Finding|Observed candidate location|Next binding and negative oracle|
|---|---|---|
|D01|terminal_review.py inspect_terminal 85–106|Pin reservation membership to admission/budget/lease/effect + independent reservation readback, not inequality of IDs. Same budget, foreign reservation => HOLD.|
|D02|terminal_review.py 114–140|Independent before/after state bytes + state digests and exact HEAD/FENCE/AUDIT row IDs; same request digest with changed state or row ID => HOLD.|
|D03|terminal_review.py 91–113|Separate SUCCEEDED receipt/verified effect from control-plane stop authority; artifact/receipt digest alone insufficient. Unknown outcome => retain exposure; stale worker cannot stop.|
|D04|reconciliation_review.py 56–73|Pin send_intent_ref, claim owner/generation, fence, exact send record and issuer proof to receipt; existing truthy send_intent_ref is insufficient. Same effect but wrong send/claim => HOLD.|
|D05|settlement_review.py 87–91|Require authoritative reconciliation result (not caller-shaped ReconciliationPin), terminal evidence and amount provenance. Shape-matching unverified receipt => HOLD.|
|D06|settlement_review.py 92–97|Economic event identity/digest and CAS expected revision separate; authoritative unique lookup before CAS. Same event after head advance => duplicate/no posting; changed amount => conflict.|
|D07|settlement_review.py 63–71, 95–104|Reservation membership/outstanding readback and currency exponent/version, tariff/quantity/rounding provenance, integer minor-unit bounds. Foreign reservation or unsupported currency => HOLD.|

W2: keep OfficeV0 55 fields and backend 20 crosswalks separate; no owner receipt. W3/W4 physical R03 4/5/7 and single T1 commit unresolved. W6 IV existing receipt_review.py unchanged; new trust boundary is not an IV signature validator. W7 unknown cost/exposure retained. Next exact scope proposal covers 0165 five candidates + 0166 four new candidates as separate slices, not authorization.
