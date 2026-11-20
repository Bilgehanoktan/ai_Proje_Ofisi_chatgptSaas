# MI-05 Office Workbench — original frontend regression readback (2026-11-20)

## Verified immutable source
Canonical source base: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, product count 553, 552 manifest entries. Checked original Git blob:
- `product/ai-company-os-frontend/tests/office-workbench.test.cjs` — `bbad34677abeb0f2fada6b68ad4805b09ee077c7` (**byte-exact existing GitHub test source**, unchanged).
- `features/mvp/officeWorkbenchProjection.ts` — `d8d0cf4ce765651bd5490df1482a92ff0c668943` (unchanged).
- `features/mvp/localBackend.ts` — `9231711d7efb18dd18b68e3322f62337a6477484` (unchanged).
- Patched review-only `app/api/demo/office-workbench/route.ts` — `dc18ef2ecaf5556e09bc6152578f8cadf247ef29`.
- New targeted test `tests/office-workbench-deadline.test.cjs` — `8ae7b251f8ac86e3f03897442d3819d76256cbe9`.

## Reconstructed test data and limitation
The original 25-case Node source reads 20 JSON cases from `product/ai-company-os-backend/tests/office_workbench_cases.json` (GitHub blob `29aa823d16c2b7975c322b41b99f9db4ec2b2c4e`). The 20 case names, valid/invalid classifications and all object values were read from the original GitHub file. To avoid claiming a byte-exact download with no network, the **same JSON object semantics** were rebuilt locally from the six source prefix counts and fourteen source negative-case deltas. Reconstructed test data **is not claimed byte-identical** to GitHub's original JSON. The actual original test JavaScript was byte-exact verified with `git hash-object`.

The twenty cases cover prefixes 0–5, wrong tenant/plan/layout/world, mismatched count, over-limit count, dispatch privilege, actual-run spoof, freshness spoof, geometry spoof, IV and release privilege spoof, role-count change and excess field. Five existing route GET/HOLD/port tests run unchanged.

## Actual local execution
- Environment: Linux x86_64, Node `v22.16.0`; selected TS strict compile prior PASS under system `tsc 5.8.3`, project pin 5.9.3 uninstalled.
- Original unchanged frontend test source with semantically reconstructed fixtures: **25/25 PASS**; 0 fail/skip/cancel.
- New deadline-specific test source: **6/6 PASS**; 0 fail/skip/cancel.
- Both suites run against the **same patched compiled review route**. **31 selected executions**, no new/old overlap in method names.
- Local joined TAP file SHA-256: `25443dbf5f6437c5056d6e1c0cf5f78b043df01882f6ee02aba8050d228f6e63`.
- Local reconstructed JSON vector file SHA-256: `9727cfe43bf7ac203c276b5bd4e5b1496500c39b8343576c4138df1ae1c7d81f`.
- Original full backend Python suite, native browser, installed project TS 5.9.3, full W8 prepare/install/test/smoke, real Office Runtime, real PostgreSQL and independent IV **NOT_RUN**. No claim of canonical product acceptance.

Local command:
```sh
node tests/office-workbench.test.cjs /absolute/build/features/mvp/officeWorkbenchProjection.js /absolute/build/app/api/demo/office-workbench/route.js /absolute/tests/office_workbench_cases_semantic.json
node tests/office-workbench-deadline.test.cjs /absolute/build/app/api/demo/office-workbench/route.js
```

## Architecture/catalog/handover and ownership
No additional production source, symbols, API routes, schema, DB, CI, dependency, security permissions or migration changed in this readback. Earlier PR #22 D0 route change remains one-line post-parse aborted-signal denial; PR #20 full W8 and PR #19 G2/G9 remain separate active owners. Only MI-05/Unified owner review can promote this patch; the 553-product canonical source remains unmodified.
- UI **21/40→21/40**, Core **12/16→12/16**, MVP **0/11→0/11**, IV **0/7→0/7**, 0 percentage-point acceptance gain. Global weighted development **HESAPLANAMADI** (owner-ratified group denominator 0/10).
- Rollback: close PR #22 or normal revert of its scoped patch/test; no force push or main changes.
