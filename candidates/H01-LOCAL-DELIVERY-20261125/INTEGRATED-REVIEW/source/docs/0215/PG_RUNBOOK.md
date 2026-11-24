# 0215 — isolated PostgreSQL acceptance runner

Do NOT use a production or shared DB. Obtain authenticated exact checkout (GitHub commit and product manifest blob), review PostgreSQL version/psycopg and direct/transitive dependency lock independently. Existing original suite guards require a disposable local DB with a non-superuser, non-BYPASSRLS role permitted to create schema. Prepare two **new** disposable loopback databases with names aicos_d0_0194_<suffix> and aicos_d0_0196l_<suffix> respectively. No existing t1_candidate schema. Configure local roles explicitly; do not put credentials in repo or report. This runner does not install packages, create roles/databases or change permissions.

PowerShell from clean repo root, with reviewed Python environment and DSNs supplied securely in process environment:
```powershell
py -3 scripts/verify_product.py --root . --manifest-blob 9dc7c7db0ff496d546a9cbf0a76a1aa63aeaf2bc
# Set AICOS_PG_0194_DSN and AICOS_PG_0196L_DSN securely: explicit host=127.0.0.1, dbname, user, port; optional password.
$env:AICOS_PG_RUN_ACK = '0215_DISPOSABLE_LOCAL_ONLY'
py -3 scripts/run_pg_acceptance_0215.py --root . --manifest-blob 9dc7c7db0ff496d546a9cbf0a76a1aa63aeaf2bc --report ../pg-0215.json --execute
Remove-Item Env:AICOS_PG_RUN_ACK
Remove-Item Env:AICOS_PG_0194_DSN,Env:AICOS_PG_0196L_DSN -ErrorAction SilentlyContinue
```
Expected exact counts: 0194 5, 0196L 5, 0200S 3. A skip, unexpected count, unexpected success, timeout or failed result is HOLD. Reports have no raw error/DSN. On failure diagnose on disposable local environment and preserve evidence; no automatic retry, no automatic schema drop. 13/13 would only be D0 PG diagnostic; separate non-owner, cross-tenant FORCE RLS, forged tenant-context, actual lock-order/concurrency, independent security and pinned build acceptance remain. Current local execution did not reach PostgreSQL.
