# W5 — Durable receipt, offline provider preflight, Runtime review

Parent: 8570530ef149ef91524037b9d7609bdb205d06f4. D0 source candidate only; no global promotion. W5-C 71 previous tests + 19 new tests = 90/90 PASS on Python 3.13.5; 48 parent-exact and 4 new files verified against Git blob identities. The previous incomplete source transfer is superseded by exact recovery; the original nine Effect & Budget tests ran unchanged. No full product, DB, real provider or independent acceptance.

W5-D: `OwnerReceiptSnapshot`, `DurableReceiptOwnerPort.read_snapshot`, `owner_snapshot_digest`, `inspect_owner_snapshot`. Compare a proposed per-invocation, coherent owner observation, externally supplied reference/pin, budget revision and receipt evidence. No implementation of owner port, DB access or issuance. T1 owns atomic writes and per-invocation membership proof, Budget owns reservation/recognition/release, PEP owns authority. Existing run-level sample_reservations, CommitReceipt and failure-only settlements are not per-invocation usage receipts. No second ledger.

W5-E: `inspect_provider_preflight` reuses route and owner receipt review, requires reservation-only snapshot, rejects usage/reconciliation/unknown outcomes and non-SAMPLE providers. No executable adapter, SDK, transport, credentials, model selection or actual usage.

W5-F: `inspect_runtime_model` compares existing RunObservation and LeaseObservation, checks latest supplied clock via preflight. No live Runtime wiring, state mutation, retry, dispatch or effect. Memory/skill/tool/PEP boundaries unchanged. A match is HOLD; current input provenance, independent custody, PEP atomic enforcement and real persistence remain open.

Collision check: 176 branch inventory; latest Core D4-R3, ORG-05R5R3, W5-EXT04/05, Unified U3A, P10J24B and Office A6 inspected. New W5 paths absent. No shared code edits. Do not merge or promote. Provisional D0 choices: snapshot equality and digest; preflight rejects any prior usage/reconciliation; exact Runtime run and lease equality. No claim of atomic read or independent authority.

Maintenance: verify original source pins, run all six W5 test modules; check owner snapshot identity/revision, invocation and receipt pins, budget scope/epoch and current run/lease. Unknown outcomes must be reconciled by owner, not repeated. Rollback: revert only this W5 delta; no schema changes. Next: owner-approved physical receipt mapping and independent custody, effect/PEP integration review, then controlled runtime wiring subject to gates. Scores 50/25 unchanged.
