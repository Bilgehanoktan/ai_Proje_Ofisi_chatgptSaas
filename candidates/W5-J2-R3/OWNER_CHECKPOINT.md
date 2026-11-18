# W5-J2-R3 — R03 owner checkpoint (proposal only)

## Source-confirmed incompatibilities
Sources are pinned in SOURCE_PINS.json. No changes to original files.

| Owner / original symbol | Existing semantics | Required owner decision |
|---|---|---|
| T1 `review.py:Operation/required_roles`, `port.py:LogicalT1Coordinator._commit` | ADMISSION (9 roles), STATE_MUTATION (6 base roles, optional lease/budget), TERMINAL (8); coordinator increments head version and iterates fixed nine role names | Define invocation phase commands and exact mandatory role coverage, including membership/receipt; either expand logical operations/roles or approve explicit subrecords under existing roles. Do not disguise allocation as ordinary transition. |
| T1 `postgres_transition_mapping.py:D0PostgresTransitionMapping.lock_and_validate` | Accepts only ordinary STATE_MUTATION with base roles and no budget_ref | No insertion through ordinary transition or default product startup. |
| Budget `postgres_admission_mapping.py` and 0195 DDL | Atomic run-level debit and run reservation, not invocation membership | Choose allocation from already reserved pool vs new independently funded reservation; R2 proposes the former. |
| Budget/T1 `postgres_lifecycle_mapping.py:D0PostgresLifecycleMapping` | Renewal or local failure only; locks original claim, lease and budget; verifies original recognized cost unchanged; terminal subtracts entire claim amount and inserts failure/no-effect settlement | Preserve untouched run behavior; add owner-reviewed partial-close contract, prevent old terminal entry point whenever historical/unresolved allocations exist; update admission/renewal readback semantics for recognized cost. No same-run capacity recycling by default. |
| D5 `intent_authority.py:D0IntentAuthority.claim_and_fence`, `fenced_transition.py:D0IntentJournal.stage` | Unique scope_sha per run, binding and transaction; one claim/run for original D0 fence | Define durable per-economic-effect identity without weakening the existing run-level fence; cannot bypass uniqueness or reissue claims. Separate invocation, admission, lease and transaction identities. |
| D5 `execute_authority_fenced_transition`, D5-C `fence_probe.py` | Existing protected-reader experiment stops before stage/T1; no production grant; original fence is local SQLite | Owner must supply real protected reader and prove expiry/revocation through COMMIT with common root publication, independent clock/key/head custody. |
| D4-R6 | Corrected RLS inventory 454; canonical PG acceptance NOT_RUN in pinned handover | Approve composite scoped FKs, FORCE RLS, least privilege, common lock order and independent readback. |
| W5 `fenced_transition.py:sample_result_bytes` | reservation_ref equals admission transaction_ref; fixed sample only | Never alias real invocation reservation to admission tx; owner-defined adapter and explicit capability phase required. |

## Proposed physical mapping for owner review (no DDL or migration)
Keep original scoped run_admissions/sample_reservations/run_heads/run_leases/sample_budgets and run_mutations/fences/events/outbox/run_audit. New physical names are not ratified. Logical records: pool allocation state (run issuance, unallocated, revision), membership (full R1 scope and durable identity), immutable role receipts (reservation/consume/usage/reconciliation), quarantine (explicit durable UNKNOWN) and owner-reviewed terminal remainder. Composite scoped references must include tenant/company/environment; no global id alone. Retain issuance, invocation allocation and current budget revisions separately. Existing W5-D lookup/readback and W5-H signed receipt remain contracts, not write permission.

## Shared transaction contract proposal
Do not implement a parallel writer. Owner must identify exact T1 operation + complete write-set for each phase. Order: root -> witness -> memory -> company stream -> run/lease/budget -> pool and membership (last sub-order TBD by owner); check protected reader before claim and again inside fence before stage/commit under same protected scope. Existing code checks D0 local sources only. New owner transaction must atomically update member/receipt/financial state and original mandatory T1 records, verify before/after and exact request+tx+economic identity, verify grant freshness through commit, and obtain independent readback from separate session. Never derive owner membership from run totals or promote D5-C diagnostic match to permission. No provider invocation or settlement enabled.

| Phase | Budget arithmetic | Required extra physical evidence (not approved roles) |
|---|---|---|
| ALLOCATE | outstanding unchanged; pool free decreases | immutable membership + reservation receipt, separate issuance/alloc revisions |
| CONSUME | no monetary delta | exact owner membership + unique consume receipt/economic key |
| USAGE | no monetary delta | actual token/cost source and consume receipt binding |
| RECONCILE | outstanding minus allocation, recognized plus actual | one reconciliation receipt; released = allocation - actual |
| UNKNOWN | outstanding preserved | sticky quarantine and independent resolution procedure |
| CLOSE_UNUSED | untouched pool only under current R2 experiment | original failure-only evidence, no member history |
| CLOSE_PARTIAL | proposed arithmetic: release only unallocated after all members reconciled | new terminal semantics; decision open, no write implementation |

## Terminal counterexample (actual R2 fixture, arithmetic comparison only)
Two runs share one budget: issuance A=60, B=40; outstanding=100. A allocates 20, consumes, records actual 12 and reconciles (release 8); outstanding=80, recognized=12, A free=40, B free=40. Legacy full-release subtraction of 60 would yield outstanding=20, under-reserving B by 20. Releasing only A's unallocated 40 would leave B's 40 outstanding. This is a hypothetical arithmetic comparison, not execution of original lifecycle mapping; its earlier recognized-cost check may reject first. New diagnostic does not write or approve either release. UNKNOWN or unresolved membership blocks arithmetic closure, including UNKNOWN on other run within the same fixture budget. No owner decision has been supplied.

## Required owner decision record
T1/Budget: choose R2 allocation policy, per-operation role strategy, partial terminal, CAS and immutable receipt schema. D5: per-effect claim granularity, protected reader and root/clock/restore behavior. D4: schema/role/lock/RLS plan. Independent reviewer: source custody and acceptance. All are missing here; user task does not substitute for independent signatures. Keep existing locks and canonical product untouched.

## PG execution prerequisites
R2 PG_ACCEPTANCE_PLAN.json lists 22 scenario descriptions, not runnable tests. Preserve IDs unchanged. Owner must implement each against approved physical mapping, provide reviewed disposable PG endpoint and role provisioning, exact source/lock pins, per-ID logs, rollback and independent readback. R3 checkpoint verifies inventory/hash and reports actual local environment only; no PG connection attempted, no substitute SQLite pass. D4 corrected 454 and D5 original 17 remain separate owner work; do not rerun or count here. No Windows raw J1 evidence supplied.
