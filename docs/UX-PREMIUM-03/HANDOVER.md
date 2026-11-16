# UX-PREMIUM-03 — Native office cooperative routing, art, minimap and D0 source inspection
2026-11-16 | isolated UI delta from UX-PREMIUM-02.5B head `e5f8e4dd356ed839b1722da1edddef8ca0d4b994`. D0 source only, independent HOLD. Full product / renderer NOT_RUN.

## Architecture delta / decision record
Preserve 02.4, 02.5A, 02.5B, P10G and core branches. No change to OfficeV0 schemas, backend, APIs, databases, package pins, policy or real agent state. Local visual movement cannot imply real work. Maintain 12×10 decorative geometry separate from snapshot `draft-hybrid-floor-1` and backend canonical layout. D0 sample is fixed, not current; no live join. The existing fixed GET `/api/demo/office-workbench` transport/parser is used only on explicit read, with no cross-source join; failed reads HOLD, not simulated values. Existing fixture Git blob `ac57b926e701196c7507a396aa868ce5e8bd5806`. Existing package blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3`.

## Technical catalog / change rationale
| File relative to frontend | Symbols and maintenance |
|---|---|
| office/engine/premiumRouting.ts | `pairEscape`: deterministic two-agent joint-state BFS, capped 14,400 states; one actor per recovery edge, no swaps, other actors fixed. `depthAt`: foot/front point + stable tie; `cameraViewport`: world-space viewport math. |
| office/engine/premiumModel.ts | `scheduler`, `routeStatus`, `begin`, `move`, `findRecovery`, `advance`, `command`: round-robin priority, conservative source/destination reservation, pair rescue only after stall and no in-flight edges. Replan on valid command; 30-tick retry cap interval. `projectionBoundary` unchanged. |
| office/scenes/premiumArt.ts | `box`, `drawFurnitureCell`, `drawAvatar`: original procedural 2.5D geometry, material shade, separate furniture footprint tiles, role palette, walking limbs, seated posture, selection; no external asset dependency or sprite license. |
| office/scenes/PremiumNativeScene.tsx | `PremiumNativeScene`: split art renderer; depth sort; fixed secondary Phaser camera, world marker, click-to-center and gesture isolation, local camera diagnostics, read-only OfficeV0 panel. Previous fallback, reduced motion, floor reserve, pinch/pan and local control retained. |
| office/engine/premiumOfficeV0.ts | `inspectOfficeV0`: exact historical fixture structural inspection; any mismatch => UNVERIFIED and JOIN_HOLD. Source matches never create authority, placement, verified active runs or task binding. |
| tests/premium-model.test.cjs | 14 cases incl. resolved opposing goal and interruption; 12 unchanged prior behaviors. |
| tests/premium-routing.test.cjs | 10 cases: pair search, impossible corridor, fixed actor, limit, determinism, depth and zoom math. |
| tests/premium-office-v0.test.cjs | 13 cases, exact fixture + negative changes. |

## Scope, results and limitations
- Node 22.16.0 / TypeScript 5.8.3 strict helper compile and test: model 14/14; routing 10/10; OfficeV0 13/13, total 37 selected tests. No sum with prior releases. Test fixture and package locally reconstructed and git blob identities matched exact reviewed baseline. Source syntax transpile for native files is not real Phaser/React typecheck. Exact dependency pins Next 15.5.29, React 19.1.10, Phaser 3.90.0, TS 5.9.3 unchanged. `npm view phaser@3.90.0` -> EAI_AGAIN; `npm run build` -> next: not found in isolated pin preflight. No full checkout/build/browser test. Native E2E script prepared, not run.
- Recovery supports pair deadlocks where an escape exists, not arbitrary 3+/global multi-agent liveness or swept-body collision. Retry can stall on impossible topology; no teleport. Round-robin does not prove fairness. Depth is per-footprint painter ordering, not physical occlusion; real visual acceptance still open. Mini map camera and touch interaction need actual Phaser tests. Chair/desk assets are procedural art, not licensed sprite pack or verified renderer screenshots. D0 readback is not cryptographic attestation or actual OfficeV0 canonical data connection; missing independent source/lease/epoch/geometry mapping remains JOIN_HOLD.
- Engineering preferences: UX-PREMIUM-03 label, pair BFS bounded state, round-robin/30 ticks, per-tile furniture, native second camera, historical source inspection. No normative decision or gate change. Existing shared Design Master pointer is untouched; this is scoped addendum.

## Replay / maintenance / rollback
On reviewed 02.5B checkout apply delta, run strict tsc helper commands below, then pinned typecheck/build and prepared E2E only on authorized isolated environment. On route stall inspect occupied source/dest, routeStatus and pair rescue; no blind teleport. On depth artifact inspect footprint/front anchor and actual painter order. On minimap issue inspect actual Phaser camera order, worldView and pointer CSS scale; do not relax sandbox. On source mismatch inspect exact fixture/schema and existing parser; never map unknown data to actors. Rollback select parent `e5f8e4dd356ed839b1722da1edddef8ca0d4b994` or revert this isolated delta plus product manifest; no migration.

From frontend root (temporary output directory):
```
tsc --strict --target ES2022 --module commonjs --outDir /tmp/premium3 office/engine/premiumModel.ts office/engine/premiumRouting.ts office/engine/premiumOfficeV0.ts
node tests/premium-model.test.cjs /tmp/premium3/premiumModel.js
node tests/premium-routing.test.cjs /tmp/premium3/premiumRouting.js
node tests/premium-office-v0.test.cjs /tmp/premium3/premiumOfficeV0.js "$PWD/fixtures/office.snapshot.json"
```
Then exact dependency environment: `npm run typecheck`, `npm run build`, `npm run dev`, and `python docs/UX-PREMIUM-03/test_native_e2e.py http://127.0.0.1:3000` from repo root. Full visual acceptance includes avatar occlusion, camera bounds, minimap click, touch pinch/cancel, reduced motion, hydration, WebGL/Canvas fallback. Next: verify actual renderer and full Next build; reconcile OfficeV0 exact scope/sequence/freshness/layout/instance/lease/task proof and independent verification; keep core merge separate. No maturity percentage increase without real build/render proof.
