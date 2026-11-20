# AI Company OS — MI-01 W8 C07 P10J16 office route expectation repair (2026-11-21)

## Scope and authority
- **Parent PR:** #35 `review/mi01-w8-orgreadback-harness-20261120` at `39310fd452cf6cebcfd92ae02fe67c935c4c3978`; separate child **draft**, no merge or owner acceptance.
- **Current canonical product:** `integration/product-dev` at `254e0188998d0d245bd8ee4eb901aead02951a66`, with 553 product source files; this proposal **does not** change it.
- Preserve CEO-0174 / CEO-0179=B limits: no changed production authority, CI, independent security C05, grants, money, external providers or PROD.
- Change **only the legacy isolated JSX navigation test**, manifest and W8 manifest Git blob binding; no changes to `OfficePanel.tsx`, unified route, actual APIs, DB, npm/Python dependencies, runtime or UI policy.

## Authentic Windows result; do not merge evidence across stages
- User original PowerShell 5.1 text uploaded: `Yapıştırılan metin(20261120-213431).txt`; local byte SHA256 `3d838dd984a74995e1de6be401687d6391abccd17fb38e015be3e80d694b6f46` (52,880 bytes).
- Runner SHA256 `bf3699fcddca0d6adc8795ffb69752fe6e3c0f7eecc232809361b29e93c33c07` **PASS**, Python tempfile on `E:\AIOS\W8\TEMP_AGENTFIX`.
- Local isolated PR35 Git blobs 3/3; P10J18 targeted **15/15 PASS**; G3 audit **552 SHA256 pins +17 shared file pairs +29 auxiliary Git blob pins PASS**.
- C04 **PASS_ACTUAL_LOCAL_DEV_NEW_REVIEW**, lock review SHA256 `bac9b49d277f7bf8509d928f2b4ed06aab4cbfd82ea0f450349db9998d08f403`.
- C06 **PASS_ACTUAL_LOCAL_DEV**: 28 offline `--require-hashes` Python wheels installed; `npm ci --ignore-scripts` added 30 packages; `pip check` no broken requirements.
- C07 **ATTEMPTED_FAIL_UNTIL_PROVEN_PASS**: isolated `tests/ui-p10j16-office-composition.test.cjs` **6/8 PASS, 2 FAIL**; error is exact added `/office/premium/unified` route in both embedded and fullscreen views. Other passing suites do **not** make C07 PASS; next full build was not reached.
- C08 **NOT_RUN**. C05 independent **HOLD**. Canonical W8 acceptance **3/8 -> 3/8, delta 0**. Weighted development `HESAPLANAMADI` (no criterion denominator).

## Source-root cause
1. `product/ai-company-os-frontend/components/dashboard/OfficePanel.tsx` at Git blob `eacb81100fb34a8e74f619a5a8e2283a97337253` intentionally links to `/office`, `/office/premium`, and `/office/premium/unified` (fullscreen omits only the first).
2. `product/ai-company-os-frontend/app/office/premium/unified/page.tsx` exists at Git blob `fb6cf1fe045f216df1ad4a24cb72eb6d42f3219f` and renders a D0 controlled unified office candidate, not authority.
3. The isolated P10J16 test originated before that third link and still strictly asserted the former two-link/one-link lists; this mismatch is the verified cause of both failing assertions. Production UI alteration to satisfy a stale test would regress intended source.

## Changed files and catalog
| Path | Change | Hash / pin |
|---|---|---|
| `product/ai-company-os-frontend/tests/ui-p10j16-office-composition.test.cjs` | Exact links arrays now include the existing unified D0 route; test label updated to “all three routes” | 4029 bytes, SHA256 `c9b66a7d45fb298647ad1d74179f61dcc37733beb41bea08894e1f4036fc1431`, Git blob `f55f72ffc1ec9c5de81b4be0fd13d2a5f01d5fe5` |
| `product/SOURCE_MANIFEST.json` | Re-pin this **one** test entry, 552 entries unchanged | Git blob `9660da1104617b4764d5f1e32009e4e3405b47f8` |
| `tests/integration/w8_unified_u3.py` | Replace only `MANIFEST` with new manifest Git blob; all U2/browser/security/data pins retained | Git blob `1609d857b46ea973180c45271d87fcc92083f0a6` |

- Test category: isolated Node VM/TSX projection; does **not** prove browser/React/Next acceptance.
- Architecture: existing D0 read-only office link stays as implemented. No API/class/DB/event/dependency modifications, no new capability or security authority.
- Scope: one legacy test source alignment; no new prototype.
- Read-only GitHub source/manifest/adapter review: **11/11 PASS**, **not** a fresh Windows or Node execution.

## Required new evidence and rollback
- **DO NOT rerun the old pinned offline PR35 PowerShell runner as a substitute for this child candidate**: it reconstructs three exact PR35 blobs and may replay the same C07 failure.
- W8 owner should regenerate or adapt exact source transfer for this child commit and verify **all changed Git blobs**, `SOURCE_MANIFEST` SHA256 pins and new `w8_unified_u3.py` manifest pin before an original fresh **NEW** stage.
- First run targeted `node --test tests/ui-p10j16-office-composition.test.cjs` and assert **8/8 PASS** in an isolated clean checkout; then original full C07 plus required Next.js build, browser smoke C08, and check frontend dependency chain.
- Prior genuine C04/C06 PASS belongs to the **PR35** stage `E:\AIOS\W8\W8_AGENTFIX_LOCAL_20261121_002919`; **do not overwrite or delete**. New source requires a new G3/C04 review fingerprint and fresh C06+C07+C08 evidence.
- Native raw evidence on user's PC: `E:\AIOS\W8\W8_AGENTFIX_LOCAL_20261121_002919.{log,json}`; console paste is received, native files not yet read back.
- If child repair is incorrect, drop this child branch and keep parent PR35 unchanged. No force-push or main/product-dev mutation.

## Handover / next
Owner MI-01/W8. Target stage **P10J16 navigation isolated test -> fresh C07 full -> C08 smoke -> independent C05 HOLD until separate authorized review**. Do not promote acceptance without actual native evidence and owner review.
