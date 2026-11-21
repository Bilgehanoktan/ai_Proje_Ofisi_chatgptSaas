# UI-00 / UI-01 — EDS theme and navigation accessibility (2026-11-21)

Task: UI01-EDS-THEME-NAV-FOCUS-20261121; isolated source only. Base `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, product manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`. UI source owner MI-05 review required. This does not modify P10J24B, P10J25, PR22/26/29/31/34-38, W8 runners, ORG, IAM, Core, API, DB, runtime, event paths, CI or production.

Existing EDS theme and menu were inspected. Changes:
1. `design-system/ThemeFrame.tsx`: preserve dark SSR default, read optional local browser theme after mount, allow only literal `dark`/`light`, save only that cosmetic setting on user click; missing/denied localStorage is nonfatal. Does not store tenant or application data. This may visibly adjust theme after hydration; no pre-hydration script was introduced.
2. `design-system/Navigation.tsx`: selecting local menu sections focuses `#main-content` on desktop as on mobile, and a visually clipped polite status names the current section. The existing `/office` Next link remains a route. No new route or dispatch.
3. New exact reproducible `tests/ui01-shell-navigation.test.cjs`, run against the exact candidate code with Node v22.16.0 and globally installed TypeScript 5.8.3: 10/10 PASS, zero fail/skip via `NODE_PATH="$(npm root -g)" node --test product/ai-company-os-frontend/tests/ui01-shell-navigation.test.cjs`. Raw TAP (local evidence) SHA256 `e31e69eaa3f8a18cc2b0ffa2d2819f4163e8411af04ea936cd69da972731e6b8`. These are isolated transpilation/VM React mocked tests, **not** real React browser, locked TS 5.9.3, Next build, W8 C07 or C08.
4. Product manifest 552→553 entries. Exact source bytes/Git blobs/SHA256 in catalog revision.

Full checkout/npm locked deps/Next build, actual Chromium C08, owner review and independent C05: BLOCKED/HOLD/NOT_RUN. P10J24B is divergent: 491 manifest entries; no merge. P10J25 remains separate graph change. PR38 C07 and license/security prerequisites HOLD.

Development percentage HESAPLANAMADI (no owner-ratified denominators). Premium UI acceptance remains 21/40 and W8 3/8; deltas 0. No source-promotion or acceptance.

Maintenance / rollback: compare exact manifest pins before later integration; run tests/build on a vetted full checkout, validate keyboard behavior and possible initial light-theme flash in Chromium. Revert this one isolated commit or discard this branch to roll back; do not touch canonical product or independent owner branches. A source owner must explicitly review overlapping paths and approve a controlled fresh-manifest transfer.
