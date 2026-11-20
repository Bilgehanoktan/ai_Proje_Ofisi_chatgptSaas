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

## User-executable scoped Windows replay helper (artifact, not test result)
- A SHA256-pinned helper was prepared in ChatGPT as `AIOS_W8_P10J16_NAV_SCOPED_TEST_20261121.ps1`, SHA256 `2d2b4cdab636c7275441cab48f09271477c0709d3fd8c993106beb8e9e82009d` (not published to this repository).
- It verifies immutable PR35-stage original P10J16 test SHA256 `8bb0a81933001c64558df9e630af93390b1549714370750e8cb43bea2cef2bee` and `OfficePanel.tsx` SHA256 `7d75044a6b8083467b9acf77d996e3adf35c2debdde74d5a88c3157bc4c30dcc`.
- It creates **new** `E:\\AIOS\\W8\\P10J16_NAV_SCOPED_<timestamp>` and copies only the isolated test and panel; performs the three exact string changes used in this candidate; checks candidate SHA256 + Git blob; executes `node --test` using existing stage's TypeScript dependency through local process-only NODE_PATH; restores NODE_PATH and verifies originals unchanged.
- Its **actual Windows execution is NOT_RUN** until the user supplies its log. It is **not** a replacement for new PR36 original G3/C04/C06/C07/C08 evidence and must not be conflated with PR35 C04/C06 PASS.

## 2026-11-21 — Linux exact pinned P10J16 Node replay (additional evidence)
- **Execution policy event:** User Windows PowerShell 5.1 rejected unsigned `AIOS_W8_P10J16_NAV_SCOPED_TEST_20261121.ps1` with `PSSecurityException UnauthorizedAccess` / `File is not digitally signed` after its SHA256 preflight. **That Windows script did NOT execute**, no local candidate was created by it, and policy was not changed.
- **Independent genuine execution:** assistant isolated Linux container using Node.js `v22.16.0`, TypeScript `5.8.3` (different from Windows Node v24.14.0); test file and OfficePanel reconstructed from actual GitHub PR36 sources. SHA256 of test file exactly `c9b66a7d45fb298647ad1d74179f61dcc37733beb41bea08894e1f4036fc1431`, of unchanged OfficePanel `7d75044a6b8083467b9acf77d996e3adf35c2debdde74d5a88c3157bc4c30dcc`. Git blob hashes checked independently `f55f72ffc1ec9c5de81b4be0fd13d2a5f01d5fe5` and `eacb81100fb34a8e74f619a5a8e2283a97337253` respectively.
- **Native targeted Node test result:** `node --test product/ai-company-os-frontend/tests/ui-p10j16-office-composition.test.cjs` **8/8 PASS**, 0 FAIL, 0 SKIP. TAP log SHA256 `fc4a5bc387c7734e31755ea032a6b02a223090045c842a74f3da1df4eb392c46` (1513 bytes) stored as conversation artifact `AIOS_PR36_LINUX_P10J16_8of8_20261121.log`; this is genuine tool execution, **not user Windows**.
- **Evidence classification:** `PASS_ACTUAL_LINUX_ISOLATED_TARGET_ONLY`; user Windows PR36 scoped script `NOT_RUN_EXECUTION_POLICY_BLOCKED`; PR35 full Windows C07 `ATTEMPTED_FAIL`; PR36 full W8 C07/C08 `NOT_RUN`; independent C05 `HOLD`; canonical W8 acceptance `3/8`. This Linux replay does not claim React/Next/browser or Windows full-original W8 success.
- **Next:** inspect `Get-ExecutionPolicy -List` and `Get-AuthenticodeSignature` read-only on Windows; do not change `MachinePolicy`, `UserPolicy`, `CurrentUser` or `Process`, do not unblock or bypass unsigned scripts. Prepare an authorized code-signed or otherwise policy-permitted verification path for PR36 fresh Windows W8 C07/build/C08. Maintain original W8 evidence stages immutable.


## 2026-11-21 — Actual user Windows PR36 targeted Node P10J16 8/8 PASS
- **Evidence origin:** user-pasted native **Windows PowerShell 5.1** console (not assistant Linux replay). The commands were directly pasted into the interactive shell; no unsigned PowerShell `.ps1` was invoked, and execution policy was not changed.
- **Stage kept immutable:** `E:\AIOS\W8\W8_AGENTFIX_LOCAL_20261121_002919\stage`. Before creating candidate, direct Windows `Get-FileHash -Algorithm SHA256` verified old `tests/ui-p10j16-office-composition.test.cjs` `8bb0a81933001c64558df9e630af93390b1549714370750e8cb43bea2cef2bee` and old `OfficePanel.tsx` `7d75044a6b8083467b9acf77d996e3adf35c2debdde74d5a88c3157bc4c30dcc`.
- **Targeted candidate folder:** `E:\AIOS\W8\P10J16_VERIFY_20261121_005100`. Three exact, unique P10J16 test fixture string replacements generated test SHA256 `c9b66a7d45fb298647ad1d74179f61dcc37733beb41bea08894e1f4036fc1431` and Git blob `f55f72ffc1ec9c5de81b4be0fd13d2a5f01d5fe5`, both verified before execution. Copied `OfficePanel.tsx` SHA256 verified unchanged. TypeScript dependency was reused read-only from the prior stage via process-scoped `NODE_PATH`.
- **Real Windows Node result:** `node.exe --test <candidate>/product/ai-company-os-frontend/tests/ui-p10j16-office-composition.test.cjs` **8 tests, 8 PASS, 0 FAIL, 0 SKIP, 0 CANCELLED, 0 TODO**, `duration_ms 241.079`. Both formerly failing navigation cases now PASS.
- **Failure guards and preservation:** printed `PR36_SOURCE_HASHES_PASS`, `NODE_EXIT_CODE: 0`, `ORIGINAL_STAGE_HASHES_PRESERVED`. Native test log path `E:\AIOS\W8\P10J16_VERIFY_20261121_005100\P10J16_TEST.log`; file bytes/hash **not yet supplied independently**, whereas console output contains full TAP summary. This is an actual Windows test on **isolated two-file candidate**, not a full PR36 552-entry source checkout.
- **Previous vs current:** scoped PR36 Windows P10J16 `NOT_RUN -> 8/8 PASS_ACTUAL_WINDOWS_ISOLATED_TARGET`. PR35 original Windows C04 and C06 remain PASS for the previous pinned source; PR35 C07 full chain failed at P10J16; **PR36 full C07 remains NOT_RUN**, **C08 NOT_RUN**, independent C05 **HOLD**, canonical W8 product acceptance **3/8 -> 3/8 (delta 0)**, weighted development `HESAPLANAMADI`.
- **Next:** Assemble a **new**, manifest-Git-blob-bound PR36 original W8 stage and rerun C07 all groups + full Next build, then C08 genuine browser tests. Do not mark acceptance from the isolated P10J16 replay. Preserve previous PR35 `.log`/`.json`, no `integration/product-dev` merge, no CI, no changed security grants.
