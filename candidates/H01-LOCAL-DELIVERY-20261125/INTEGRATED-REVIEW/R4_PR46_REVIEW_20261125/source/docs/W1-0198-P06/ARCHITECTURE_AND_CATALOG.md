# W1-0198-P06 — Exact persisted fixture gate and selected regression

## What / why / where / how
P05 product remains byte-identical (306 product files, 305 manifest entries). No new API, DB schema, event, dependency, class or function. Recovered the exact 44-file P04 source closure (160282 bytes) using connector reads and verified reusable local bytes after direct GitHub checkout/archive failed. 39 product SHA-256 pins and all 44 Git blob/size pins matched before/after execution; 5 SQL files have blob/size pins only. Existing P05 runner unchanged; local execution used Python 3.13.5, SQLite 3.46.1, FastAPI 0.128.2. No real credentials, providers or external effects.

## Executed evidence
P02 8 + P03 9 = 17 previously NOT_RUN cases PASS. 0194 35 + 0195 19 + 0196-L 26 = 80 original regression cases PASS. 97 distinct case IDs; no failures/errors/skips in final runs. Initial regression report deliberately retained: 34 expected vs 35 actual for 0194, all 80 tests passed but gate failed count; corrected expected count and reran. No source/test edits. Reports are exact local bytes, verified by Git blob.

[Evidence index](../../tests/evidence/TEST_EVIDENCE_W1_0198_P06.json) · [Catalog](../../catalog/revisions/TECHNICAL_CATALOG_W1_0198_P06.json) · [Granular gates](../../progress/W1_0198_GATE_TRACKER.json).

## Reproduce / diagnose / maintain
Use the P05 source lock and existing runner with an exact P04 source checkout or recovered subset. The recovery transport branch is NEVER MERGE. In an isolated reviewed Python environment, from repo root run: `python -B tests/integration/run_lifecycle_p05.py --source <exact-source-root-or-archive> --report <new-report.json>`. For the additional regression, import the existing runner, use load_lock/materialize to a fresh temporary directory, run run_cases(stage, {'test_transition_mapping_0194':35,'test_admission_mapping_0195':19,'test_lifecycle_mapping_0196':26}), then recheck all pins with check_bytes. Count mismatch is a gate failure, not automatically a product test failure; inspect ran/cases/failures/errors/skipped. Pin mismatch is HOLD; do not edit recovered inputs. Preserve reports for all attempts. Rollback pointer: 0a8eb7b2cbfba65b2199f83f4ae2b45ba91404a8; no product rollback needed because product blobs unchanged.

## Scope and next
Selected persisted SQLite and direct API handler evidence only. Full backend, seven-endpoint frontend/backend parity, React/build/browser, actual PostgreSQL, independent acceptance and live authority remain NOT_RUN/HOLD. Historical readback is not trusted active state. Windows deferred by user. P07 follows existing A–H path ownership; read-only scope/clock/lease/reservation/ACL/W-A provenance, then causal projection only with exact proof. No main/CI/PROD, no new external effects.

## Measurement
Existing 24 ordinal area scores are unchanged. Fixed-denominator gates separately measure verified closure 44/44, selected tests 17/17 and regression 80/80. No inferred global weighted completion, no historical count addition.
