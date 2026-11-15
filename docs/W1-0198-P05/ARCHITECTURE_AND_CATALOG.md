# W1-0198-P05 — pinned fixture recovery and integration coverage

Parent 4ead00903f34e0226f0ca6475c89aaeacb9de364; source 13c95e63a9177b2664c44ac0bd4598ff24c7b0f0; full product branch integration/w1-0198-p05. Transport-only commit 54e6feb5bf95e3fe436bb81011bb53cb089a59a0, branch recovery/w1-0198-p05-fixture-pack, NEVER MERGE. The transport tree intentionally contains only the 44 original required source/fixture/DDL files plus 4 helper/lock files and README. All 44 source file Git blob IDs and sizes match P04. Static import/dependency inspection is not execution proof.

## What / why / where / how
A: tests/integration/lifecycle_p05_source_lock.json pins 39 product files with existing SHA-256 and Git blob/size and five candidate SQL files with exact Git blob/size. The full 44-file selection is based on P02/P03 test imports, package initializers, dependency modules and fixture/DDL reads; total 160282 bytes. No local whole-tree recovery; the connector can read and create Git objects but local GitHub checkout DNS/archive download blocked. The minimal transport tree reuses Git blobs; no source rewriting. It can be downloaded separately from the full source tree.
run_lifecycle_p05.py validates the lock against a hardcoded Git blob, checks every source byte and copies only pinned regular files from a directory or ZIP into a temporary empty stage. Existing interpreter >=3.10, SQLite >=3.37, FastAPI needed. Runs two exact modules via isolated Python interpreter and environment allowlist, testsRun and distinct IDs must match 8 + 9 and every case PASS; skips/errors/count mismatch fail; reports JSON and checks source bytes again. No dependency install, provider calls, CI, external write or real PostgreSQL. Process isolation is not an OS sandbox or security boundary. Dependency versions are recorded, not pinned environment acceptance. Failed/blocked runs remain HOLD/FAIL, no acceptance.
test_run_lifecycle_p05.py: 16 local tests, including directory/ZIP extraction, hash and path tampering, duplicate/nonregular members, wrong lock, actual child PASS/FAIL/SKIP/subtest and count mismatch.
test_lifecycle_ddl_p05.py: 7 local tests using five exact pinned SQL files, with SQLite dialect substitution already used by 0196-L tests, plus exact P04 snapshot reader. Validate 12-table count readback and unchanged DB bytes, unique task scope, orphan reservation/outbox FK constraints, budget bound, missing scoped head, write denial. Actual temporary SQLite tests, not real PostgreSQL or persisted lifecycle fixture API tests. Python 3.13.5, SQLite 3.46.1, FastAPI 0.128.2. All 23 new auxiliary/DDL tests passed; exact local test blobs match remote. No product sources changed; 306/306 product files retained. 17 actual P02/P03 cases NOT_RUN. Full frontend build/browser, backend suite, real PG and independent acceptance remain NOT_RUN/HOLD.
B–H: preserve P04 UI/session/join/lease/history contracts; no extra feature ahead of A gate. No scope join, freshness proof, model or memory retrieval, worker dispatch, or real cost.

## Maintenance / execution / rollback
Use full P05 branch or minimal transport archive. From extracted root run:
```
python tests/integration/run_lifecycle_p05.py --source . --report lifecycle-p05-evidence.json
```
If source pin fails, replace source with exact transport commit, never change pins to fit an unverified file. If missing Python dependencies, use previously reviewed isolated environment; runner installs nothing. Inspect per-case JSON. Source mismatch or test failure remains HOLD/FAIL; investigate using exact fixture and commit. No merge of transport branch: it deliberately omits unrelated files. Rollback to P04 full branch (no migration). No independent grant changed.

## Progress
Source 34.375%, design 71.875% descriptive ordinal averages unchanged. Integration coverage = (18 PARTIAL_INTEGRATED + 1 EDS_SLICE_INTEGRATED)/24 = 79.1667%; partial only = 75%; accepted = 0/24. This counts areas where source integration began, not the fraction of all integration work completed or operational product. No inflation.

## Next gate
P06 actual 17 fixture case execution on exact recovered source, fix actual failures, then pinned full suite and browser. Independent B–H may proceed only within existing plan dependencies; do not add historical endpoints in place of evidence. Windows deferred by user.
