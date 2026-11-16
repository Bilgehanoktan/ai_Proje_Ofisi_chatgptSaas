# AI Company OS — 0213 architecture and integration record

Baseline `e33ffb633bc5a445aec1fb4946625884d503c348`, branch `integration/0213-cross-domain-gates`. Scope: isolated D0, real local SQLite, no grants/provider calls. Current product source changed by **two new tests only**, plus a standalone offline diagnostic script. Existing product logic, API, DB migrations, event contracts, dependencies and earlier decisions unchanged. 350 product manifest entries (+2) and 351 product files including manifest.

## What / why / where / how

- **C: multi-project coordinator** — `tests/test_company_multiproject_0213.py` derives synthetic `plan-b` with distinct canonical plan revision, creates a second scoped run roster, registers a second project and project cap, calls original `D0PostgresAdmissionMapping` within `CompanyCoordinatedMapping` / `LogicalT1Coordinator` on original disposable SQLite schema. Four new tests: two projects reserve against one budget (20+20), project B cap violation rolls back, simultaneous claims with stale history give one winner, and wrong plan is rejected. These are *real SQLite data changes*, not PostgreSQL isolation claims. Original single-project 6 pass retained.
- **B: full guard chain** — `tests/test_authority_wrapper_0213.py` prepares six tests using original `test_fenced_transition_0210` and `test_witnessed_sql_0209` fixtures. This test source was syntax-checked, but **NOT_RUN** because 0209–0210 witness / snapshot dependencies are not present in the 55-file local slice. Source state cannot be promoted to integration success.
- **A: recovery reproducibility** — `scripts/diagnostic_preflight_0213.py` checks SHA-256, Git blob hash and length on all 55 source locks and reports direct package versions; with explicit `--run-diagnostic`, runs the 56-test selected suite. Its result is always `acceptance=HOLD`, never a pin-complete acceptance.

## Actual evidence

Local 55/55 pinned content validation. 56/56 original/selected diagnostic unittest results (52 prior selected and 4 new), including one deliberately reproduced restore residual, not a safety assertion. 4/4 new multi-project tests passed. Bundle preflight re-ran and found FastAPI, Starlette and Uvicorn mismatch. Full backend/frontend build, browser, PostgreSQL 13, RLS and 6 prepared exact wrapper tests: NOT_RUN.

## Remaining security architecture

Authority SQLite is not independent restore-proof custody. If attacker/backup can roll back authority + journal + T1, replay is possible (D-04). External witness publication timing (D-03), cryptographic key custody, clock, revocation, actual effect fencing (D-01/D-02), and strict non-owner PostgreSQL RLS remain independent acceptance HOLD. No default dispatch, provider or spend path was enabled.

## Recovery and rollback

Diagnose by comparing pinned blob digests and last authenticated commit; check pool revision, per-project cap, T1 receipt and `company_event_order` in one transaction; treat unknown commit as quarantine pending independent readback. Roll back only new test/script/docs, **never** rewind or delete consumed intent claims or history. Maintain separate W1 UI and other architecture branches; no automatic merges.

References: [catalog](../../catalog/revisions/TECHNICAL_CATALOG_0213.json), [evidence](../../releases/GITHUB_READBACK_0213.json), [gates](../../progress/INTEGRATION_GATES_0213.json), [next](../../handover/NEXT_STEP_0213.md).
