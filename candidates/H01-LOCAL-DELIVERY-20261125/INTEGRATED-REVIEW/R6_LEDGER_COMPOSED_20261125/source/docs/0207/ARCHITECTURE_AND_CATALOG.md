# DOC-REV-0207 — D0 cross-boundary evidence

Baseline `614aa63efbd0a95d0fa5fe47390df043d773370f`; source `d06e65dba202d79740b05980eea739596ad134c3`. 336 product files, 335 manifest entries; 334 existing non-manifest product files unchanged. One test added; two repository test infrastructure files added; manifest updated. No runtime module, API, event, database migration or dependency version change.

## Actual tests
72/72 selected local cases (65 regression, 7 new), zero failed/skipped, Python 3.13.5, SQLite 3.46.1. 28 exact baseline files checked against Git blobs and SHA-256, one new test checked against remote blob. 24 snapshot guard, 17 memory access, 15 snapshot store, 9 model invocation, 7 cross-boundary. Real disposable SQLite fixtures; model invocation is structural and denied, not provider execution. [Evidence](../../tests/evidence/TEST_EVIDENCE_0207.json).

## P0 finding 0207-D-01
A new memory revocation/tombstone changes memory decision to STALE_HOLD and old snapshot to CAS_HOLD, but model envelope still structurally matches because it does not bind the memory pin. Both remain DENY/HOLD; no live call, data release or spend.

Design a combined immutable admission/input provenance binding including memory snapshot/revocation, ACL, run/version/attempt, lease/fence, witness/policy epoch, provider registry and input digest. Recheck at authority/effect boundary; test revocation race and rollback. No self-grant or normative change.

## A/B verification preparation
55-file static candidate lock for 12 core + 17 lifecycle/handler tests from the exact 0206 union. Six SQL blobs are size/blob pinned, 49 product files additionally SHA-256 pinned. New wrapper uses an unchanged historical runner after verifying its blob; direct dependency pins checked, transitive lock and runtime closure are not proven. Runner and 29 cases NOT_RUN. Full checkout remains blocked by DNS. No dependency installation.

## Diagnosis / maintenance / rollback
Use `python scripts/verify_product.py --root . --manifest-blob 573166141f186245b94b818b9c0b1cdaf85d37e9` on exact checkout. From repository root use `python tests/integration/run_core_0207.py --source . --report core_0207_preflight.json --check-only` then run without check-only in an isolated reviewed environment, with a new report path. Source or dependency mismatch is HOLD; no bypass for acceptance. Preserve historic runner pins. No migration to roll back; return to 0206 commit, retain this branch and test artifacts. Full T1/PG, R03, independent custody, browser/build and normative decisions open. No live dispatch, external providers, spend, CI, main or PROD.

[Catalog](../../catalog/revisions/TECHNICAL_CATALOG_0207.json) · [Next](../../handover/NEXT_STEP_0207.md)
