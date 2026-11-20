# MI-P0 Office post-fetch deadline QA — R2, 20.11.2026

This is an **additive evidence revision**. Earlier R1 source/test results and the architectural record remain intact; R2 replaces only the current selected QA count 4→5 and supplies one actual Node wall-clock deadline measurement, not full product acceptance.

## Repro and change register
- Why: Owner PR22 R2 test suite has distinct post-fetch coverage; R1 validated read/cancel and controlled abort but not a real timer.
- Where: isolated review PR28's `test_postfetch_stall.cjs` appended one `actual 2500ms AbortSignal.timeout` test. `run_postfetch_check.sh` updated **only the exact test SHA256 pin**; two new R2 evidence files created. No API, product, database, dependencies, CI or grants.
- How: run `bash run_postfetch_check.sh /exact/PR22/route.ts /outside/path/output.tap` in isolated Node v22.16.0 + tsc 5.8.3 environment. Runner aborts on original route SHA256 mismatch, test SHA256 mismatch, Node/tsc mismatch; compiles exact 2114-byte PR22 R2 source with only parser and port stubs.
- Original source Git blob `ae42ecccdda987c00537696f2698f49c374ec927` / SHA256 `bf03304a9e8705d68c9c8987f7c03a928eb27b728d9daca44d33b86b2b9677aa`. New test blob `0f245680e16c3ae401eb2627489618109f56131a`; new runner blob `b6a0b625662369295d2e6813161e565ff918ea7c`.
- Real rerun on exact source: **5/5 PASS**, including abort while actual `reader.read` and `reader.cancel` methods had been entered, plus real Node 2500ms signal `GET()` → HTTP 503 (measured subtest 2509.826ms). Raw TAP Git blob `d9dd694954c23cd148f7fa9e0a3002343f73c6ee`, SHA256 `9227e2dd5c39e3af1e569aaf1ae1f835b9b71dbffdbb191f108fe9acf1e72261`.
- First run 4/4 and original PR23/PR22 owner tests are distinct historical evidence. No double counting into product acceptance.

## Technical catalog delta
`test_postfetch_stall.cjs` adds one new Node `node:test` case using native `AbortSignal.timeout(2500)` with actual wall-clock `performance.now()` and an 8.5s watchdog; not a new exported product symbol. `run_postfetch_check.sh` pins the new test SHA; compile and cleanup semantics unchanged. R2 new evidence JSON and TAP; source manifest/API/DB/events/product dependencies untouched.

## Remaining gates
This real timer is **an isolated mocked-transport runtime measurement**, not the original Next server, customer network or PROD SLA. PR22 owner review, project TS 5.9.3, native browser/full W8 C04–C08, 553→562 source variant and independent PG/root/issuer/sink/IV remain **HOLD/NOT_RUN**. Canonical product acceptance **Core 12/16; UI 21/40; MVP 0/11; IV 0/7**, delta **0 percentage points**. Global 15/35/20/20/10 metric remains **HESAPLANAMADI** until owner-ratified denominators.

## Maintenance/rollback
If owner route or fixture source changes, stop on SHA failure and review new source; never silently repin. Diagnose unexpected hanging by retaining TAP and whether `read`/`cancel` was reached. Roll back only PR28 isolated QA files with normal revert or close draft PR; do not edit PR22/23, main, product-dev, releases or authority claims. Owner next: PR22/MI05 review R2 and PR20/MI01 full source-pinned W8.
