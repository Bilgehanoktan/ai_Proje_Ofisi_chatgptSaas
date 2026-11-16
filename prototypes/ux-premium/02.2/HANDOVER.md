# UX-PREMIUM-02.2 — Character Lab
Date: 2026-11-16. STANDALONE_DESIGN_PROTOTYPE / NOT_PRODUCT_INTEGRATED.

## Baseline and ownership
Parent Git commit 36f326bcc4a56bf94bd782dadd6a84678961be1b; parent 02.1 office.html Git blob e08aca8f9dc55b04d9e47461ec76aa5d03193947. Work only in prototypes/ux-premium/02.2/ on integration/ux-premium-02-office-motion. Never modify 02.1, product/, shared trackers, API contracts, canonical architecture or other branches. No merge. D0 decorative role templates, not actual agents, assignments, authority, money or task state. H01 remains the only human CEO; Orchestrator depiction is not H01.

## Technical catalog / architecture delta
| File / symbol | What / why / how |
|---|---|
| avatars.js / cast | Four fixed role palettes, facial features, decorative positions and seat anchors; local only |
| character(a,p) | Original SVG groups for shoes, legs, torso, arms, hands, neck, face, hair, glasses; standing/seated geometry |
| avatarLayer() | Draw role templates on floor 1 only, using 02.1 P() transform; selected pose only; passive floor empty |
| renderCast() | Accessible card selection and pose controls; no network or mutation |
| changeCharacter() | Allowlist role and pose, redraw, restore focus; local presentation state |
| draw/panel wrappers | Preserve original 02.1 scene, room and floor logic; overlay separate from canonical OfficeV0 |
| build.py | Pin parent SHA-256, embed CSS and JS; deterministic generated office.html |
| test_avatars.py | Standalone Chromium controls and screenshots, with offline set_content |
| TEST_EVIDENCE.json | 20 selected actual checks, not additive to previous 16 |
| PROGRESS.json | Local work package stage, product maturity unchanged |
| SOURCE_MANIFEST.json | Git blob and SHA-256 pins for authored/generated source and evidence |

## Maintenance, diagnosis, rollback
Build: python build.py ../02.1/office.html (or explicit exact parent path). Open generated office.html offline. Test: python test_avatars.py; requires Python Playwright and Chromium (CHROMIUM_PATH override). The local file:// navigation was blocked by environment policy; test uses set_content. Initial test selector with unquoted numeric value fixed. No product build, Phaser, canonical geometry, collision or real agent test. If avatars overlap furniture, inspect cast x/y/seat, P() and SVG painter order. Check avatarLayer floor guard and changeCharacter allowlist for selection bugs. For keyboard focus verify data-cast and data-avatar handlers. Roll back by opening unchanged 02.1 or removing only 02.2 folder from isolated prototype branch; no shared change. Palette, skin/hair, role poses and decorative locations are provisional design decisions, not user identities or canonical station assignments. SVG characters are stylized 2D, not photorealistic 3D, and occlusion, animation rig, sitting alignment and multi-direction movement require refinement.

## Next
02.3: pose-driven walk/idle/typing/meeting motion with deterministic synthetic paths, pause/reduced-motion, no actual task inference; then 02.4 drag/pan/zoom and 02.5 integration review. Re-read latest product and branch ownership before integration. Source scores unchanged: Frontend 50, EDS 50, Office Engine 50. Local work packages 2/5 first slices; camera partial. Full acceptance remains open.
