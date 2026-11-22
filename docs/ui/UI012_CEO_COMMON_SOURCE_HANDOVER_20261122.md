# AI Company OS — UI-01 + UI-02A controlled common source review (2026-11-22)

**Task:** `MI05-UI012-COMBINED-PREWINDOWS-20261122` | **State:** ISOLATED_SOURCE_REVIEW / OWNER_HOLD
**Purpose:** Reuse the existing product code from two isolated MI-05-owned UI tracks **without merging any protected branch or authorizing production**, and prepare exact source to be picked up during later Windows full build.

## Exact ancestry and three-way reconciliation
- Canonical source base `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` with **552** manifest entries; source owner review requirements unchanged.
- UI-01B theme/navigation/PlanGraph + exact existing npm lock parent source: `integration/mi05-ui01d-pinned-lock-stage-20261122@1a75ea2cd287f8fbeab01f4ce5fd89c4197ba2c9`, inherited manifest Git blob `aa36b436f3c41cb896cbb63dd385952989836105` (**555** entries, 556 product blobs incl manifest), PR40 DRAFT.
- Independent UI-02A existing CEO `OperationalReadback` provenance and event total fix: `integration/mi05-ui02a-ceo-provenance-isolated-20261122@659fa93ca60364395095a0efe74ab3ed37051303`, manifest Git blob `a0fef0821e19fed773405a9cef111895b1bbeac2` (**553** entries), PR42 DRAFT.
- GitHub source path intersection is **only** `product/SOURCE_MANIFEST.json`. Exactly **2** existing CEO files are replaced by their verified original UI02A blobs, and exactly **1** new CEO regression test file is appended. UI01 source, npm lock, tests and owner records unchanged. Candidate union manifest = **555 -> 556** entries, expected 557 product blobs incl manifest. A new shared manifest is created from the PR40 parent; no copying of the stale separate UI02A manifest over it.
- Parent history and UI02A branch remain separate for review/rollback. Shared owner catalog and this revision-specific handover are copied into the new child; previous source owner changes are not overwritten.
- Note old open PR #2 and #3 touch `Dashboard.tsx` and `MetricsStrip.tsx`; they are **not** modified here. Other current PRs must be rechecked before any promotion.

## Behavior in exact existing product
- UI01 retained: ThemeFrame light/dark cosmetic browser preference, Navigation focus and screen reader section status, PlanGraph 75/100/125/150 zoom.
- UI02A adds only safe historical provenance and *derived* observed/expected event ratio in the **already mounted** existing CEO OperationalReadback. Uses existing `useProjectionRead('task-budget')`, no new backend, fetch endpoint, subscriptions, stores or authority. Historical sample stays historical; live agent/run/cost/grant never inferred.
- Native code touched in child commit only: `OperationalReadback.tsx` blob `5a83e9861c8edfeca99f253a09ca4d7cb1fa15b2`, `OperationalReadback.module.css` blob `f909da8b520cf1a3cdb95a972c495e140294ffc9`; new `ui02-ceo-provenance.test.cjs` blob `11e7a75cfd3ddbb7ba26a7a706585730ab3249b1`.
- Unchanged original CEO test `ui-p10j17-ceo.test.cjs` blob `27167d887f7cd228f8ea6f83887b444f74b2b1e1` preserved.

## Actual local synthetic integration test on exact file copies
- Node v22.16.0; available global TypeScript v5.8.3, not the pinned full product TS v5.9.3. Mock-React JSX/transpile, **not** full React/Next or Chromium.
- Four targeted test suites, executed **together** on exact UI01B ZIP original six file copies plus UI02A exact blobs and unchanged CEO original test: **40/40 PASS**. TAP SHA-256 `c828ae6ee33298bc45817d52dfa9935eedc0c187b32c6530690ab623916cf809`.
- Original `navigationModel.ts` blob `d41206b847daafa15e3a50023792ac10680814ad` with original `navigation-model.test.cjs` blob `67395deef9e553beace053ab6019f1a4c5a519e4`, isolated TS compile and original model test: **8/8 PASS**. TAP SHA-256 `f6bec71af693f075e268f69cd93af2f1f2ec067773b8baec1bb48acc9255f987`.
- Original `sectionModel.ts` blob `7a0c8b6c7dc8a1c0f99616cb2b13fec3d35163c2` and original `ui-p10j11-sections.test.cjs` blob `d774e8fb2fe0957f339b36f4635ccee67d96c512`, isolated TS compile + original test: **4/4 PASS**. TAP SHA-256 `afbe97bb099c2ba3b1d34fa073998df33788a4bbbd21769fed673a7fe27612ca`.
- **52/52 selected tests** on a *new combined source candidate*, not retroactive release evidence for earlier source branches. Initial UI02A development test 2 FAIL with temporary `dd` markup was fixed to `ul` without modifying original tests and re-run; final combined 52/52 PASS.
- `npm ci`, exact pinned TypeScript full typecheck, Next.js build, real Chromium screen/keyboard/snapshot tests, official W8 C07/C08, independent C05/IV: **BLOCKED/NOT_RUN/HOLD**; source owner and license approval still pending. No CI or PROD claim.

## Next gates, owner, rollback
- MI-05 owner and MI-01 lock/license owner review the exact two-source union and manifest. Recheck active PRs against source file paths + npm lock, then decide authorized full-source checkout.
- Continue separate pending UI02B/C/D/... existing code work only on paths approved by their owner; no parallel writes to PR2/3 Dashboard/MetricsStrip.
- Later Windows: exact checkout, 556 SHA256 entries + tree verification, approved immutable lock, npm ci, full tsc/Next build, actual Chromium desktop/mobile and screenshot evidence. Official W8 C07→C08 and independent C05 remain separate.
- Promotion to `integration/product-dev` only after owner/test/manifest gates; no main/CI/prod/secret/customer data.
- Rollback: close draft candidate PR or normally revert one isolated commit; PR40/PR42/canonical history untouched. No database migrations/API/event code changed.
- Acceptance UI **21/40 → 21/40**, W8 **3/8 → 3/8**, weighted development **HESAPLANAMADI**.
