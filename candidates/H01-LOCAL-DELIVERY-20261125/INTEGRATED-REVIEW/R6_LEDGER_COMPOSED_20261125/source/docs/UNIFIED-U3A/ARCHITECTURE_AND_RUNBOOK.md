# UNIFIED-U3A — first source-bound product execution checkpoint
Parent e014868ae03cf73487aba156647eeac9442422cb; CEO-0174/0179=B, D0 isolated dev only. U3 requested actual product execution; full app remains BLOCKED. No new runtime permissions, live data, main, CI, PROD or independent acceptance.
## Current sources
Core bebee3198ede68cd201cba363752a9006be35581: D1 and D2 raw reviewed PASS (13/13 original PG tests), historical 11/16; D3 RLS open. Core advanced during precommit, product/database tree pins identical to 34694a5552a91f614e4d220b364b441d0d955f36, no merge. See core docs/0227/D3_RLS_SCOPE_REVIEW.md: original five DDLs/12 tables lack RLS; separate fixture needed; do not claim RLS accepted or alter stopped D1/D2 cluster. P10J24B 6941a73e5b1b63b1ada7b912d375efb07a7599b1: 61 recovered paths, 17 selected tests historical only; no product changes. Office 089a4a256cdf0fc835035041ac519b4c15250542, A6 438985fea059f0ffafdfa16f0d090cb854b5fc36 unchanged.
## Implementation
One product repair: WorkflowDraft lacked its own shared context (ProjectStudio/CorePreview/AgentDetail already used it). Reuse StudioContextPanel bound to inspected task, not draft edges or real runtime. No canonical join. Preserve editor controls and validation; TSX syntax only. 505 product files, 504 manifest entries. No package/schema/DB change. Exact P10J24 runner and three historical files transferred outside product; 55/55 historical Git blob/size closure remotely checked (52 current +3 overlay). Original lock not repinned. New w8_unified_u3.py imports exact P24/P23 and rebinds manifest in process, retains original review/install/build/test/smoke/native gates; adds 63 selected tests and two additional auxiliary paths. Browser hook runs while original local servers active; refuses missing/duplicate invocation or invalid report and clears invalid markers. Scenario requires actual shared HTTP response, same digest on CEO/Agent/Project/Workflow/Office, clear propagation, client navigation without reload, passive floor zero roles, actual 30s expiry and no external requests. Browser script syntax only, full inherited chain/browser selectors/timing NOT_RUN. Ten runner tests fake parent only.
## Local evidence
Linux Python 3.13.5 / Node 22.16.0 / TS 5.8.3. Delta ZIP CRC/SHA256 checks 27+23. Local 37 exact product files (36 retained + one repaired) matched Git blob, size and manifest SHA256; 467 remaining not recovered in this turn. Two strict subset compiles, 63/63 reruns (U2 14 actual loopback HTTP with fixture reader, U1 5, A5R3 12, A5R2 17, A5R1 15). Ten mechanics PASS, one TSX syntax PASS, Python scripts compile. Remote 504/504 manifest paths/sizes and 17 pairs verified. Git DNS failed; full ZIP unavailable locally. Offline npm ENOTCACHED; pip no-index lacks fastapi==0.163.0. Full locked install/backend/Next/typecheck/browser/native/actual DB/PG/RLS NOT_RUN; no U3 gate promotion. Core D2 is historical separate source evidence.
## Workstation runbook
Use exact delivery commit from handover/readback, clean checkout (core.autocrlf=false), fresh source and stage outside each other; do not reuse existing core/office stages. From repo root:
```powershell
py -3 -B -m unittest discover -s tests/integration -p test_unified_u3_runner.py -v
py -3 -B tests/integration/w8_unified_u3.py audit --repo .
py -3 -B tests/integration/w8_unified_u3.py prepare --repo . --stage C:\AICOS\unified-u3a-stage
```
Stop on nonzero. Stop at REVIEW.json, inspect actual wheel/lock provenance and direct pins. No install before separate explicit local review/fingerprint; older approval invalid.
```powershell
$stage = 'C:\AICOS\unified-u3a-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_unified_u3.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_unified_u3.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_unified_u3.py smoke --stage $stage --approve $approve --chromium '<reviewed executable>' --frontend-port 17420 --backend-port 17421
```
Retain raw audit/install/full backend/Next/TS/core29 logs, reports, REVIEW/lock hashes, original DB hashes, markers and U3_BROWSER_REPORT.json + five actual captures. No fabricated markers. D3 follows core scope review with separate explicit local approval and disposable RLS fixture; do not reuse or mutate stopped D1/D2 cluster. No credentials/DSN in evidence.
## Diagnosis / rollback
MANIFEST/AUX_PIN/COLLISION: stop, inspect exact checkout and overlay; never copy historical files into product. Missing cache/wheel: use approved connected workstation; do not downgrade pins. Browser digest/TTL/route failure: preserve logs/screenshots, debug provider/selector timing without extending TTL or authority. Preserve failed stages, no forced overwrite. Roll back to e014868ae03cf73487aba156647eeac9442422cb on separate branch, no DB restore.
## Next
U3B clean full checkout and review fingerprint, then actual full build/browser, D3 separate. U3A preparation/repair only, not full U3 completion. U4 parallel isolated, U5 JOIN_HOLD, U6 MVP 0/11.