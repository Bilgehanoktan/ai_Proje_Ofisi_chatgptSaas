# W5-J2-R1 — D0 membership review / owner gate HOLD
Parent: `147502d831ab146b8825585fc7ac390f951beb84` (W5-J). Additive local delta; no canonical product changes, migration, provider call, spend, GitHub write or branch merge. Windows 170/170, integrity 105/105 and 94/94 are user-reported; original logs not supplied. Do not count Windows as new distinct tests or close its evidence archival gate.

## What changed and why
The original 0195 schema has one sample_reservations row per run; admission mapping increments outstanding once in the same transaction as run admission. 0196L sample_settlements only recognizes zero for D0_LOCAL_FAILURE_NO_EFFECT. Neither represents per-invocation usage. `membership_review.py` checks a proposed owner row projection against an independent expected reference; it cannot issue a receipt, read a real DB, enforce persistent uniqueness or establish custody. `test_physical_constraints.py` uses a disposable SQLite database and deliberately simplified test-only tables to test constraints, rollback, two connection contention and CAS behavior. It starts with an already-reserved balance; no second charge is implied. `test_membership_review.py` tests shape, scope, replay-key aliases, phase, balance sanity and quarantine. No external dependencies.

## Owner interface and physical mapping — proposal, not migration
| Logical data | Existing source | Required owner work |
|---|---|---|
| Scope, attempt, run, plan, principal, agent | run_heads / Scope / RunObservation | Exact scoped membership FK and owner readback; retain full scope |
| Project/effect | company run membership / W5-H ReceiptEffectPin / D5 | Resolve by owner; never derive from run ID |
| Admission ID, request digest, transaction | run_admissions | Keep separate from invocation idempotency and consume transaction |
| Budget ID, revision, currency, outstanding, recognized, unknown | sample_budgets | Current CAS under original T1 lock; independent owner readback |
| Run-level amount and budget revision | sample_reservations | Define allocation of run reservation or distinct owner debit; never both |
| Invocation, route, profile, key, reservation ID | ReceiptLookup, UsageBinding, invocation route | Persist exact immutable per-invocation membership; no alias to run reservation |
| Reservation/consume/usage/reconciliation pins and transactions | W5-D/H/I types, owner journal | Owner supplies independently read rows and pins, role separation, no invented receipt |
| Known usage and release | UsageEvidence, ReconciliationEvidence | Known cost only; recognized=actual, recognized+released=reserved; validate token/route ceilings through original W5 reviewers |
| Unknown | budget unknown_cost + owner outcome | Preserve outstanding; quarantine; no zero fill, automatic retry or settlement |
| Fence and epochs | run_leases / D5 protected authority | Recheck under owner lock through commit; no J2 authority implementation |

## Required physical constraints
Owner-scoped uniqueness on (tenant,company,environment,budget,reservation_id), (scope,invocation_idempotency_key), (scope,invocation_pin), (scope,membership_pin); identity survives retry/attempt/route changes. Unique receipt per membership/role and unique receipt identity across roles in scope (candidate fixture preference pending owner review). Composite scoped FKs; original T1 event/outbox/audit and receipt records in one transaction. Do not identify membership via aggregate outstanding or successful signature alone. Store historical issuance revision separately from current budget revision and from consume/reconcile transaction identity. Pin references are compared, not cryptographically authenticated by the new reviewer.

## Transaction acceptance specification (owner, NOT_RUN)
1. Existing root -> witness -> memory -> company stream -> run/lease/budget lock order; D5 authority, expiry-through-commit and CAS remain owner-controlled.
2. On admission/readback, decide explicitly whether an invocation allocates an existing reservation or receives an additional reserved debit. Never silently increment outstanding twice. Bound total allocations to authoritative available run-level reservation; prevent concurrent over-allocation and run-level failure release while membership is unresolved. No allocation algorithm is approved here.
3. On consume, insert unique economic identity and consumed receipt under original T1; commit all required writes or roll back; lost ACK requires independent readback, not retry.
4. For unknown outcome/cost, preserve outstanding and prohibit new effects until explicit owner reconciliation; require verified evidence, never infer zero. If evidence conflicts or cost exceeds ceiling, HOLD for owner review, not automatic adjustment.
5. On known usage, verify original W5 accounting, route ceiling and signed receipt under owner custody; atomically reconcile known amount and release unused balance exactly once with CAS and immutable receipts. Require full transaction write-role readback, not this projection alone.
6. PostgreSQL negative cases: concurrent same-key different attempt/route, reservation alias across invocations, receipt alias across roles, stale CAS/fence/epoch, scope/RLS, over-allocation, terminal release while unresolved, lost ACK after commit and before commit, rollback after every write stage, unknown->zero/retry, overrun, wrong receipt evidence, restore/revocation. D4/D5/ORG/Unified owners retain their own tests.

## Evidence and limits
49 tests in Python 3.13.5 / SQLite 3.46.1: 37 read-only unit tests (including subtests) + 12 disposable SQL fixture tests. No real PostgreSQL, no canonical owner adapter, no regression rerun of W5-J, no product build, no IV/H01 release. Test-only DDL does not implement full proposed schema or RLS; SQLite lock behavior is not PG concurrency proof. Supplied row set may be incomplete; absence never proves freshness. State labels, receipt cross-role uniqueness, 4096 row cap and proposed projection fields are engineering choices for candidate review, not ratified business rules. Current unknown flags are diagnostic only, not persisted by the reviewer. J2 remains HOLD; J3–J6 unchanged, J5 canonical PG NOT_RUN. Existing design/source scores 50/25 unchanged.

## Reproduce / diagnose / rollback
From this directory: `python -B -m unittest -v test_membership_review test_physical_constraints`. Missing or ambiguous membership: inspect owner projection and uniqueness indexes, not regenerate pins. Budget mismatch: inspect original owner CAS, issuance revision and source digest. UNKNOWN: retain reservation, escalate to owner; never rerun provider. Reproduce fixtures only in disposable temp dirs. Rollback: discard additive candidate folder; no existing product files or DB changed. Next J2-R2: T1/Budget owner approval and full allocation/receipt mapping before any canonical migration; coordinate D5 protected reader and actual PG tests after owner authorization.
