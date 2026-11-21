# MI-01 / W8 — Core0207-C50-R1 successor contract and handover

Date: 2026-11-21. Status: REVIEW-ONLY candidate, NOT historical C07 PASS, NOT independent security C05.

## Baseline, ownership, scope
- Canonical integration/product-dev: 254e0188998d0d245bd8ee4eb901aead02951a66, 553 product files, 552 manifest records. Unchanged.
- Parent PR #36: review/mi01-w8-p10j16-unified-office-links-20261121 at 683a26171ac54544260456ce84e19c38614aa5e2. Existing MI-01/W8 owner retains the original W8 suite.
- PR #34 already owns cryptography 50.0.2 production dependency upgrades. No duplicate update.
- New candidate branch is pinned to exactly PR36 head; only unique new non-product paths. No modification of W8 adapter, historical lock/runner, product, database, APIs, npm/Python locks, CI, permission or source manifest.
- Decisions and authorities unchanged: local D0 review only, no automatic merge, production grant, provider, CI escalation or security approval.

## Authentic Windows evidence, 2026-11-21
- PR36 552-source G3 audit PASS; C04 lock review PASS; C06 28-wheel/30-npm offline install PASS. Stage: E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\stage.
- Original Core0207 historical runtime pin requires cryptography 46.0.4. Current PR36 stage has cryptography 50.0.2; historical runner returned DIRECT_DEPENDENCY_PIN_MISMATCH. Original C07 therefore HOLD.
- Original P24 exists at PR36 source/tests/integration and matches Git blob 0728ba08494bb8d67c7cec42fe27dd8606bdc7f3. Previous diagnostic precheck path in stage was wrong.
- Patched helper R2 SHA256 3ef7db69f9a134b8b23683a71690273b494fea7088051b1532170921c8fc2663 corrected exactly two paths. Actual R2 Windows Core29 diagnostic: 29/29 PASS under 50.0.2 with diagnostic-unpinned; isolated Next.js build and TypeScript noEmit both exit 0. Original stage integrity preserved True.
- Evidence directory: E:\AIOS\W8\PR36_DIAGNOSTIC_ONLY_20261121_134455. Full JSON and log not uploaded/read back here; do not infer case IDs beyond source-defined test modules. All three R2 results are diagnostic, not C07.
- C07 HOLD; C08 NOT_RUN; C05 independent HOLD. W8 acceptance 3/8 (37.5%) before and after, delta 0 points. Weighted development HESAPLANAMADI.

## New exact contract proposal
1. tests/integration/core0207_crypto50_r1/CONTRACT.json — Git blob 537e0c35592ca7366a52ab87c08db7e419f18b71.
2. tests/integration/core0207_crypto50_r1/run_core0207_c50_r1.py — Git blob cc467843bf11857fbbd9df19e513626fb7de85bf.

The new runner NEVER passes diagnostic-unpinned. It loads the immutable historical 55-file source lock, verifies original runner, helper and P24 Git blobs, validates C06 stage lock review digest and INSTALL_OK, exact approved PR36 product manifest blob, Python 3.13.17 under the original stage venv, exact current four direct dependency versions, materializes the same 55 original file bytes into a temporary isolated directory, and calls the ORIGINAL hashed P05 helper with the same four test modules and counts. It checks 29 PASS without skips, rechecks 55 files and original stage guards, and writes its report outside the stage. It never writes C07 acceptance markers.

Unchanged originals:
- Historical 55-file lock Git blob 223f6fbd28cf4c428c07eb60dda4a36f644fa58c.
- Historical Core29 runner Git blob b019a5e60cfff4183b00e99f252ffe00bc164eda.
- Historical P05 helper Git blob befb9f429791a01b2fe37009e40f994a5924b2ff.
- Historical P24 helper Git blob 0728ba08494bb8d67c7cec42fe27dd8606bdc7f3.
- Historical source commit 614aa63efbd0a95d0fa5fe47390df043d773370f.
- Modules: test_retained_snapshot_0201 5, test_terminal_anchor_lifecycle_0203 7, test_lifecycle_projection_p02 8, test_lifecycle_prefix_p03 9 = 29.
- Historical dependencies: fastapi 0.163.0, starlette 1.10.0, cryptography 46.0.4, uvicorn 0.34.2.
- New direct dependency contract changes ONLY cryptography to 50.0.2; all historical source and test bytes unchanged.
- PR36 product manifest blob 9660da1104617b4764d5f1e32009e4e3405b47f8.
- PR36 C04/C06 REVIEW SHA256 341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3.


## Current validation levels
- Actual GitHub new-file readback: exact blobs recorded above.
- Source/design guard checks: 12/12 static string/contract checks PASS. This is NOT Python compile and NOT runtime test.
- Versioned successor runner Python execution: NOT_RUN.
- Original complete W8 C07: HOLD, C08: NOT_RUN, independent C05: HOLD.
- This contract is a review candidate only; even if its new isolated 29 tests PASS, original C07 remains blocked until an owner-approved versioned W8 adapter and complete fresh W8 run.

## Required next owner work
1. MI-01 owner reviews exact source 55 entries, all 29 case IDs, unchanged historical source/runner blobs and present C06 stage review hash.
2. Dependency/security owner validates transitive graph, wheel SHA, cryptography loaded binary/OpenSSL provenance and license requirements. No old crypto downgrade; independent C05 acceptance stays separate HOLD.
3. Owner-approved local run of new candidate using original PR36 stage venv, runner-root E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\source\tests\integration, and the existing R2 historical_source_55 directory; report in new separate E directory, compare case IDs to prior diagnostic. No original stage edits.
4. After review, create NEW reviewed W8 adapter version that invokes the versioned suite while preserving the original historical lock and fail-closed tests, regenerate exact source manifest and runner pins, re-run full original product C07 plus Next build under a fresh stage. Then independently run actual C08 Chromium browser same-document/screenshots checks. No acceptance until proper owner/IV signoff.
5. Independent C05 risk review remains HOLD. Neither source test result nor W8 acceptance percentage is changed by this candidate.

## Catalog / support / rollback
- New runner symbols: git_blob, require, exact_file, import_pinned, validate, main.
- Contract is JSON-only; no new product class/function/API/DB/table/event/production dependency.
- Diagnoses: missing/symlink original => MISSING_OR_SYMLINK_FILE; source hash => GIT_BLOB_MISMATCH; wrong graph => SHA256_MISMATCH/C06_MARKER_HOLD; wrong Python => NOT_PR36_APPROVED_VENV_PYTHON; wrong direct pins => VERSIONED_C50_DIRECT_PINS_MISMATCH; case regression => VERSIONED_C50_CASES_NOT_29_OF_29. Never bypass a HOLD.
- Rollback: close draft PR or normal revert only new branch files. Preserve PR34/PR35/PR36, both original Windows stages, historical 46.0.4 lock, C04/C06 evidence, governance decisions and acceptance counters. No force push, auto merge or PROD.
