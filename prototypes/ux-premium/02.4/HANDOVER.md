# UX-PREMIUM-02.4 — Camera & Navigation Lab
Date: 2026-11-16. STANDALONE_DESIGN_PROTOTYPE / NOT_PRODUCT_INTEGRATED.

## Baseline / ownership
Parent 02.3 Git commit `22b69660ef9bccee0ef95599abb468952862d62c`, office.html blob `bbd05e0c52b7a8af1abf6a6849730aa75d1ecfb5`, SHA-256 `090152d2fa815e6ee49ca2725d1491cfe21ea77d8c0e49d7f875498b7d1a6da0`. Parent ZIP CRC and 14/14 package manifest entries verified. Work only in `prototypes/ux-premium/02.4/` on `integration/ux-premium-02-office-motion`. No shared product/API/DB/architecture/tracker/other branch mutation; no merge. No actual agent, task, authorization, external effects or canonical OfficeV0 binding. H01 remains sole human CEO.

## Architecture and technical catalog delta
| File / symbol | What, why, how |
|---|---|
| camera.js / cameraWorld, cameraClamp, cameraBox, cameraLimit | 1100×720 decorative world; responsive aspect-fit viewBox; 1–2.4 zoom; constrain each axis or center if viewport exceeds world. |
| cameraPoint, cameraZoomAt | Inverse SVG screen matrix, pointer-centered exponential wheel zoom; anchor maintained unless boundary clamp intervenes. |
| cameraPan, cameraPointers, cameraPointerEnd | Pointer-event drag (5 px threshold), capture, release/cancel/blur, click suppression; two-finger distance ratio and midpoint translation for pinch and pan. |
| cameraMini, cameraMap, cameraMapViewport | Orthographic overview using same P() projection, decorative floor plan, four actor markers on floor 1, clipped visible rectangle; floor switch invalidates marker cache. No canonical position. |
| cameraManual, cameraKeys | Manual camera interactions cancel follow, keyboard arrows/+/-/Home, semantic buttons retained. |
| changeCharacter wrapper | Valid active-floor selection focuses actor at 1.75×; existing optional follow maintained. |
| draw wrapper, cameraRenderedFloor, cameraStyle | 320 ms floor entrance opacity/translation, no deferred floor authority; reduced-motion bypass. |
| motionPaint, motionStatus wrappers | Mini-map marker refresh with existing ~30 fps paint; passive floor follow disabled; previous motion model retained. |
| ResizeObserver | Recompute viewBox for actual viewport aspect ratio. |
| build.py, office.html | Exact 02.3 hash pin, deterministic inline injection; self-contained offline HTML. |
| test_camera.py, TEST_EVIDENCE.json | 54 selected Chromium set_content checks: desktop mouse/wheel, key, map, role/floor/follow, motion and emulated touch (CDP actual input events). |
| PROGRESS.json, SOURCE_MANIFEST.json | Separate local package count, unchanged product scores, SHA-256/Git blob pins. |

## Test findings and fixes
Initial floor switch test caught stale markers: the reset cache value equaled empty marker string; invalidated cache using null, reran. Touch reset check required a short wait after real emulated touch input to observe click delivery (test synchronization, not a product claim). Added four checks for drag vs selection, follow arbitration while paused and passive-floor follow disablement. Final 54/54 selected checks PASS. Previous 42 checks are historical and not added or claimed rerun. Screenshots are actual standalone Chromium render. No native mobile device, product build, full React/Next/Phaser tests, performance benchmarking or independent acceptance.

## Maintenance / diagnostics / rollback
Build: `python build.py ../02.3/office.html` (or explicit exact file); test: `python test_camera.py` (Playwright Python, Chromium, optional CHROMIUM_PATH). Open office.html locally; test environment uses set_content. If zoom/pan wrong inspect getScreenCTM, cameraBox and clamp; if touch stuck inspect pointer map, capture/cancel; if marker stale inspect floor cache invalidation; if follow conflicts inspect cameraManual and motionStatus wrappers. Keep 02.3 unchanged and open it to roll back, never revert shared product. No new product dependencies or DB/API changes. No real positions, collisions or authority derived from visual state.

## Provisional choices / residual limits
1–2.4 zoom, 1.75 focus, 5px drag threshold, 320ms floor effect, mini-map placement/palette and marker sizes are design choices. Zoom anchor may shift when clamped; at fit zoom an axis can have extra background on differing screen ratios. No inertial pan, floor elevator simulation or full 3D. No multi-agent collision/path reservation or complete furniture depth sorting; previous SVG visual limits remain. Touch verified in emulated Chromium, not on physical iOS/Android. Product frontend, EDS and Office Engine remain 50/100 ordinal source scores, last recorded baseline; no promotion. Local program 4/5 first slices, not acceptance.

## Next — 02.5
Read latest common base, compare actual Next/Phaser rendering and OfficeV0 contracts. Map presentation-only components, canonical geometry and verified state adapters, preserve fail-closed/stale states and passive floor. Prepare exact file ownership and integration review, no silent merge of divergent workstreams. Full pinned build/browser/mobile/contract tests and independent gates tracked separately. Only raise official scores with evidence; separate prototype readiness from product acceptance.
