# ORG-05R5R2-EXEC — Windows execution
Use the exact new child commit archive, not this delta alone. Extract into a new checkout with original LF bytes preserved. The launcher requires the sibling ORG-05R3/R4/R5/R5R2 directories and exact pins. Use an existing independently reviewed local PostgreSQL 17 installation, a separate Python environment with reviewed psycopg and psycopg-binary 3.3.9, and a nonadministrator OS account. No downloads or installation performed by this script.

From repository root in PowerShell, adjust `$Pg` to the reviewed installed binaries. `$Stage` and `$Report` must not exist; their parent must exist. Do not reuse previous stages or D3/D4 ports.

```powershell
$Pg = 'C:\Program Files\PostgreSQL\17\bin'
$Stage = Join-Path $env:LOCALAPPDATA 'aicos_org_r5_disposable_01'
$Report = Join-Path $env:LOCALAPPDATA 'ORG_R5_PG_RESULT_01.json'
python candidates/ORG-05R5R2-EXEC/launch_disposable.py --pg-bin $Pg --stage $Stage --report $Report
```
Only after preflight PASS, reviewed binary/driver hashes and confirmation of the fresh isolated stage:

```powershell
python candidates/ORG-05R5R2-EXEC/launch_disposable.py --pg-bin $Pg --stage $Stage --report $Report --execute-disposable
```
Interactive prompts request admin password during initdb and psql, and four fixture role passwords during bootstrap and runner. Enter matching passwords; do not put passwords in commands. The script runs existing 26 tests on port 55435, produces the named report and invokes existing R5R2 review. A complete report is UNATTESTED; send the report plus sanitized local bootstrap/start/stop and execution evidence for review. Do not send credentials, private paths or raw server.log. On failure preserve the new stage and logs; no automatic rerun or deletion. A manual stop must target only the verified new stage:

```powershell
& "$Pg\pg_ctl.exe" -D $Stage stop -m fast
```

Do not run the stop command if the stage identity is uncertain. Real PostgreSQL execution and acceptance remain NOT_RUN/HOLD until evidence exists.
