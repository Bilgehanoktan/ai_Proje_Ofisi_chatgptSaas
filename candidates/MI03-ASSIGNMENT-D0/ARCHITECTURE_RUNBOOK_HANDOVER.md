# MI03-GATE02 — assignment lifecycle D0 source candidate

Base 247813150153e4ad1f1c9eb574b9b991095a7c5c; common observed 61bb06efbba7544bfc68260ed8eb4d342cab9b8e. Existing G8 owner handoff remains unratified. This is an isolated source candidate, not a second runtime or product promotion. Existing proposal tables and HOLD notices remain unchanged. Fresh disposable SQLite only via initialize_assignment_ops; never migrate an existing database.

## Behavior
One ACCEPTED_D0 record per scoped run, append-only REVOKED_D0 revision 2, immutable rows, expected digest CAS, expiry HOLD, exact original pin required for revocation, stale sources deny readback. No automatic reassignment/reacceptance. Source uses existing ORG history/seat/team and Core historical reader/derive_request. Core adapter is static and NOT_RUN; caller owns separate historical cursor, not atomic across stores. Synthetic approval observations are never authority. All returns HOLD, no commit/dispatch/retry permission.

## Test and maintenance
From candidates/MI03-ASSIGNMENT-D0/ run python -I -B test_assignment_lifecycle.py. 20/20 actual local SQLite tests, three exact original source blobs, direct synthetic SQL seed. Copies of lifecycle/DDL in test folder match source blobs. Test log and exit retained. Existing OperationsStore writer and full Core adapter were not run. No actual owner issuance or P02 acceptance. If CAS or source mismatch: keep HOLD, inspect original pins and immutable record; never reset claim or overwrite history. Revoke only exact original retained pin. If setup fails, use a fresh disposable DB after diagnosis; no production migration. Rollback by isolating/reverting source candidate; no actual authority changes.

## Next
ORG/Core owners review one-run lifecycle/supersession/revocation semantics and exact source diff; run actual original OperationsStore + Core historical readback against owner fixture, then actual G8 P02-A–E with independent owner registry/member/assignment/role issuance. D4 physical role, publication barrier and G9 three-store tests remain separate. GATE01 and strict COMMIT are independent owner tracks. No workstation action, CI, merge, real effects or independent acceptance.
