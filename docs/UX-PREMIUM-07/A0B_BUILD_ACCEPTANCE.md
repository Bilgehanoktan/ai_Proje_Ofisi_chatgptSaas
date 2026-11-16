# UX-PREMIUM-07-A0B — reviewed build/native baseline
2026-11-16 | D0 isolated workstream | A0 still BLOCKED; do not start A1–A5.

## Baseline and executed evidence
Parent e7cdb4b4137c76f15b893409e58112bdd9de0ed9; product manifest c61c2006d3c01877ef002664e585c7c5289c1676, 398 pins/399 files, 181 frontend. A0 delivery 12/12 SHA-256 and CRC PASS; remote path/size 398/398, 55/55 core29 static lock paths/bytes/blob IDs, 16/16 contract/fixture pair blob parity. Full checkout/hash recomputation not performed. Six exact selected TypeScript/test files reproduced locally; actual Node 22.16.0 and global TS 5.8.3 strict compile: model 16 + traffic 12 + boundary 3 = 31 selected PASS. 12 adapter checks PASS: 7 actual original chain/pin/local helpers and 5 deliberately doubled smoke control-flow cases. No full product tests implied. All three original runner files recovered and exact Git blobs verified; actual original W8 verify rejects incomplete checkout. Historical A0 15 and UX06 92 not additive.

## Implemented harness extension
w8_ux_a0b.py pins P10G/P10F/unified, selects current manifest only in process, preserves original review/lock/aux/installation/full backend/Next/typecheck/smoke and DB hash checks. Adds three selected office suites with pinned TS inside reviewed stage. Pins native_ux_a0b.py into auxiliary stage. During original smoke, after the pinned last original browser script, runs the new native smoke against the same loopback servers before original DB hash guard; NATIVE_SMOKE_OK only after both native and original reviewed smoke complete. Failure, missing or duplicate hook removes smoke markers in reviewed stage. Native script: explicit Chromium path, loopback origins, intercepted nonlocal HTTP requests fail test, real route canvas/JOIN_HOLD, atlas, camera/minimap, decorative roles, passive floor, reduced motion/reset/reload and page errors. Captures actual screenshot only on real run. Original 02.5B/03/05 scripts unchanged; eight combined groups are a new harness, not a claim of running old scripts individually. No manual art/depth/GPU acceptance. No API, DB, product code, package pins, authority, or core changes. No CI/main/PROD/provider/spend.

## Blocker and next execution
Git DNS failed; registry ping EAI_AGAIN, offline package-only lock ENOTCACHED, package-only build probe next not found exit 127. No full install/build or actual native browser; no fabricated image. Complete exact authenticated checkout of this branch on approved environment. Audit before dependency resolution. From clean repo:
```powershell
py -3 tests/integration/w8_ux_a0b.py audit
py -3 tests/integration/w8_ux_a0b.py prepare --stage C:\AIOS\ux-a0b-stage
```
Stage must be new outside repo. Review generated locks/REVIEW.json, npm lock, Python wheel provenance and pinned transitive graph before using its reviewed SHA-256. Do not auto-approve. Then:
```powershell
py -3 tests/integration/w8_ux_a0b.py install --stage C:\AIOS\ux-a0b-stage --approve $reviewedHash
py -3 tests/integration/w8_ux_a0b.py test --stage C:\AIOS\ux-a0b-stage --approve $reviewedHash
py -3 tests/integration/w8_ux_a0b.py smoke --stage C:\AIOS\ux-a0b-stage --approve $reviewedHash --chromium $chromePath
```
Stop on any nonzero exit; preserve diagnostics and use fresh stage on retry. Windows commands prepared, not run. NATIVE_EVIDENCE.json alone is not W8 smoke acceptance; check BUILD_TEST_OK, SMOKE_OK, NATIVE_SMOKE_OK, DB hashes and screenshots. Manual visual/occlusion and HD acceptance separate; OfficeV0 JOIN_HOLD owner 0/55, independent HOLD. No A1–A5 before reviewed A0. A6 contract review only. Diagnose pin mismatch with exact branch and Git blob, network failures with approved registry, native failure from console/screenshot and original runner logs. Rollback remove three new test infrastructure paths and documentation delta by selecting parent; product unchanged. Engineering decision: extend existing W8 rather than create a competing acceptance workflow; last smoke hook relies on pinned parent and is guarded against absent/duplicate invocation. No normative decision or new dependency.
