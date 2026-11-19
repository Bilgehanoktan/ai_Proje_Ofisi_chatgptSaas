# MI03-GATE02-ASSIGNMENT-RECOVERY-79 — D0 assignment Store recovery regression

## What/why/where/how
Existing selected 71 cases re-executed with original 32 exact G6A/G7/G8/GATE03 file blobs. Eight **new** Python unittest cases run in disposable SQLite, without modifying original product/source or candidate. New files in locally delivered 45-entry ZIP: `tests/test_assignment_db_recovery_01.py` and `run_integrated_79.py`; SHA-256 anchored in EVIDENCE.json. Combined 79/79 actual PASS, all 32 original Git blob/source SHA-256 pins before/after, 44/44 ZIP-extracted SHA256SUMS, independent rerun 79/79 PASS.

## Critical security limit: demonstrated counterexample
An old SQLite snapshot **plus old retained ZERO pin** permits re-creating the same synthetic ACCEPTED_D0 decision digest. This test intentionally passes because it **reproduces a weakness**. An old DB with independent **new** retained pin returns MISSING_HOLD. Neither outcome grants real authority (every D0 review is HOLD). Do not count expected vulnerability reproduction as safety acceptance; require independently monotonically custodied owner/intent head and strict protected publication/COMMIT before any live effect.

## Two originally requested blockers, honestly classified
- **GATE02 genuine Core assignment positive:** NOT_RUN. Existing 32-file stage deliberately lacks `app.core.development_review.research_slice` and `plan_history_review`; independent original canonical Research SQL/fixture and transitive source must be pinned and run. Existing 71 includes fail-closed missing-Core diagnostics, not positive acceptance.
- **Memory–T1 original 0214 ten:** 0/10 NOT_RUN. Needs original 265 backend manifest/source bytes, G6A exact two-source overlay and three owner DDL, cryptography 46.0.4; local GitHub network/checkout unavailable. Earlier 42 direct T1 selected is separate. Existing 0214 last case deliberately shows **joint full restore vulnerability**; 10/10 later must not be security acceptance.
- G9 seven, G2 original 50, canonical PG RLS, W8 full build/browser and IV: NOT_RUN/HOLD.

## Maintenance / rollback / handover
Use the ZIP's `python -I -B run_integrated_79.py`, or revert governance commit; source/permission/product refs unchanged. Do not migrate fresh SQLite lab DDL to production, use an old writer against IAM store, treat a fixture observation as issuer proof, or reset consumed claims. Formal ORG/Core/T1/D4/Unified owner review remains required. D5-G weighted 42.5% → 42.5%; Core 12/16 and MVP 0/11 unchanged. No CI enablement outside H01's separately documented narrow MI10 scope.
