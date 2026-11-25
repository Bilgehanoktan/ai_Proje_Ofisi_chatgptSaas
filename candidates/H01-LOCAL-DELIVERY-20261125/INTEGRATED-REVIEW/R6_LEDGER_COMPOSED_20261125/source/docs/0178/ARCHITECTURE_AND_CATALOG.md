# DOC-REV-0178 — EDS fix and exact offline preflight
## Changes / why / where / how
0177 Dashboard read sections from company.catalog fixture; changes to uiCatalog authority/preferences rows were not consumed. New design-system/catalogPresentation.ts exposes CatalogRow, CatalogSections and presentCatalogRows. Only three allowlisted existing title/view pairs are eligible; overlay must exactly match pinned display metadata, otherwise UNKNOWN · HOLD. Source/fixture never mutated; all unrelated rows unchanged. Dashboard calls helper for section display. CorePreview distinguishes no selected task (dependency —) from selected task with no dependencies (Yok). New candidate c66ef8a4a9966bbebe53d1e8c03886635a4e8e1a: 47 files, 1 new, 2 modified versus 0177; 44 unchanged. Original product tree and previous candidate preserved. No dependency, API, event, DB or contract changes.
## Verification
0177 static readback/import path scan 25 TS/TSX files, 41 relative literal edges, 0 unresolved. This is not a compiler check. The new pure helper was compiled standalone with TS 5.8.3 and tested under Node 22.16.0: 8/8. Python 3.13.5 standalone extracted-directory preflight fixture tests: 12/12. Tested files' local Git hashes matched uploaded blobs. Product/browser/build NOT_RUN; actual archive unavailable in sandbox, Git DNS unavailable, npm cache empty, no lock. This is not independent PRE or normative acceptance.
## Exact local preflight
Download the pinned 0178 GitHub commit archive via GitHub, extract in isolated folder; before install from root:
```powershell
py -3 scripts/verify_eds_candidate.py --root quarantine/0178/frontend --manifest quarantine/0178/FRONTEND_TREE_MANIFEST.json
```
Expected 47/47 only on exact clean extracted candidate, symlink/extra/missing/hash mismatch HOLD. Git SHA-1 blob identity is source integrity only, not signature. Script assumes a trusted local immutable directory and manifest pinned to reviewed commit; not a hostile concurrent filesystem or archive extractor.
Standalone reproduction (PowerShell, existing TypeScript/Node only; not product build):
```powershell
tsc --target ES2020 --lib ESNext --strict --module commonjs --outDir .tmp-0178 quarantine/0178/frontend/design-system/catalogPresentation.ts
$env:EDS_HELPER_JS = (Resolve-Path .tmp-0178/catalogPresentation.js).Path
node --test tests/catalog_presentation.test.cjs
py -3 -m unittest discover -s tests -p test_verify_eds_candidate.py -v
```
## PRE scope / blockers
Exact parent 889a54d1d588778791b0be3dea8a5e66c40d1285; candidate tree c66ef8a4a9966bbebe53d1e8c03886635a4e8e1a; 0177 original product base preserved; 3 incremental files and cumulative 0177 changes need genuine independent reviewer, SoD/custody, scope digest, PRE receipt, valid T01/T06 and POST review per 0162-E. No receipt or self-approval. User CEO-0174 authority recorded; does not replace independent gates. Next after applicable gates: clean archive verification, reviewed transitive locks, isolated DEV/TEST build and browser, backend smoke; 14 EDS product checks NOT_RUN. Separate R12 branch not merged.
## Maintenance / rollback
Wrong status: compare exact fixture title, uiCatalog row, helper expected row; never alter canonical fixture for UI label. Unknown selection: inspect readPlanProjection guard and selected task. Preflight: compare exact commit and clean directory; do not ignore extra or hash mismatch. Revert only 0178 revision or retain 0177 candidate; no migration. Preserve 24-area score rubric and evidence history.
