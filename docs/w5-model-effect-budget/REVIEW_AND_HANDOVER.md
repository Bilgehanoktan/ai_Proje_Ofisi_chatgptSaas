# W5 / area 09 — mandatory effect and budget proof review
Baseline 167e5239882dc7b49bd96647412fe6761da0be5e (0227). D08/D14/D21; D30-05A. This is a scoped design checkpoint, not a normative ADR or new grant.
## Findings
- model_gateway/runtime_binding.py pins reservation_ref and ceiling but explicitly does not observe a ledger.
- model_gateway/sample_adapter.py checks a diagnostic effect, skill and gateway; no actual model invocation.
- budget_engine/reservation_review.py checks scope, revision, currency, epochs, UNKNOWN and capacity; it creates no reservation.
- core/policy/gateway_review.py checks grant, lease, witness and effect binding; structural match still DENY (PEP_ISOLATION_NOT_PROVEN).
- model_gateway/gateway.py remains DisabledModelGateway.
## Next implementation contract
Reuse existing owners. Before a model invocation can even be considered for authorization, bind the exact invocation digest to a committed reservation receipt (reservation identity, budget identity, amount/currency, idempotency, scope, policy/witness epochs), current run/lease/fence and exact logical effect identity. Verify against independently obtained current observations, not caller-supplied matching objects. A capacity match is not a reservation receipt. Unknown cost, stale revision, missing receipt, mismatch, revocation or missing independent custody must HOLD/DENY. No provider call or spend from this review. Actual effect remains outside T1; do not add a second authority.
## Acceptance matrix (NOT_RUN)
Missing receipt; wrong reservation id; wrong budget id; wrong scope; wrong currency; insufficient amount; wrong idempotency; stale policy/witness epoch; stale lease/fence; UNKNOWN cost; wrong invocation/effect digest; revoked grant; matching synthetic references still DENY; real receipt without independent custody still HOLD; concurrent revoke/consume and restore residual require independent boundary tests.
## Catalog delta
Documentation only. Existing files above unchanged; no new class/function/API/DB/event/dependency. Source candidate not yet implemented. Design/source scores 50/25 unchanged; no new test or integration gate.
## Isolation and handover
Separate branch from pinned 0227. Historical workstream/0196-memory-model is behind; P10J24b and unified-u2 diverge and touch sample_adapter.py, so do not modify that file or merge those branches. Other active branches not exhaustively diffed. Next: inspect actual committed reservation readback and intent authority contracts, then implement a deny-only binding candidate in a new module with exact-source tests. Do not modify shared runtime, UI, PostgreSQL or current global handover. Rollback: revert this documentation commit on this branch only. Troubleshooting: compare pinned invocation, reservation and effect identity; preserve UNKNOWN and never retry blindly. No network, provider, spend, CI, main or PROD authorization.
