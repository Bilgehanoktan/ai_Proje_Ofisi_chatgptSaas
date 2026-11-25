# DOC-REV-0210 — local fenced T1 and durable intent quarantine

Baseline `b9cd16ca6dbb6d8344c34b9446564af7d2a29040`; source `cd1dd5e61e259d4f16b94ae7e386e32730c8fd13`. 345 product files, 344 manifest entries; all 342 prior non-manifest blobs retained. Two product files added. No canonical API/event/DB migration or dependency version change.

## What / why / how
`fenced_transition.py` adds explicit D0-only `D0IntentJournal`, `IntentPin`, `FenceReview`, `local_revocation_fence` and `execute_fenced_transition`. Intent body, original transaction ref, joint/witness binding and exact scope digest are committed before T1. One attempt per exact scope; append-only outcomes are UNKNOWN or HISTORICAL. Absence of result is PENDING. All results are HOLD, no retry/release/provider permission. If T1 commit succeeds but result write fails, PENDING persists. If commit response is lost, UNKNOWN persists and original exact readback is historical only.

Local fixed lock order: stage journal and commit; reserve witness writer with BEGIN IMMEDIATE, then memory writer; original D0PostgresTransitionMapping and WitnessedTransitionMapping through original LogicalT1Coordinator/postgres_transaction; hold both local locks until commit/close; then append outcome. No real network/PG provider, no default wiring. Writer locks serialize existing cooperating SQLite append/publish APIs, not external pin service, filesystem replacement, clock or real provider effects. Separate paths verified against inode alias among three stores; T1 connector/clock/latest are trusted fixture dependencies.

## Evidence
154 actual selected tests, 138 regression +16 new, 0 fail/skip. 49 exact selected closure files (46 product, 3 DDL). 13 additionally recovered exact files (10 product, 3 DDL) are source-only, not test evidence. 32/55 locked core paths now local, 23 absent; 55 remote pins unchanged. 29 locked tests NOT_RUN. [Evidence](../../tests/evidence/TEST_EVIDENCE_0210.json).

## Residuals
D-03 local writer race passed; test also changes the external latest callback after last check, and D0 commit persists. Thus independent trust root/authoritative effect boundary still open. D-04 new reproduced: restoring journal + T1 pre-attempt images while memory witness remains unchanged permits a second local attempt. A restore-external intent head/claim and independent custody are needed. Do not solve by trusting a copied local journal. Local fixture keys and locks do not establish independent acceptance. Existing legacy diagnostic paths retained. Full Company/Terminal composition, PG13/RLS, core29 and full build/browser remain NOT_RUN.

## Maintenance / rollback
Use manifest `d8fbc81d6a0a8e409e92b906de9d86db2b65dd12`; verify exact original candidate DDL and source pins. Inspect immutable intent and exact receipt. Unknown/absence never proves rollback; no automatic retry or delete. Use historical readback only. Return to 0209 code commit if necessary, preserve journal/witness and all evidence; do not restore old data to replay. No canonical migrations applied. Main/CI/PROD/live authority unchanged.
