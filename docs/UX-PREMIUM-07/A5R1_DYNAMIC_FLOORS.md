# UX-PREMIUM-07-A5R1 — D0 dynamic floors and portal protocol
Parent d8671883a77ee7f97b1fc3528e3ffdc1831b3856, A4R2. User direction 2026-11-17: defer Windows; isolated A5 source and synthetic model tests allowed. CEO-0174/0179=B, DEC-28B/C-D, A5 plan. No native acceptance promotion.
## Scope and change
Add premiumDynamicFloors.ts and premium-dynamic-floors.test.cjs in product frontend. Existing premiumLift, A1 geometry, A2 registry, A3 traffic, A4R2 scenes and W8 harness unchanged. This is an isolated successor candidate to the legacy role-keyed lift; not imported by either renderer. A5R2 must adapt exact A1/A2/A3 inputs and coordinate reservations with a single traffic writer. No fake second-floor activation, no real agent placement, no API, DB, dependencies or authority.
Floor declarations have explicit D0 IDs, revision, immutable cells and department IDs. nextFloorReview is a design sequence only; no lifecycle mutation. Only explicitly ACTIVE synthetic floors permit actor placement/transfer, all other states block. No real approval, station allocation or departmental lifecycle inferred. Current production-candidate reserve remains passive; A1 portal remains disabled.
Portal has declared distinct stops per floor, separate bounded queue, one passenger at a time. Source reservation on enqueue, destination reservation before positioning/boarding, FIFO head waits if occupied. IDLE→POSITIONING (if needed)→BOARDING→TRAVEL→EXIT→IDLE. Source occupancy remains conservative during transit; destination placement commits exactly once on exit; inTransit is D0 marker. Cancellation only before travel, releases reservations; replayed request IDs rejected even after cancellation. Movement is sequential single-cell local fixture movement, not A3 global routing. Local tokens are frozen object identities plus revision/step, not serialized grants; recreate fixture to change layout. Snapshot immutable; no shared external trust.
## Verification
Actual isolated strict TypeScript 5.8.3 compile and Node 22.16.0 tests 12/12 PASS. Initial TS narrowing error corrected before successful compile. Exact two Git blob pins match local files. A4R2 76 model and 12 harness historical, not rerun. A4R2 Windows build/native NOT_RUN, A5 full build/native NOT_RUN, HD 0/36, OfficeV0 JOIN_HOLD 0/55, independent HOLD. No screenshots. Git local checkout DNS blocked.
Run from frontend directory with temporary output outside repo:
```powershell
$out = Join-Path ([System.IO.Path]::GetTempPath()) ('aios-a5-' + [guid]::NewGuid())
npx --no-install tsc --strict --target ES2020 --module commonjs --outDir $out office/engine/premiumDynamicFloors.ts
if ($LASTEXITCODE -ne 0) { throw 'A5 compile failed' }
$env:A5_MODEL = Join-Path $out 'premiumDynamicFloors.js'
node --test tests/premium-dynamic-floors.test.cjs
if ($LASTEXITCODE -ne 0) { throw 'A5 tests failed' }
Remove-Item Env:A5_MODEL
```
Run only with reviewed installed dependencies; do not install or change pins. Current A4R2 W8 is manifest-bound to its parent; run on A4R2 exact checkout, not this branch until separately rebound.
## Engineering choices / limitations
Candidate bounds 32 floors, 32 portals, 128 actors, 128 queued requests per portal, 256×256 coordinate envelope and 10000 lifetime request IDs; not validated capacity or normative limits. One landing per stop, source remains occupied through exit, no waiting bay, no automatic deadlock recovery. Reciprocal requests can HOLD indefinitely; cancel preboarding request then clear landing. No real timing, dynamic lifecycle transition, role/station assignment, persistence, crash recovery, graph route integration, multiportal load or performance acceptance. Local cell fixture tests only. Next: A5R2 exact A1/A2 adapter with per-floor room/station IDs, A3 reservation coupling and no double movement writer; synthetic multiportal/FIFO, 4/6/8/12 actors, bounded wait and recovery tests. Renderer transition and native acceptance after A4R2 Windows review. A6 contract review separate, 55-field owners still pending.
## Diagnose / rollback
STALE_TOKEN: use current snapshot token, never fabricate or reuse across instances. REQUEST_BLOCKED: inspect source cell, active fixture state, capacity, duplicate ID. LANDING_BLOCKED: inspect occupation and reservation; no skip or teleport. CANCEL_BLOCKED: retain travel until exit. PORTAL_INVARIANT: freeze candidate, retain snapshot; do not force release. Revert isolated branch to pinned A4R2 parent; remove two new source files and their manifest entries only if reverting by patch. No DB migration. No main, CI, provider, spend or production.
## Parallel scope
A6R1 438985fea059f0ffafdfa16f0d090cb854b5fc36; UI P10J20 ae3f5e45c8dc77359f5ae7701efc833585d3c4a9; core 0226 c715e1edfd1af021b4c0be0681c6958455b6a26f observed. No changes to those branches; no automatic merge or shared manifest copy.
