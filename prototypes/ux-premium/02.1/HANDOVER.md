# UX-PREMIUM-02.1 — Office visual overhaul
Date: 2026-11-16. Status: STANDALONE_DESIGN_PROTOTYPE / NOT_PRODUCT_INTEGRATED.

## Isolation and baseline
- Product reference: integration/ui-0211-p10e, commit 14738822c38eb179825e00a01e48e2a3a0c16c3d. New branch integration/ux-premium-02-office-motion. New files only under prototypes/ux-premium/02.1/. No changes to product/, common architecture, catalog, API contracts, DB, trackers, main or other branches. No merge.
- Previous UX-PREMIUM-01 remains unchanged; this new standalone scene does not replace its dashboard or route. Decorative coordinate system is not OfficeV0 geometry. Four room zones are design intent, not station allocation. Second floor inactive. No agents, runs, spend or authority. No network or runtime integration.

## Technical catalog delta
| File / symbol | What, why, how |
|---|---|
| office.html / CSS | Atelier palette and responsive split layout, visual only |
| P, pt, poly, rect, box, line | Isometric coordinate transform and geometric primitives |
| rug, chair, monitor, desk, plant, sofa, glass, wall, board | Original procedural SVG decor, wood, seating, display, partition, greenery |
| rooms, roomLabel, draw | Four selectable room zones, floor 2 inactive; no canonical geometry |
| camera, reset, focusRoom, panel | Bounded zoom and pan, room focus, floor selection, keyboard activation |
| test_office.py | 16 standalone Chromium checks, screenshots; product acceptance excluded |
| TEST_EVIDENCE.json | Actual selected checks; no external HTTP or JS errors |
| SOURCE_MANIFEST.json | Source SHA-256 and Git blob IDs for exact readback |

## Progress (local work packages, not product maturity)
1. Office art + executive spaces: first visual slice done; final asset quality not accepted.
2. Avatar pack: not started here; previous role markers only.
3. Motion demo: not started here.
4. Camera: partial early implementation; button pan, zoom, focus; drag and animation pending.
5. Integration-ready prototype: pending; no Next.js/Phaser integration.
Official ordinal frontend, EDS and Office Engine source scores remain 50/100 as recorded in TRACK-0210; no new product score.

## Tests / maintenance
Run python test_office.py (Python Playwright and Chromium; CHROMIUM_PATH override). Chromium set_content rather than full Next.js/browser product. 16/16 PASS. Mobile width, keyboard, camera and passive floor verified; visual design manually inspected. No full build/Phaser/real runtime/independent acceptance. Current asset geometry has no verified collision/occlusion or route graph. Text and room IDs are decorative constants. Inspect draw()/primitive order for overlaps; camera() clamps; floor reset and focusRoom() for state issues. Roll back by dropping the isolated new folder or using original UX-PREMIUM-01; never overwrite shared product files.

## Next
UX-PREMIUM-02.2: original human-like 4-role character asset set, explicit synthetic state markers, poses and selection; then 02.3 motion, 02.4 camera drag/accessibility, 02.5 integration contract/diff. Re-read current product branch before any merge. Retain safety and evidence badges; no silent promotion or score increase. Palette, room dimensions, furniture and camera limits are provisional engineering choices.
