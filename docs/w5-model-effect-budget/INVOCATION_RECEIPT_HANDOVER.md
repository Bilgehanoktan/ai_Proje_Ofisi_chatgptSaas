# W5 — Invocation route binding and reservation/usage receipt port

Parent: db38b65dc1120cf5cc25222774295662f9d7d120. Only W5 source additions, no shared owner edits or merge. D0 review only.

InvocationRouteContext replays the exact routing record and existing invocation envelope against supplied run, lease, clock, raw bytes and catalog/metrics pins. It checks caller-nominated primary and alternate profiles, input/output token limits, capability and cost ceilings, then derives UsageBinding. A match is HOLD, never selection or dispatch. Input token count is an explicit synthetic reference, not a trusted tokenizer measurement.

ReceiptLookup binds the invocation idempotency and reservation identity. ReceiptReadback carries pinned reservation, usage and reconciliation observations and budget revision/source pin. ReservationUsageReceiptPort is an owner-supplied read-only Protocol with no implementation. Existing run-level admission CommitReceipt/sample_reservations and aggregate budget balances cannot establish per-invocation membership; do not reinterpret failure-only sample_settlements as actual model usage. The review checks supplied pins, exact identities, unknown-cost state and arithmetic/ceiling consistency, and retains HOLD even when everything matches. There is no ledger, schema, write path, API or provider integration.

Evidence: 62/62 actual isolated tests (21 new + 41 prior); 25 parent-exact files and 3 new file pins. Original 9 Effect & Budget tests were not rerun; exact dependency recovery blocked by incomplete transfer. Full regression PARTIAL. Source catalog and full local log hashes in companion records. No product score or authority changes.

Collision scope: current W5 plus seven active peer branches inspected (Core 0229-D4R2, Unified U3A, ORG-05R5, UI P10J24B, Office A5R3/A6, W5-EXT03); no matching new paths. No global tracker, shared Runtime, Budget, T1, DB, UI or sample_adapter mutation.

Maintenance: compare invocation/route/profile and scope/attempt/lease/fence pins, then budget source revision and independent receipt pins. Treat unknown result/cost and missing custody as HOLD, never synthesize evidence or retry blindly. Roll back only the W5 delta commit, no migration. Strict dual-candidate eligibility and reservation covering invocation ceiling are provisional D0 choices, not ranking/billing policy. Next: exact full regression and owner-approved durable receipt adapter contract, then integration review; no real provider calls, grants, spend or independent acceptance.
