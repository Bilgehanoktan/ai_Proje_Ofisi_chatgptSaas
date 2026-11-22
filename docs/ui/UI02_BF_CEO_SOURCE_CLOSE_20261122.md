# AI Company OS — UI-02B–F CEO source integration / pre-Windows review
**Task:** MI05-UI02B-F-CEO-COMMAND-SOURCE-CLOSE-20261122
**Owner:** MI-05 / Premium UI; dependencies MI-01/W8 and MI-06/ORG
**Mode:** bounded CODE/REPO isolated DEV only; **SOURCE_READY_FOR_OWNER_REVIEW / RELEASE_HOLD**
**Parent:** integration/mi05-ui012-ceo-combined-review-20261122@5b6b5456a7a40e13bddc524f6476ab2d2339977e; manifest 556 entries, SHA 097d4bb1e9a4a5b1acad50ccdd176e7caf7ade76.
**Canonical product:** integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66 — untouched.

## Changes to existing mounted product components
- UI02B: existing `design-system/MetricCards.tsx` is already mounted through unchanged `components/dashboard/MetricsStrip.tsx`. Hide numeric `office.snapshot.json` fixture values from verified CEO KPI cells; present explicit STATIC_ONLY/HOLD until a separately authorized live source exists. `formatMetric` pure exported helper preserved for prior contracts.
- UI02C: existing `features/data/SharedSnapshotPanel.tsx` already rendered in CEO summary. Reuse shared provider's existing `planRead` for separately validated strict D0 reference plan; show task and wave **templates only**, not run, completion, date or actual progress.
- UI02D: in same panel reuse the already registered `useProjectionRead('organization')` and strict ORG-07C parser to present historical position count separately; no assignment/identity authority inferred. Existing AgentDirectory/OrganizationReadback remain unchanged.
- UI02E: reuse `readSecurityView` existing static guarded security source to show IV and release template HOLD/INCONCLUSIVE; no newly issued H01 decision/IV acceptance, no event/database write. Existing SecurityStudio and sidebar remain the detailed management views.
- UI02F: preserve exact existing SharedSnapshotProvider historical replay and Office-only presentation; on CEO only, show explicit JOIN_HOLD and link to the existing `/office` route. Plan, ORG and replay readings are independent and never silently joined; no new SSE engine/route.
- New targeted `tests/ui02-ceo-source-summary.test.cjs` checks positive/negative independent read, stale HOLD clearing, no false KPI, separate Office presentation, security fail-close, read/reset delegation.
- No edit to `Dashboard.tsx` or `MetricsStrip.tsx`, whose paths overlap legacy open PR #2/#3. Across all known open PRs checked, neither of the **two changed source paths** nor new test path overlaps. Shared manifest remains single-writer and needs owner reconciliation before product promotion.

## Exact candidate pins and tests
- MetricCards Git blob `20ba4e7a32d03dac612bb3ff293d64dfabcff4b0`, bytes 1024, SHA-256 `fefa8e7ad28bc935f7a7ab376761f1e521704b633db0964f623edbb3811b69e5`
- SharedSnapshotPanel blob `4a35c712a92a609e8ed07e5ea28d24a15eb67576`, bytes 5475, SHA-256 `7f8746fbb8f5fc26d8de369af229042fe53ebc485eae3d0c5d1717ef35d19b67`
- New test blob `c8a333c82c3706f3b8e4ee191034bdf30bec1187`, bytes 7235, SHA-256 `e8981dce5fbef9006194688c40f6f8959afb573b7b4cafc1e6860d9b2c6dd503`
- Local Node v22.16.0, global TS 5.8.3. Five targeted UI source suites **51/51 PASS**. TAP SHA256 `56df2a5e61d749e98795f88547c390151271fd3a75642e64a16e2a2da45396d4`.
- Exact original navigation-model + test **8/8 PASS**, TAP SHA `6c2190dad6ab2bf490a86dfc3b8772418c593a497ba022b2da931f2ffe90301e`.
- Exact original CEO section-model + test **4/4 PASS**, TAP SHA `fe248458ead5a1cda733754cf621aebe168bac40193383685a2967b203c3c733`.
- Combined selected local evidence **63/63 PASS**; JS VM/TS transpile mocks, not complete React, pinned TS5.9.3, Next production build or Chromium. First local new-test attempt **9/11 with 2 FAIL** because test regex did not permit JSX text whitespace; fixed only new test assertions and reran **11/11 PASS**, then 51/51, 8/8 and 4/4. Not an actual product runtime failure. Original tests not edited.
- Manifest union now expected 556 → 557, product tree 558 files including manifest. Inspect exact tree/path/size and return GitHub readback before claiming source closure. Missing full actual runtime and dependency licenses remain HOLD.

## Gate and dependency boundaries
- Owner MI-05/MI-01 lock/license and MI-06 ORG review: HOLD; prior PR39/40/43 all preserved, no automatic merge.
- Approved exact full checkout, npm ci, TypeScript 5.9.3 full typecheck, Next build, desktop/mobile Chromium, W8 official C07/C08, independent C05/IV: NOT_RUN or BLOCKED. No main/PROD/new CI/secret/actual customer data.
- Product acceptance UI **21/40 → 21/40**; W8 **3/8 → 3/8**; weighted development **HESAPLANAMADI**. UI-02 source work is not release acceptance and static source cannot provide real company metrics.
- Next: MI-05/MI-06 owner review, complete exact checkout on Windows and original frontend/browser tests; reconcile manifest with parallel MI branches. If accepted, controlled promotion to product-dev followed by integrated regression; otherwise HOLD.
- Rollback: normal revert of one isolated child commit or close draft PR; ancestor PR43/PR40/PR42, current canonical product, security authority and data remain unaffected.
