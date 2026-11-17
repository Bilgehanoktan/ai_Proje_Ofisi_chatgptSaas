# ORG-05R5R3 — isolated PostgreSQL launch and scope boundary

Parent: `80bc6f4e4d46e9341660e7e7a85ba5a917168c54` (ORG-05R5R2). No product source edits, no branch merge. R5 and R4-PG remain separate. Core D3 `f6cde1c6dece8423c1f809cee9896101f76b2150` and Unified U3A `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` reviewed read-only.

## Architecture and acceptance

New launcher orchestrates exact existing R5 bootstrap, R4 schema, R5 26-check acceptance and R5R2 offline reviewer in a unique local cluster. No new DB schema or runtime engine, no external network or provider calls. No product gate promoted. R5 manifest and all 20 pinned source files verified by SHA-256 from GitHub bytes; local R5R2 five manifest entries verified and 20 existing report tests rerun. New 20 launcher tests passed in Python 3.13 (mocked process sequencing, actual local file and validation tests). Two new modules compiled. PG server/client and psycopg not present, package DNS lookup failed. Actual PG tests 0/26; Windows execution NOT_RUN. R5 29 protocol and R3 141 behavior tests not rerun.

Core `valid_scope()` accepts only synthetic-tenant/synthetic-company/A0_SAMPLE_ONLY; both ORG fixture scopes differ. No alias conversion, no auth bypass. `TaskReference` lacks run_id; matching caller-provided references is not canonical ownership. The existing R3 Studio and Office readbacks remain synthetic. See SCOPE_BOUNDARY.json; actual IAM, task membership, API and Office integration HOLD pending a reviewed common scope profile and verified owners. No new duplicate authority.

## Run on Windows (non-administrator, explicit disposable test only)

Use an authenticated fresh clone of the R5R3 branch, with byte preservation (`git -c core.autocrlf=false clone ...`). Verify exact commit and this delta's SHA256SUMS. Use a separate reviewed Python environment with psycopg 3.3.9 and PG17 binaries; do not install packages into Core. From repository root, after reviewing R5 RUNBOOK.md and this launcher's code:

```powershell
python candidates/ORG-05R5R3/run_isolated_pg.py --candidates candidates --pg-bin 'C:\Program Files\PostgreSQL\17\bin' --stage-parent $env:LOCALAPPDATA --port 55435 --execute-disposable
```

Adjust PG bin path only to reviewed actual binaries. Password prompts are interactive: choose new disposable credentials at initdb and role setup; enter those same passwords at later prompts. Do not publish secrets or absolute personal paths. The launcher checks the exact reviewer hash, pinned parent sources, driver and binary versions before creating a directory, rejects ports 5432 and 55433, uses loopback and checks actual cluster name/version/admin/data directory before bootstrap. It creates a unique stage under the existing parent; it never reuses an existing stage. The port precheck is not a reservation. Trusted local executable and checkout custody remain prerequisites; the cluster label alone is not provenance.

## Maintenance and recovery

On source hash mismatch stop and compare original Git bytes; never regenerate pins to bypass. On missing binary or driver fix only isolated test environment. On port conflict choose a new reviewed free port. On any subprocess or report failure preserve printed stage, server log and any report. Do not automatically rerun, drop, or delete. Before manually stopping a failed stage, verify its data directory and local port against the recorded stage; use pg_ctl only on that directory. Successful report-format check stops only the new cluster, preserving files. A complete report is UNATTESTED; review raw evidence separately before PG acceptance. No automatic acceptance or product permission. Source rollback is return to R5R2 commit, not DB rollback. Design choices: default port 55435, reserved ports 5432/55433, fixed PG17/driver pin, explicit non-admin execution, fail-stop on error and successful-stage stop. No automatic install or cleanup. Next: actual isolated PG run and independent review, fix observed failures, then coordinate Core/ORG common test scope and canonical task/identity readback before API and Office acceptance.
