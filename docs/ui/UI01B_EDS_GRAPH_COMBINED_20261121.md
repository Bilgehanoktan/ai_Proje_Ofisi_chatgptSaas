# AI Company OS — UI-01-B source consolidation / review handover (2026-11-21)

Task: `MI05-UI01B-EDS-GRAPH-INTEGRATION-20261121`
Status: **ISOLATED_COMBINED_SOURCE / MI-05_OWNER_REVIEW_HOLD**. This is NOT release, not `integration/product-dev`, not main, and not IV/security acceptance.

## Pinned source / ownership
- Canonical base: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 product files / 552 manifest entries.
- Exact base SOURCE_MANIFEST Git blob: `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`.
- UI-01: `integration/ui01-eds-theme-nav-focus-20261121@2f07c12daf2f0b7745de203dd38a0c6f532a8960`.
- P10J25: `integration/p10j25-graph-zoom-isolated-20261121@69579e38ea06bee76154cc105b95bbe204544140`.
- Both UI branches were one commit ahead of the *same* pinned base; no source paths overlap between them, **only** `product/SOURCE_MANIFEST.json` overlaps.
- Previous P10J24B candidate diverges (not included); open PR #19, #22, #26, #29, #31, #34–38 changed no six target UI code/test paths at read time but several change shared manifest. Re-check latest HEAD/PRs before promotion. MI-05 is the UI source owner; this candidate's author is *not* an independent reviewer.
- All six source/test Git blobs have been fetched at origin refs and matched local source via `git hash-object` and SHA-256, **without modifying any original blob**.
- Two owner docs and two owner catalog revisions are retained byte-exact from their source branches.

## Changes
- `design-system/ThemeFrame.tsx`: cosmetic light/dark browser preference; initial SSR dark, hydration-flash not browser-verified.
- `design-system/Navigation.tsx`: desktop focus-to-main, polite section status; mobile behavior and /office link remain as source.
- `features/graph/PlanGraph.tsx` / `PlanGraph.module.css`: bounded zoom 75/100/125/150 and focus styles; graph data/auth unchanged.
- Two pre-existing test files copied byte-exact.
- Merged candidate manifest: **552 -> 554 entries** (two new test paths); expected 555 product files including manifest, verified by comparing branch diff to pinned base; no full product archive audit was run. Baseline manifest root metadata retained unchanged to preserve historical provenance; THIS handover defines the candidate status.

## Actual test evidence, exact local candidate copies
- Node `v22.16.0`, global TypeScript `5.8.3`; not approved pinned TypeScript `5.9.3`.
- `NODE_PATH=$(npm root -g) node --test product/ai-company-os-frontend/tests/ui01-shell-navigation.test.cjs product/ai-company-os-frontend/tests/ui-plan-graph-zoom.test.cjs`: **21/21 PASS** (10 UI-01 and 11 graph). TAP SHA256 `df3fb02890b89087d7075b2b339dc93c9067fe12b5f5f801867ebb187824ec94`.
- Existing owner `navigation-model.test.cjs`, canonical exact blob `67395deef9e553beace053ab6019f1a4c5a519e4`, after transpiling exact canonical `navigationModel.ts@d41206b847daafa15e3a50023792ac10680814ad`, run via `node tests/navigation-model.test.cjs .ui01b-compiled/navigationModel.js`: **8/8 PASS**. TAP SHA256 `d6cb40c1d6690d6eb218143aa7f65466d30a556060c33a88ea763e9d86befd4a`.
- Existing owner `ui-p10j11-sections.test.cjs`, canonical exact blob `d774e8fb2fe0957f339b36f4635ccee67d96c512`, transpiled `sectionModel.ts@7a0c8b6c7dc8a1c0f99616cb2b13fec3d35163c2`: **4/4 PASS**. TAP SHA256 `176288188c199c5cd92b7656cb22d27cc7a8f695672548967817f5e1d4fc84ad`.
- Total **33/33 local scoped cases**; source provenance and no duplicate release credit. An initial incorrect `node --test` positional invocation of navigation-model test failed because that original test requires `process.argv[2]`; corrected command passed without a code change. The unsuccessful invocation is NOT counted as a product failure or hidden as a passing test.
- Full Next.js production build, pinned dependency installation, complete TypeScript typecheck, real React/Chromium, visual screen shots, office/PG/IV and formal W8 C07/C08/C05: **NOT_RUN / BLOCKED / HOLD**. Exact full 553-product-source checkout and reviewed full npm dependency lock graph were not available. No unreviewed dependency install.
- Native browser risk: dark-to-light initial theme flash; status inside collapsed mobile nav may not announce; graphics alignment at zoom extremes not visually verified. Source owner/browser QA must inspect before acceptance.

## Acceptance, controls and rollback
- UI product acceptance previous 21/40, current 21/40, delta 0.
- W8 product acceptance previous 3/8, current 3/8, delta 0.
- Weighted development percent HESAPLANAMADI (missing frozen denominators).
- PR #38 DRAFT: owner security/license audit and official C07 are HOLD; C08 NOT_RUN and C05 independent HOLD. No W8 runner/locks/CI/API/DB/IAM/ORG/T1 changed here.
- Next: MI-05 owner reviews exact union patch plus shared manifest; obtain complete pinned checkout/lock, run existing W8/frontend/typecheck and Chromium scopes, re-check parallel PRs. Promotion to `integration/product-dev` only with signed/recorded scope and verified gates. No automatic merge.
- Rollback: normal revert of *this* isolated commit or abandon isolated branch; original UI-01 and P10J25 branches plus historical PRs are untouched. Never force push.
