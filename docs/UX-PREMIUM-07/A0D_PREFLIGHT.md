# UX-PREMIUM-07-A0D — exact checkout execution preparation
2026-11-16 | isolated Premium planning/acceptance tooling, no product change. Parent A6R1 438985fea059f0ffafdfa16f0d090cb854b5fc36. Actual product source remains A0C a79df6622e2eb9de63795ff6c0309984d1be6910, manifest f5b011cc9f72e85a7d1c371705e11e6dacfc9c42. UI P10J11 and core 0224 heads unchanged at observation. No feature work A1–A5 before A0 reviewed. A6 contract review remains 55/55 reviewed, owner and canonical 0/55.

## What/why/where/how
A0C full checkout still unavailable locally: Git actual fetch exit 128 DNS github.com, npm ping EAI_AGAIN; existing library archive metadata found but raw-byte access not authorized, no reconstruction claimed. P10J08 tested source 752b225deac4557a548faec7191a090fbfba19f7 and Premium A0C have all four direct dependency definition blobs identical (package.json and three Python requirements). This does not verify resolved transitive locks or build; do not copy review fingerprints/markers. Reuse existing W8 chain, no new competing runner or product change.

New standard-library bootstrap prepare_a0c.py solves Windows ZIP path length / fragmented console input and stale-stage confusion: creates a new short workspace, git init with repository-local longpaths=true/autocrlf=false, fetches exact commit only (uses existing Git authentication), checks FETCH_HEAD, detached HEAD, tracked status, manifest and A0C adapter blob, then calls original A0C audit/prepare. Prints REVIEW.json path and SHA-256; stops before approval, install, build or smoke. Existing workspace is refused, not deleted. No change to other sessions' worktrees, system Git config, sources, locks, DBs, or ports. Tests use actual Git subprocesses with local fixture repos and synthetic W8 subprocess. Seven pass, zero fail; Linux Python 3.13.5/Git 2.47.3. Actual remote run stopped at fetch; no stage created. Not Windows acceptance or product test. No new dependencies.

## Local next action
Download prepare_a0c.py to your preferred location, then execute from that folder:
```powershell
py -3 .\prepare_a0c.py --workspace C:\aios\premium-a0d
```
Use a new workspace path on each failed retry; don't delete other branches/stages. The existing W8 audit verifies all 398 SHA-256 records, 16 schema/fixture pairs and auxiliary pins. Prepare produces fresh REVIEW.json, npm lock and Python wheelhouse; review actual contents, not just hash. Do not auto approve. After review:
```powershell
cd C:\aios\premium-a0d\src
$stage = 'C:\aios\premium-a0d\stage'
$reviewedHash = '<explicitly reviewed SHA-256>'
py -3 tests/integration/w8_ux_a0c.py install --stage $stage --approve $reviewedHash
py -3 tests/integration/w8_ux_a0c.py test --stage $stage --approve $reviewedHash
py -3 tests/integration/w8_ux_a0c.py smoke --stage $stage --approve $reviewedHash --chromium $chromePath --frontend-port 17400 --backend-port 17401
```
Execute each only after previous exit 0; chromePath must be explicit existing reviewed executable; confirm ports free. Do not use literal placeholder or old P10J hash. Collect full stdout, review/lock inventory, markers, native evidence/screenshots. No new live activity. Diagnose fetch via actual network and Git authentication (never disclose credentials); source mismatch via exact commit and blob pins; review failures via dependency inventory; native failures via actual console/screenshots. Preserve failed workspace for diagnosis. Rollback is selecting A0C source and using original runner directly; no migration or live DB restoration.

## Integration
progress/UX_PREMIUM_07_A0D_INTEGRATION.json retains all 24 rows, A0–A7 and 16 core binary gates from A6R1. No gate score changed: core 7/16, historical UI 21/40, owner 0/55, independent 0/7, HD 0/36. Product source still 399 files including manifest; actual local full audit/build/Phaser NOT_RUN. Separate branch-specific architecture, technical catalog, progress and handover; no shared pointers changed.
