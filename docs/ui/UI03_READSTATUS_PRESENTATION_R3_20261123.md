# MI05-UI-READSTATUS-PRESENTATION-R3-20261123 — source, tests and handover
Date: 2026-11-23. Owner scope MI-05 UI; dependent MI-06 ORG, MI-01 W8, central manifest owner.

## Source identity
- Canonical development branch: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` (untouched).
- Exact isolated parent: PR #48 `59400debd73bf3b5e2df1e0d2fe008fd4e633917`, which descends from PR #45 `17911f73003e6ac303579d40d4a9aac8a3e2fe98`.
- 37 open PR paths reviewed; `SharedSnapshotPanel.tsx` changed only by PR #45, an ancestor of this child. No concurrent code writer in those 37 PR diffs. GitHub source ownership review is still REQUIRED for promotion.
- Original target Git blob `4a35c712a92a609e8ed07e5ea28d24a15eb67576`, exact local pre-change match. New blob `687443fdf73ef53bd39017b6581b7ce05e0f497a`.
- PR #48 `projectionRead.ts` original blob `b9046f4f4f92ea121ecb530c7fa781af96d8d79d` and `useProjectionRead.ts` blob `4294f67533cd1ff0d92a117935393bbee84d2abe` NOT MODIFIED.

## Smallest UI change
Only existing rendered `product/ai-company-os-frontend/features/data/SharedSnapshotPanel.tsx` was updated. It imports existing `readStatus`/`ReadState` and passes full `planRead.state` and `organization.state` instead of `phase`. STALE → `Tarihsel görüntüleme süresi doldu · HOLD`, TIMEOUT → `Okuma zaman aşımı · HOLD`, READBACK_HOLD → existing general HOLD. Historical D0, sample-only, JOIN_HOLD, IV/Release HOLD, plan/ORG independence, static Office geometry and read/reset remain unchanged. No API/DB/event/authority, no credential, no grant, no live KPI, no execution or geometry join.

## Targeted actual local test
- New `product/ai-company-os-frontend/tests/ui03-readstatus-presentation-r3.test.cjs`: 8 targeted JSX presentation tests (mocked hooks with original PR48 readStatus helper), Node v22.16.0, global TypeScript v5.8.3 via `NODE_PATH=$(npm root -g)`. Original source/check exact reader Git blobs before test.
- Run: `NODE_PATH="$(npm root -g)" node product/ai-company-os-frontend/tests/ui03-readstatus-presentation-r3.test.cjs`
- Final result: **8/8 PASS**, failed 0, skipped 0; source and new test Git blobs confirmed exact to local tested bytes.
- Raw evidence: `tests/evidence/UI03_READSTATUS_PRESENTATION_R3_20261123.tap`, SHA-256 `febc2422f5c2ab87fd5c5b10946f815d31f111e7bfe28cf532b73335642a8fb8`.
- Earlier local diagnostic runs: Node --test positional argument and non-project TypeScript path produced harness errors; second attempt 7/8 due omitted mocked `data`; the final corrected harness was rerun 8/8. Those attempts are retained in conversation, NOT counted as independent regressions.
- Prior PR #48 **12/12 + 9/9** kept historical and NOT rerun.
- Full locked TypeScript 5.9.3, npm ci, Next.js build, real Chromium desktop/mobile, formal W8 C07/C08, independent C05: **NOT_RUN/HOLD**, not claimed by JSX mock tests.

## Separate proxy source owner handoff (no route edits)
- PR #22 Office `route.ts` and PR #26 shared `readBoundedD0Json.ts` use `content-type?.startsWith('application/json')`. This accepts invalid `application/jsonp`.
- Owner comments: PR #22 #7110573674, PR #26 #7110574369, combined PR #31 #7110575224. Strict media type + negative checks needed; preserve absolute 2500 ms deadline. No API or W2/W4 source changed.

## Source/manifest ownership, catalog and rollback
- New UI test and changed panel source are **isolated review files**. `product/SOURCE_MANIFEST.json` is a shared central single-writer file, deliberately NOT changed; its two required exact rebinds are in the versioned R3 delta proposal. This child is NOT manifest-complete or ready for canonical promotion, until central owner reconciles with PR #31/47/48 plus MI-01 W8.
- No new dependencies, scripts, endpoints or physical DB changes. No independent security/IV receipt.
- Canonical UI acceptance `21/40→21/40` (delta 0); W8 `3/8→3/8`, MVP `0/11`, IV `0/7`. Weighted development **HESAPLANAMADI** (no approved frozen criterion denominator).
- Rollback: close draft child PR or ordinary isolated commit reverts. Parent PR #48, PR #45 and canonical source remain intact. Full exact repository ZIP unavailable in test environment; do not mistake this delta for full product archive.
- Next: MI-05/MI-06 source owner review → central manifest reconciliation → approved exact full checkout and C07/C08/IV gates.
