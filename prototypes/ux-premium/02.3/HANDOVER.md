# UX-PREMIUM-02.3 — Motion Lab
Date: 2026-11-16. STANDALONE_DESIGN_PROTOTYPE / NOT_PRODUCT_INTEGRATED.

## Source and scope
Parent commit 4ae38f774966089fdeb565bcca8d7165d4e42e76; parent 02.2 office.html blob 846c57c31ee4ff40a38f65d7bef196cab1d3d027; SHA-256 86e177752f922a6fe498a93e7fd4aa31768267d716df4ca15cb7a1bd3c96f0a3. Parent package 14/14 manifest entries matched, CRC passed. Work only in prototypes/ux-premium/02.3/ on integration/ux-premium-02-office-motion. No product/, shared tracker, API, database, canonical architecture or other branch writes; no merge. H01 remains the sole human CEO; actors are role templates, not actual employees, tasks, permission, dispatch or ledger evidence. No network or external effect.

## Architecture and catalog delta
| File/symbol | What / why / how |
|---|---|
| motion.js / motionGraph, motionEdges | Fixed decorative graph, doors/corridor/approach/home/meeting/lounge anchors. Undirected local edges, no canonical OfficeV0 equivalence. Four distinct home, meeting and rest seats. |
| motionPath(start,end) | Breadth-first traversal over fixed edges, returns route or null; deterministic given fixed edge order. |
| motionActors, motionTarget | Per-role local display state, position, route, mode, phase and facing; no backend source. |
| motionCommand(id,mode) | Allowlisted role/mode; rejects passive floor and busy transitions; routes from current node; reduced-motion snaps to target. |
| motionAdvance(s,dt), motionFinish | 108 decorative units/s; consumes distance along segments, seated-to-standing and sitting transition (350 ms), walking/working/meeting/resting/idle. No scheduler or real task state. |
| motionRig(a,s) | Original palette, articulated SVG legs, arms, facing mirror, walk stride, idle breathing, typing, meeting gestures and seated poses; reduced-motion disables movement. |
| motionPaint(), avatarLayer | Transforms actors with P(); role selection outline and seat-back foreground overlay for work/meeting; optional camera follow; no collision/pathfinding proof. |
| renderCast(), changeCharacter(), motionStatus() | Local motion commands, role selection, pause/reset/follow, accessible status and disabled state; inherited floor/room/keyboard controls. |
| motionLoop, reducedMotion change handler | requestAnimationFrame, delta cap 50 ms, painting at about 30 fps; pause/floor 2 freeze regular advancement; reduced-motion snap on preference change. |
| build.py | Exact parent SHA-256 check, deterministic inline injection to office.html; no parent write. |
| test_motion.py / TEST_EVIDENCE.json | Selected Chromium set_content checks including real RAF, deterministic stepping, seat anchor, focus, pause, reduced motion, floor and network. |
| PROGRESS.json / SOURCE_MANIFEST.json | Local milestones separate from unchanged product scores; SHA-256 and Git blob pins. |

## Maintenance / diagnostics / rollback
Build: python build.py ../02.2/office.html (or exact path). Test: python test_motion.py (Python Playwright, Chromium; CHROMIUM_PATH optional). Open generated office.html locally. Tests use set_content (not full Next/browser product or Phaser). If routes are wrong inspect motionGraph/Edges and scene door geometry, if posture misaligns inspect seat anchors and motionRig, if follow conflicts inspect manual camera capture listener; if character freezes inspect floor, motionPaused, state and remaining path. Restore prior prototype by opening unchanged 02.2; never revert shared product files. No API, DB or dependency changes. Presentation only.

## Limits and provisional decisions
SVG 2D not photorealistic 3D. Route graph hand-authored against decorative geometry; no physical collision or multi-agent path reservation; actors can overlap each other or furniture. Chair foreground correction limited to two modes, not full depth sorting. Meeting means a selected actor reaches a distinct meeting seat and gestures; group coordination is not implemented. Rest is a separate seated lounge location. Direction is left/right mirror, not full directional sprites. Speed, 350 ms pose duration, routes, lounge anchors, camera follow zoom and gesture amplitudes are provisional design decisions. No real clock/lease/task proof, no API or OfficeV0 bind, no product build or independent acceptance. Full product score unchanged. 

## Next
02.4 camera: pointer/touch drag, pointer-centered zoom, map bounds and minimap, floor transition, focus/follow arbitration, camera accessibility and responsive tests; then 02.5 contract-preserving integration review on latest common base. Maintain isolated prototype history.
