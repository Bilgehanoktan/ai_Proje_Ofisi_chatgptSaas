# MI-05 / UI-03 — Projection reader visibility and stale-data closure
2026-11-22 · REVIEW/HOLD · No product/independent acceptance

**Task:** MI05-UI03-D0-PROJECTION-FRESHNESS-20261122
**Canonical:** integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66 (unchanged).
**Exact isolated parent:** PR #45 @17911f73003e6ac303579d40d4a9aac8a3e2fe98, manifest blob 8310f6ccd772eb324b0a6cb20c2d4530b77e2bee, 557 manifest entries. The child adds 1 test and updates 2 existing UI sources; expected 558 manifest entries, 559 product files inclusive of manifest.

## Why / changed behavior
The preexisting shared CEO+Office SSE historical reader expires its displayed data after 30 seconds and on visibility loss. The nine independent D0 GET projection readers previously retained a successful historical result indefinitely. In the existing `projectionRead.ts`, display results now expire to `STALE / HOLD / data:null` after at most 30 seconds, re-read cancels the previous expiry, timeout/invalid response clears data, and `invalidate()` denies late results. In existing `useProjectionRead.ts`, browser visibility loss invokes the same invalidation without any new request. `readStatus` gives a distinct stale message. This is **presentation retention, not authenticated source freshness**.

API calls and registered parsers remain identical: GET /api/demo/{mvp,admission,outbox,office-workbench,task-budget,lifecycle,lifecycle-prefix,plan,organization}; no backend API/DB/event change, new endpoint, worker, new framework, IAM grant, actual session, geometry join, SSE, live KPI or task result. Organisation route without owner binding remains 503 HOLD.

## Source/ownership and risk
All 35 open PRs were checked for code paths. None touched these two UI source files or the new test path. PR #29 sources are composed into PR #31; the separate UI ancestry is PR39 → PR40 → PR43 → PR45 and PR42 is carried into PR43. Shared `product/SOURCE_MANIFEST.json` is edited **only on this new isolated child** and must be reconciled by its integration owner with PR #31/W8 before any promotion. PR #45 itself and canonical product-dev remain unmodified. Parent source Git blobs were verified exactly before writing.

## Tests and evidence
- Node v22.16.0, TypeScript v5.8.3 local (global, not pinned 5.9.3); transpilation of selected exact reader and hook.
- Original unchanged `tests/projection-read.test.cjs` blob 226e0e9721677235184547b8d79e91b2e6c541fb: **12/12 PASS**, TAP SHA-256 d29b454ff6ee772366a7e39bd82f044f738d48847df2bec05ef48f12df6757a5.
- New `tests/ui03-projection-freshness.test.cjs`: **9/9 PASS**, TAP SHA-256 7b3259f7363acd6454e0734ab31b36ea95dcbbfd37976dc30657a749c8978e74.
- Scoped `tsc --noEmit --strict` for the reader with a local `organizationCap` type stub: PASS. It is **not** a full Next/React product typecheck. No npm install.
- Full pinned lock/typecheck/Next build, Chromium desktop/mobile, W8 C07/C08, independent C05, live tenant/IAM, real PG/IV: **NOT_RUN/HOLD**. Do not double-count 21 selected cases as unique product acceptance.

## Failure modes / rollback
Time expiry, hidden tab, stale callback, failed refresh and unmount suppress history rather than infer current agent/company. Potential tradeoff: historical example disappears after 30s, requiring a deliberate new read. Existing original source and prior history are retained. Rollback: abandon draft PR or normal revert of one child commit; no DB rollback. Cross-owner manifest reconciliation, MI-05 and MI-01 review, then full Windows acceptance are separate.

**Acceptance:** UI 21/40 → 21/40; W8 3/8 → 3/8; MVP 0/11; independent IV 0/7, all delta 0. Development percent HESAPLANAMADI (frozen denominators unavailable). No new CEO architecture decision required.
