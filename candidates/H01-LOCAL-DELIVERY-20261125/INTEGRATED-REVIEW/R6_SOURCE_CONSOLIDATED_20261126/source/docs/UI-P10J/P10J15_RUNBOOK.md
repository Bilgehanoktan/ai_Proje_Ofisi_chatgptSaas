# P10J15 local validation runbook — disposable D0
Use authenticated exact checkout of this branch and pinned manifest e0dfff291acf9fab0893569bbc8be855a12d58d3. No live database or shared credentials. PowerShell examples from clean source root.

```powershell
py -3 -B scripts/verify_product.py --root . --manifest-blob e0dfff291acf9fab0893569bbc8be855a12d58d3
py -3 -B tests/integration/w8_p10j15.py audit --repo .
py -3 -B tests/integration/w8_p10j15.py prepare --repo . --stage C:\AICOS\p10j15-stage
```
Expected 442 source pins, 17 schema/fixture pairs. Prepare creates a NEW stage outside source and a REVIEW.json; inspect actual transitive pins, wheels, provenance and fingerprint. Never invent approval or reuse old approval.

```powershell
$stage = 'C:\AICOS\p10j15-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j15.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j15.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j15.py smoke --stage $stage --approve $approve --chromium '<reviewed browser executable path>'
```
Inspect actual totals/skips and 72 planned PNGs. Full backend discovery includes original SQL8/SQL10/SQL6/DB4 and new 0225 tests; isolate failures with stage venv and backend cwd using unittest -v test_canonical_research_0224 test_result_reference_0221 test_scheduled_admission_0220 test_shared_snapshot_db_0223 test_company_fence_binding_0219. Capture output, exits and source/lock pins. Prior core 0226 SQL6/DB4 are separate evidence. Historical locked29 gate remains separate.
PG: see docs/0215/PG_RUNBOOK.md and docs/0217/PG_RLS_ACCEPTANCE.md. Reviewed PG server + driver, two fresh distinct local disposable DBs and non-superuser/non-BYPASSRLS roles; securely supply DSNs locally; no secrets in logs. In reviewed Python environment run scripts/run_pg_acceptance_0215.py --root . --manifest-blob e0dfff291acf9fab0893569bbc8be855a12d58d3 --report ../pg-p10j15.json --execute only with required local ACK and verified clean source. A skipped case fails 13-case gate. Existing 0189 two-session historical probes do not prove current T1 RLS. Separate reviewed two-tenant FORCE RLS fixture needed. 
Copied scripts/preflight_mvp_0226.py and docs/0226/LOCAL_ACCEPTANCE_RUNBOOK.md retain original core-only manifest/count; use on 0226 checkout, not union.
Stop on HOLD. Do not mutate pins, authority or existing DBs to make tests pass. No CI/main/PROD, live model/tool/agent, cost or release.
