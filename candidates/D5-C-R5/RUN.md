# Run D5-C-R5 on Windows (fresh isolated D0 only)
1. Download this pinned branch archive, extract it into a new source directory. Open PowerShell in candidates/D5-C-R5. All three source inputs are included and pinned.
2. Locate the previously reviewed D1 input folder containing postgresql-17.12.zip and wheels/ with psycopg-3.3.9-py3-none-any.whl, psycopg_binary-3.3.9-cp314-cp314-win_amd64.whl, tzdata-2026.6-py2.py3-none-any.whl. Only read those original archives. No substitute or new download.
3. Run:
```powershell
$inputs = Read-Host "D1 archive folder (contains postgresql-17.12.zip and wheels)"
$stage = Join-Path $env:USERPROFILE ("AIOS_D5C_R5_" + (Get-Date -Format yyyyMMdd_HHmmss))
py -3.14 -B .\run_windows.py --inputs "$inputs" --stage "$stage" --port 55437
```
Preflight is read-only, no server or install. It requires exact Python 3.14.3, 3 source pins, server + 3 wheel hashes, fresh path and free loopback port. Do not continue if it fails. 
4. Only if the operator confirms 55437 is not allocated elsewhere and authorizes this isolated synthetic execution, use the same variables:
```powershell
py -3.14 -B .\run_windows.py --inputs "$inputs" --stage "$stage" --port 55437 --execute
```
Type EVET at allocation prompt. A fresh offline venv, fresh cluster and generated ephemeral credentials are created. No existing services/DBs modified. Output may be HOLD on timing, runtime or other failure. No automatic retry. Check FINAL.json and stopped status before proceeding.
5. Return only FINAL.json, profile.json, pg_evidence/report.json if present. Do not share server-private.log, private logs, credentials, data directory, or venv. No user data is needed. If final says server_stopped=false or file absent after a failed start, stop further tasks and inspect only the exact stage; do not kill arbitrary processes. A success is diagnostic pending review, not product acceptance.
