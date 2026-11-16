# DOC-REV-0215 — signed external observation and parallel acceptance preparation

Parent `a4a6aba3e986927b4e2b0157028e6623c669864e`; source commit `76815dfd2401d7a81f1f9f0a112da06d8002fb2f`. 0214 source manifest was already published; CURRENT still pointed at 0213. This addendum corrects that handover discontinuity. 0214 historical source manifest records 18 recovered backend + two parser files, 66 Python / 14 Node diagnostic results including ten original wrapper cases (one restore residual); these counts were NOT rerun in 0215. Original six prepared 0213 fixtures remain NOT_RUN.

## Security / recovery (D-03, D-04)
New `external_claim_review.py`: typed, canonical Ed25519-signed external claim observation includes expected independent signing key hash, nonce/challenge, exact root/sequence, scope hash and sample tick window. A single read-only local SQLite transaction compares root and consumed claim. Real D0 restore of authority file after consumption produces LOCAL_DIVERGENCE_HOLD when compared with the fixture's fresh signed consumed observation. No match or absence allows dispatch, retry or release. 15 local tests pass. No change to existing 0211 wrapper or default execution path. Separate signer/key service, independently sourced monotonic head and trusted clock, authenticated command path, consume/fence through commit and effect gate are still required. D-03/D-04 remain OPEN; a restored local fixture or a stale expected pin is not independent security.

## PostgreSQL (P0)
`scripts/run_pg_acceptance_0215.py` verifies entire externally pinned product manifest and five exact DDL blobs before any run. Distinct local 0194 and 0196L database profiles; original suites 5+5+3, exact ACKs and counts, nonzero exit/skip/timeout -> HOLD. Credentials never written in reports; no install/create DB/remote/CI. 14 unit checks pass; actual PG13 and RLS NOT_RUN (no psycopg/PG, no full local checkout). Local preflight returns SOURCE_OR_DDL_HOLD. Original fixture users own candidate tables; tests are not non-owner RLS proof. See PG runbook.

## CEO / Office (P1)
Shared HistoricalEvidenceStrip now consumes historicalPresentation: exact sample identity, tenant/company/environment, task and full plan revision, sample-only lease and budget, unknown live count and HOLD placement/release/independent status. Original fixed parsers verified exact. Both existing lifecycle panels already import the shared strip; no cross-sample join, live KPI or geometry change. 17 strict TS/Node reference tests pass; not actual API/browsers or full TSX compile.

## Maintenance
Diagnose claim mismatch by checking separately acquired key/head/challenge and local readback; do not delete or replay consumed intent. If PG source/DDL/DSN/profile/result mismatch, stop and inspect isolated DB and logs locally, never reuse a suspect schema; original fixtures guard and clean up only their own schema. Revert only source delta, not authority state. No canonical API, DB/event schema or dependency change. No main, PROD, real providers or spend. 46 new checks; inherited 7/16 integration criteria (43.75%), not system maturity. 24-domain ordinal ratings unchanged.

[Catalog](../../catalog/revisions/TECHNICAL_CATALOG_0215.json) · [Evidence](../../releases/GITHUB_READBACK_0215.json) · [PG runbook](PG_RUNBOOK.md) · [Next](../../handover/NEXT_STEP_0215.md).
