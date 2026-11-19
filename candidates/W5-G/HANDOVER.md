# W5-G — Physical receipt mapping / D0 owner handoff

Parent: 01bc99b5fe30aa4f0f0be3dfdfcf64e8b0d2f836. Core reference: D4-R6 c42beeb9f8ed7e5fc0ec83c2fdaccf6563a8607a. This is a read-only diagnostic and mapping contract, not an implementation of DurableReceiptOwnerPort, a grant, a migration or product acceptance.

## Physical crosswalk and ownership

| W5 contract | Existing physical source | Limit |
|---|---|---|
| Scope and attempt | run_heads | Current run only; no historical invocation binding |
| BudgetSnapshot | sample_budgets | Company budget aggregate; full run scope is not stored there |
| ReservationEvidence | sample_reservations + run_admissions | One record per run, admission request digest and transaction; no invocation/reservation ID, profile/route pin or receipt custody |
| UsageEvidence | none in inspected owner schema | No input/output token counts, actual charge or provider receipt |
| ReconciliationEvidence | sample_settlements | Failure-only run release, recognized_minor=0; not invocation reconciliation |
| OwnerReceiptSnapshot | none in inspected owner schema | No per-invocation coherent snapshot or independent provenance |

T1 owns membership/atomicity, Budget owns reservation/recognition/release, PEP owns effect authority, IV owns independent verification. Do not copy a run-level reservation into multiple invocation receipts, infer actual usage from a quote/zero settlement, treat an admission transaction hash as receipt custody, or treat current aggregate revision as historical proof. The existing W5-D/E/F interfaces are unchanged. No new ledger, table, API, dependency, writer or gateway entrypoint.

## Diagnostic and evidence

run_level_receipt_diagnostic.sql: one parameterized SELECT against the existing five owner tables; fixed synthetic scope plus exact run/plan/task/agent/principal/attempt predicates, full scoped joins, budget identity/epoch/currency/revision/balance checks, and failure-settlement detection. All returned rows are HOLD with three false flags. Empty result, malformed result, exception or unavailable session is HOLD at the caller. It is not an identity, freshness, RLS, complete T1 write-set or authorization check. The query has no owner port caller and is not part of product startup.

Actual local tests: 16/16, Python 3.13.5 / SQLite 3.46.1, using four byte-exact Git-pinned DDL files (schema qualifier and parameter placeholders adapted only in memory); foreign keys enabled, query-only for SELECT, fixture writes for setup/negative cases. PostgreSQL, RLS, real provider, independent custody and full W5 90-test rerun NOT_RUN in this turn. Previous 90 PASS remains historical evidence only. No global promotion. Direct git network DNS failed; original DDLs recovered from GitHub connector and blob hashes verified.

## Parallel boundaries and next

Branch inventory 183 at initial check, 184 before branch creation. W5, D4-R6, D3, ORG-06, ORG-05R5R3, EXT-06, Unified U3A, P10J24B, A6 trees examined; candidate paths not present in those references. Four DDL blobs shared; A6 admission writer differs, so not an integration base. No other branch or shared product paths changed. W5-G is a new isolated branch from the pinned W5 head; the previous W5 branch stays untouched.

Provisional D0 design choice: the diagnostic is a standalone SQL artifact, not a runtime adapter, until T1/Budget owners agree to a per-invocation identity, immutable membership, coherent read, unique idempotency and accounting state contract. W5-H can specify independent receipt custody and PEP checks but cannot validate or enable a real provider against these rows. W5-I/J require owner mapping and approved integration. Scores stay 50/25. Real calls, spending, grants, merges and independent acceptance remain HOLD.

Maintenance: from repo root run `python -B candidates/W5-G/test_physical_mapping.py`. A pin mismatch stops the test; inspect owner changes, do not update pins to make it pass. PostgreSQL query execution requires separate reviewed isolated owner scope and test permission. Rollback: discard this candidate branch or revert only its additive delta; no data/migration changes.
