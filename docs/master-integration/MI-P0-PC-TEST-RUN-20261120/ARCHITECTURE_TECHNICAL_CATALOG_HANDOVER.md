# AI Company OS — MI-P0 PC test handoff | 2026-11-20

## Scope and authority
H01 explicitly requests local PC testing of W8, current ORG G7, and protected PostgreSQL/security. The current ChatGPT environment can read GitHub and local attached files in an isolated Linux container, but cannot directly execute Windows PowerShell or control a local Windows PC. This turn prepared an executable offline test kit; **the actual Windows tests have not run**. Under CEO-0174 and CEO-0179=B isolated DEV and local synthetic tests remain authorized; production, real grants, protected PG independent security and IV acceptance remain HOLD.

## Immutable owner references
- Canonical 553 product files / 552 manifest: integration/product-dev at 254e0188998d0d245bd8ee4eb901aead02951a66.
- MI-01 W8 owner PR20 head 99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542; source manifest Git blob 27b4eb5816265d4e6e6d2458acb6220db7dd0c76; runner blob b4043035e75c5a18b7b19a9f18eecfef8e8fe677; frozen npm helper 257ba8f110508ff30ad03212111cfe8e2299d801.
- MI-04 PR19 immutable 562 source target 93e6c84db1a061ee914aa2c1d543620404515c0b. Original G7 test checkout Git blob 6bd86d7972c8bca511b5702117be3542431e7493; PR24 current ORG test runner blob 48bc0a7c6582defac61a5e346fd923af200d1d88.
- Existing W8, ORG, Office, PG, release and security PR ownership was not modified.

## Technical catalog: source paths / symbols / API / DB / dependencies
| File / symbol | Role | Test classification |
|---|---|---|
| scripts/pc-tests/20261120/aios_pc_runner.py — Session, checkout, blob, must_equal | Creates exact clean Git checkouts, rechecks Git SHA1 blobs and SHA256 files, logs processes, persists JSON with distinct gate states | New PC test orchestration only |
| Session.g7 | Invokes unchanged PR24 runner on exact PR19 checkout; requires 7 original test methods on current product OperationsStore | Original G7 remains NOT_RUN until executed |
| Session.w8_audit, Session.w8_prepare | Invokes owner PR20 original U3 audit and C04 prepare; creates frozen npm/wheelhouse REVIEW.json | Does not perform C05 owner approval or install |
| Session.w8_full | Only with supplied independently reviewed 64-hex SHA and explicit Chromium executable; invokes C06 install, C07 test/build, C08 native smoke | BLOCKED pending C05 independent owner review |
| Session.pg_probe | Read-only pg_isready to 127.0.0.1:5432 | Does not test protected PG RLS/COMMIT/restore |
| test_aios_pc_runner.py — PCToolSafetyGuards | 12 pure stdlib safety regressions: SHA/hash, symlink, source absence, no auto-approve, local probe isolation, failed subprocess log | Actual 12/12 local helper PASS |
| run_example.ps1 | Wrapper calling Python allsafe; does not change execution policy | Windows NOT_RUN |
| EVIDENCE.json, SHA256SUMS.txt, README_TR.md, test_guard_12_PASS.log | Source pin, architecture/runbook, raw evidence and rollback records | GitHub exact 8/8 blob readback |

No product modules, APIs, DB tables/migrations, events, dependency lock, workflow triggers, main or production grants modified.

## Results and evidence
- Linux container: Python3.13.5 helper tests 12/12 PASS with zero failures/skips, 3 Python files py_compile PASS, ZIP archive CRC PASS.
- Source and delivery exact SHA256 listed in EVIDENCE.json and SHA256SUMS.txt. Full Windows test kit ZIP SHA256: df91cdabb13c20adbd564d107bb74d1003790ca93d3b69679b623abad2683bc0.
- Windows W8 original C04-C08: NOT_RUN/HOLD, current ORG original 7: 0/7 NOT_RUN. Protected PG nonowner RLS/COMMIT/restore, independent root/issuer/sink and IV remain HOLD. No local PC commands were executed.
- Canonical acceptance unchanged: Core 12/16, UI 21/40, MVP 0/11, IV 0/7. Development percentages weighted 15/35/20/20/10 require owner-approved denominators; currently 0/10 groups, therefore NOT CALCULABLE. Acceptance change 0 percentage points.

## Maintenance, diagnostics, handover and rollback
README_TR.md provides a single PowerShell command: python -B C:\AIOS\TEST_KIT\aios_pc_runner.py --mode allsafe --root C:\AIOS\TEST_RUN_20261120. It clones two source commits into separate isolated directories, executes exact-source G7 tests, original W8 source audit/C04 wheel preparation, and read-only PG port probe. One gate failure does not erase other reports. Logs and PC_TEST_RESULTS.json stay on the user's PC.
- Git SHA mismatch, dirty checkout or wrong runner blob => fail closed. Never repin to make test pass.
- Git clone denied => user resolves their own GitHub authentication without sharing credentials.
- Partial W8 C04 stage => preserve logs and use a fresh isolated root for retries.
- C05 supply chain/license review must be completed before second-phase install/test/browser; no automatic acceptance. Protected PG, live authority/issuer custody and independent IV require separate owners and actual evidence.
- Rollback: close this draft PR or revert only its new review files; deleting the isolated Windows TEST_RUN folder after preserving test evidence does not touch product-dev, main, production database, existing permissions or owners.

No new CEO policy decision is claimed. Next step is actual one-command execution on the PC or entering Work/Computer Use mode with an available PC-control connection; then attach the scrubbed result JSON/logs for validation.
