# ORG-05R5 — reviewed disposable PostgreSQL 17 runbook (NOT_RUN)

This is a source candidate. Do not execute on Core D1/D2/D3, U3, any existing cluster, production, or customer data. No passwords, connection strings, actual principal or provider calls are stored. Existing R4 schema is reused unchanged. No automatic cleanup or destructive rollback.

## Source preflight
Checkout the exact ORG-05R5 commit/archive. Place this delta at `candidates/ORG-05R5` beside the original `ORG-05R3` and `ORG-05R4` directories from parent `49499807a9a0c37d34375a17d1f5fbacc31ac4b3`. Compare `SHA256SUMS` before running; runner also checks 7 R3 dependency files and R4 SQL against pinned SHA-256. Use reviewed PostgreSQL 17 binaries and psycopg 3.3.9 binary driver (same version as D3; not installed here). Use a separate venv, approved wheel/hash and no existing application env vars. `python -m unittest -v test_pg_protocol` is local fake-DB protocol test only.

## Fresh local Windows stage (manual, explicit opt-in)
The following is a preparation example, not an executed transcript. Adjust executable paths after confirming installed PG17. Use a new empty directory, unique free port (example 55435; check availability) and a distinct administrator. Never reuse the D3 port 55433 or data directory. Run under a non-administrator OS account. Keep passwords out of command arguments and logs. Verify SCRAM pg_hba and loopback-only listen.

```powershell
$Pg = 'C:\Program Files\PostgreSQL\17\bin' # verify actual path
$Stage = Join-Path $env:LOCALAPPDATA 'aicos_org_r5_disposable_new'
$Port = 55435
if (Test-Path $Stage) { throw 'Use a new directory, never reuse a stage' }
if (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue) { throw 'Port already in use' }
& "$Pg\initdb.exe" -D $Stage --username=org_r5_admin --auth=scram-sha-256 --pwprompt
if ($LASTEXITCODE -ne 0) { throw 'initdb HOLD' }
& "$Pg\pg_ctl.exe" -D $Stage -l (Join-Path $Stage 'server.log') -o "-p $Port -h 127.0.0.1 -c cluster_name=aicos_org_r5_disposable" start
if ($LASTEXITCODE -ne 0) { throw 'pg_ctl HOLD' }
& "$Pg\psql.exe" -X -h 127.0.0.1 -p $Port -U org_r5_admin -d postgres -c "SELECT current_setting('cluster_name'),current_setting('data_directory'),current_setting('server_version_num');"
```

Review the printed `data_directory` locally against `$Stage` (do not upload a personal absolute path), cluster name, PG major and authenticated role before proceeding. From `candidates/ORG-05R5`:

```powershell
& "$Pg\psql.exe" -X -v ON_ERROR_STOP=1 -h 127.0.0.1 -p $Port -U org_r5_admin -d postgres -f .\bootstrap_roles.sql
if ($LASTEXITCODE -ne 0) { throw 'Role setup HOLD; do not retry this stage' }
& "$Pg\psql.exe" -X -v ON_ERROR_STOP=1 -h 127.0.0.1 -p $Port -U org_r5_admin -d aicos_org_r4_disposable -f ..\ORG-05R4\PG_SCHEMA_R4.sql
if ($LASTEXITCODE -ne 0) { throw 'Schema HOLD; do not retry this stage' }
# In a separate reviewed Python environment with psycopg 3.3.9:
python .\run_pg_acceptance.py --execute-disposable --port $Port --report .\ORG_R5_PG_RESULT.json
```

Runner prompts for four transient role passwords. It checks fresh empty tables (both scopes), policy inventory, local cluster/PG major, role flags, RLS FORCE, and role membership. It performs actual SQL via non-owner sessions and stops on first failure. It emits a fresh JSON report, not passwords or personal paths. No report is created when source verification or driver import fails before test start. No automatic reruns. On commit UNKNOWN, preserve the database and evidence; reconcile expected head, prior history pin, proposal identity, notice row and counts through a separately reviewed read before another write. Do not delete or reuse the stage on a failure. Stop only the new cluster after evidence collection: `& "$Pg\pg_ctl.exe" -D $Stage stop -m fast`. Never point this command at Core.

## Evidence boundary
The 26 named PG checks are test candidates until the actual JSON report is reviewed. Role creation and exact R4 SQL installation must be reviewed independently. Cluster label, loopback and role guards reduce accidental misuse; they are not production identity or proof of server custody. No independent IAM, dynamic RLS, live API, canonical T1, Event Store, production migration, or live Office Engine acceptance is implied. Tests preserve partial results if an assertion fails; bootstrap and source checks can fail before the report begins.
