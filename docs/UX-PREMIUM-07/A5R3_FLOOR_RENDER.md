# UX-PREMIUM-07-A5R3 — read-only floor presentation and SVG diagnostic
Parent 2927259330934ed3a6ba51eb5f9105240aca832f; DEC-28B/C-D and A5 plan, CEO-0174/0179=B. User continues A5; Windows remains deferred. 
## Implementation
premiumFloorRender.ts binds one trusted in-process A5R2 snapshot reader; does not receive or expose motion commands and never constructs another world. Floor selector, floor-scoped rooms/stations/departments/landings, visible actor count and reservation list all come from one captured snapshot. Only ACTIVE fixture actors on selected floor and not inTransit render. Boarding actor stays on source; TRAVEL/EXIT passenger visible only in portal status; destination actor appears only after A5R1 exit commit. Passive floor shows design template, no occupants. Portal phase, queue length, wait reason, source/target and cabin floor report observed model values; no invented travel time or live runtime status. Camera fit per A1 dimensions; isometric coordinate formula matches A4 convention, not a native camera call. Floor selection increments viewEpoch, clears edge; reduced motion clears interpolation. For an observed contiguous single adjacent step with positionsVersion +1, interpolate 240 ms; skipped sequence or unfinished edge snaps to last observed valid position. Same-floor movement only; no cross-floor tween. Reader rejects wrong D0 scope, revision change, lower sequence and foreign equal-sequence token; throws and retains prior view for diagnostics. Caller must stop display/use on error and recreate bridge on world change. This is a trusted local typed reader, not external schema/freshness/tenant/security verification; higher sequence from foreign reader with same revision is not authenticated. No real authority.
premiumFloorSvg.ts produces isometric SVG diagnostic from FloorFrame: exact geometry and footprint bounds, station anchors, per-role actor markers, depth order, approach cells and reserved cells. Escaped string labels, simple original vector art. No network assets, animation loop, Phaser/React integration, actual cab motion or art acceptance. Four local SVGs and CairoSVG PNGs generated from actual fixture with 4/0/3/5 actor tags and checked as XML. Floor labels in SVG use unchanged A1 template zone names (F1-...), even on other floors; scoped room IDs remain in frame, not custom floor art.
## Actual validation
Parent delta 12/12 SHA256-size entries checked; six local original TS files matched Git blob IDs. Strict ES2020/CommonJS TypeScript 5.8.3 compilation with Node 22.16.0; 12 new model tests plus 17 A5R2 and 15 A5R1 regressions = 44/44 actual selected PASS. No A1-A4 full original test suite or project pinned TS 5.9.3 rerun. No native/Windows/full build, no HD/OfficeV0/independent acceptance promotion. Four SVG render checks are separate from 44 tests; not browser screenshots.
## Reproduce with reviewed installed toolchain, frontend root
```powershell
$out = Join-Path ([System.IO.Path]::GetTempPath()) ('aios-a5r3-' + [guid]::NewGuid())
npx --no-install tsc --strict --target ES2020 --module commonjs --outDir $out office/engine/premiumFloorSvg.ts office/engine/premiumFloorTraffic.ts
if ($LASTEXITCODE -ne 0) { throw 'compile failed' }
$env:A5R3_BUILD = $out
node --test tests/premium-floor-render.test.cjs
if ($LASTEXITCODE -ne 0) { throw 'render tests failed' }
node tests/premium-floor-traffic.test.cjs (Join-Path $out 'premiumFloorTraffic.js') (Join-Path $out 'premiumHybridLayout.js') (Join-Path $out 'premiumActorIdentity.js')
if ($LASTEXITCODE -ne 0) { throw 'A5R2 failed' }
$env:A5_MODEL = Join-Path $out 'premiumDynamicFloors.js'
node --test tests/premium-dynamic-floors.test.cjs
if ($LASTEXITCODE -ne 0) { throw 'A5R1 failed' }
Remove-Item Env:A5R3_BUILD,Env:A5_MODEL
```
No dependency install, W8 rebind or Windows acceptance attempted.
## Diagnosis / rollback
UNKNOWN_VIEW_FLOOR / VIEW_FLOOR_LOST: check explicit floor declaration, do not create floor. WORLD_VIEW_DISCONTINUITY / D0_VIEW_REQUIRED: halt readback, retain diagnostic evidence, recreate only against same authorized D0 fixture; not a runtime trust check. VIEWPORT_INVALID: keep prior valid viewport. Missing actor: compare inTransit, lifecycle and selected floor, not role or inferred state. On visual gap snap to latest observed state, no replay or teleport command. Revert candidate to exact parent, no DB migration. 
## Next
A5R4 source-level selected-floor scene shell, accessible floor controls, floor-scoped labels and distinct approved/candidate department geometry/art; isolated from existing native scene. Native renderer lifecycle/atlas reuse, physical cab animation and A4R2 review remain open. A6 separate contract review, JOIN_HOLD. No core merge, main, CI, PROD, external effects, spending or real data.
