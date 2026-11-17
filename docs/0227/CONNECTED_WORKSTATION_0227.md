# 0227 — connected workstation execution packet (D0 only)

Use the existing CEO-0174 / CEO-0179=B scope. No CI, main merge, PROD, real data, paid/model/provider calls, real grants or external business effects. No new security acceptance. This is an operational handoff, not an executed environment. Keep the 0226 exact clean checkout, historical checkout and runtime separate. Do not send credentials or private source to third parties. Do not use a shared database.

## 1. Acquire exact source with authenticated Git on a connected workstation

PowerShell example (new directories only; Git authentication must already be configured through the user's existing authorized method). Do not put tokens in URLs or logs. Do not use the older local ZIP as the current source.

```powershell
$ErrorActionPreference = 'Stop'
$base = 'c715e1edfd1af021b4c0be0681c6958455b6a26f'
$hist = '614aa63efbd0a95d0fa5fe47390df043d773370f'
$manifest = '981a13fc226184dc3a911ae0d94e0042285ff302'
$repo = Join-Path (Get-Location) 'aicos-0226-clean'
$history = Join-Path (Get-Location) 'aicos-0207-historical'
$runtime = Join-Path (Get-Location) 'aicos-0227-runtime'
if ((Test-Path $repo) -or (Test-Path $history) -or (Test-Path $runtime)) { throw 'Use new directories' }
git -c core.autocrlf=false clone --no-checkout https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git $repo
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
git -C $repo config core.autocrlf false
if ($LASTEXITCODE -ne 0) { throw 'Git config failed' }
git -C $repo checkout --detach $base
if ($LASTEXITCODE -ne 0 -or (git -C $repo rev-parse HEAD) -ne $base) { throw 'Wrong current commit' }
git -C $repo worktree add --detach $history $hist
if ($LASTEXITCODE -ne 0 -or (git -C $history rev-parse HEAD) -ne $hist) { throw 'Wrong historical commit' }
git -C $repo worktree add --detach $runtime $base
if ($LASTEXITCODE -ne 0) { throw 'Runtime checkout failed' }
Set-Location $repo
py -3 -B scripts/verify_product.py --root . --manifest-blob $manifest
if ($LASTEXITCODE -ne 0) { throw 'Clean source mismatch' }
py -3 -B tests/integration/run_core_0207.py --source $history --report ../core-0227-source.json --check-only
if ($LASTEXITCODE -ne 0) { throw 'Historical source mismatch' }
```

Require 392/392 content SHA-256 and exact product file set locally, 55/55 exact historical files. If line endings differ, diagnose checkout attributes; do not rewrite source or manifest to make it pass. Keep clean source unchanged. The historical check-only report is not A3.

## 2. Dependency resolution and review

Use a new venv on the runtime worktree. Record OS/arch, Python, Node, npm, and installer/resolver versions. Existing direct Python pins: requirements.txt, requirements-test.txt, requirements-history-signatures.txt. Existing frontend pins and overrides: package.json. Do not change them silently. PostgreSQL server/driver and browser tooling must be explicitly versioned/reviewed for the selected target; a PostgreSQL binary or a Python package merely present on PATH is not D1. Review the actual package graph, platform wheel/optional dependency availability, hashes/integrity, licenses and provenance. FastAPI/Starlette TestClient compatibility is a verification item, not a diagnosed incompatibility.

Candidate-only Python resolver command (no installation; run from runtime backend; use the selected isolated Python):
```powershell
python -m pip install --dry-run --ignore-installed --only-binary=:all: --report ../../../python-resolution-0227.json -r requirements.txt -r requirements-test.txt -r requirements-history-signatures.txt
```
On failure retain logs, do not use a newer version or add dependencies automatically. Use a separately reviewed hash-generating resolver to produce platform-specific transitive lock(s), including any separately approved test/PG/browser dependencies, then install using pip --require-hashes from the reviewed lock. A resolver JSON is not a reviewed lock. Record exact version, source and hash of the lock generator. Require pip check and version match after installation.

Candidate-only npm resolution (runtime frontend; lockfile generation only, scripts disabled):
```powershell
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```
Review package-lock.json against package.json, resolved hosts, integrity, platform optional packages and overrides. After review use npm ci, typecheck and build; review lifecycle scripts before allowing them. Do not copy node_modules into clean source. Commit lock candidates only as a separate controlled source revision with updated manifest and reviewed evidence. No lock was generated in this session.

## 3. Existing tests, not new prototypes

Using the runtime venv and clean/historical pinned sources, run the original historical runner (without diagnostic-unpinned) from clean root:
```powershell
python -B tests/integration/run_core_0207.py --source $history --report ../core-0227-locked.json
```
A3 additionally requires reviewed transitive locks; runner direct-pin match alone is insufficient.

From runtime backend with its reviewed environment:
```powershell
$env:PYTHONPATH = '.;tests'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m unittest -v test_company_fence_binding_0219 test_result_reference_0221 test_canonical_research_0224
```
Require 6+10+8=24 original tests, no failure/error/skip, preserve logs. These are D0 SQLite integration checks, not PG. Then run full approved backend regression and import/startup using existing app/main.py. Record exact suite collection and actual counts; no unexplained deselection. There is no backend pyproject/build package at this source; do not invent a wheel build result. Any required packaging is a separate implementation item.

## 4. PostgreSQL and browser

Follow docs/0226/LOCAL_ACCEPTANCE_RUNBOOK.md and docs/0215/PG_RUNBOOK.md. D1 requires actual disposable PG/driver connection; D2 run existing scripts/run_pg_acceptance_0215.py against the clean source with its current manifest and distinct loopback DSNs, 13/13 no skips. D3 requires separately observed non-owner FORCE RLS, cross-tenant/forged-context denials, genuine lock contention/rollback on current mapping; historical probe alone is insufficient. Use no production/shared database or credentials in evidence. E3 requires reviewed npm lock, npm ci, typecheck and build. E4 requires built application in real browser with actual historical D0 DB/API, shared CEO/Office/Studio scopes and mismatch/resync behavior, no fixture-only result. Record build/test logs, source/lock digests and gate-specific evidence. B3 stays HOLD.

## 5. Failure/rollback

Stop on a source mismatch or dependency error. Retain clean source and evidence; do not relax tests or alter existing pins just to pass. Remove only explicitly identified disposable worktrees/databases after ownership verification, not shared data. No automatic deployment or promotion. Revert this documentation-only branch commit if needed; product manifest and historic lock remain unchanged.


## 0227-A3 checkpoint — avoid duplicated work
Historical A3 accepted from A0F raw-reviewed exact historical Core29 evidence; see ../../tests/evidence/A3_EVIDENCE_TRANSFER_0227.json. Do not rerun merely to increase counts. All four direct spec blobs match A0C and P10J15, but source-bound A0C approval/markers cannot be reused as E1 for current product. For a targeted 24-case D0 diagnostic, use the existing reviewed Windows A0C interpreter on a new pinned core checkout after checking the original A0C stage with its original wrapper and review fingerprint, exact 392 source bytes, direct pins and pip check. Do not alter A0C source/venv, install additional packages in it, use real DBs or carry over its marker files. Use fresh TEMP and no PG/provider credentials. Capture exact source, lock and test logs; 24 tests are not full E2. The P10J15 workstream already contains exact target test blobs; coordinate a single run where applicable, but keep source-specific evidence and no branch merge. For full current E1/build acceptance use a separate reviewed runtime stage and source-bound REVIEW. Existing stage command and path can be reused only if present and revalidated on the workstation.


## 0227-E1 — retained Windows A0C lock recovery (preferred when original stage exists)

Use the versioned scripts/run_e1_0227.py from the new 0227 checkpoint, outside the clean checkout. The clean source is the detached commit 52219c7a222bae41735c9a9b9f7f7082462982b4, product manifest unchanged. Verify actual A0C stage path (example below; replace if different). Requires Windows Python 3.14.3, Node v24.14.0 and npm 11.9.0. Do not create stage in the source or A0C stage; do not overwrite prior directories.

```powershell
$root = 'C:\AIOS\core-0227-clean'
$old = 'C:\AIOS\premium-a0d\stage'
$stage = 'C:\AIOS\core-0227-e1'
$runner = 'C:\AIOS\run_e1_0227.py' # saved from the versioned runner
if (Test-Path $root) { throw 'Use a new clean checkout directory' }
git -c core.autocrlf=false clone --no-checkout https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git $root
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
git -C $root config core.autocrlf false
if ($LASTEXITCODE -ne 0) { throw 'Git config failed' }
git -C $root checkout --detach 52219c7a222bae41735c9a9b9f7f7082462982b4
if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
py -3.14 -B $runner prepare --source $root --a0-stage $old --stage $stage
if ($LASTEXITCODE -ne 0) { throw 'Prepare HOLD' }
Get-Content "$stage\locks\REVIEW_0227.json"
Get-FileHash "$stage\locks\REVIEW_0227.json" -Algorithm SHA256

```
Inspect actual review and send its contents/hash for verification. Only after explicit local approval, pass the NEW fingerprint (not A0 review hash) to execute.

```powershell
$approve = '<new reviewed SHA256>'
py -3.14 -B $runner execute --source $root --a0-stage $old --stage $stage --approve $approve
if ($LASTEXITCODE -ne 0) { throw 'Execution HOLD; preserve logs' }

```
Return the evidence directory, REVIEW_0227.json, python.lock and package-lock.json; retain the old stage and new stage. No secrets, live DB, old venv copying or dependency version substitution. If old wheels absent, revert to separately reviewed resolution workflow. E1 cannot be promoted until real new review and install evidence inspected; original24 only D0 SQLite, no E2 full build.


## 0227-E1 final raw review — PASS
User-uploaded raw ZIP 14/14 CRC, 9/9 report log hashes, 28 Python wheel/installed versions and 61 npm lock entries, 30 installed versions, 24 original test names match source and all pass. Two extraneous npm packages are exact optional lock entries; E3 recheck. No raw wheel binaries or independent replay. E1 closed, 9/16 (56.25%); product and DB source unchanged; prior 307 count separate. D1/D2 next; D3/E2/E3/E4/B3 open. Evidence: tests/evidence/E1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D1 — candidate downloads and connection runner
Server ZIP checksum matches EDB (user transcript); Psycopg/psycopg-binary/tzdata downloads successful. Public PyPI hashes verified for pure Psycopg and tzdata; local JSON API exact check required for binary. New pinned scripts/run_d1_0227.py uses reviewed E1 wheelhouse read-only, new 31-package lock, disposable loopback-only SCRAM cluster, two non-superuser/non-BYPASSRLS DBs, write/read/rollback and graceful stop. Linux syntax/fixture checks only; no Windows execution or new gate. 9/16 unchanged; PG13/RLS pending. Evidence: tests/evidence/D1_WINDOWS_WHEELS_READY_0227.json.


## 0227 D1 initdb HOLD
User transcript confirms all 3 PyPI checks and reaches postgres 17.12/initdb after 31-pin installation sequence. Password mismatch aborts initdb; rerun intentionally refused by fresh-stage guard. Preserve failed stage; copy only ZIP and wheels to new sibling stage and repeat isolated D1. No connection or PG13/RLS test; 9/16 unchanged. tests/evidence/D1_WINDOWS_INITDB_HOLD_0227.json


## 0227-D1 retry1 connection HOLD
User reports initdb and PostgreSQL start/stop successful, child OperationalError masked by runner; exact failing statement unknown. No D1 acceptance. Preserve retry1 and diagnose with interactive read-only psql connection and role/database existence checks, then stop own cluster. No password or private log transfer; no reinstallation or grants. 9/16. Evidence: tests/evidence/D1_WINDOWS_RETRY1_CONNECTION_HOLD_0227.json


## 0227-D1 authentication diagnosis and candidate fix
User psql diagnostic starts server, reaches loopback 55432, FATAL password authentication failed (exit 2), stops successfully. Exact mismatch cause unknown. New scripts/run_d1_0227_authfix.py generates ephemeral ASCII admin, restricts and verifies temporary pwfile ACL before writing, removes file in finally, sends same credentials to child via stdin; SCRAM preserved; test password user-held. Compile and four synthetic controls PASS; Windows not run. Retry2 fresh input-only copy; old stages preserved. 9/16 unchanged. tests/evidence/D1_WINDOWS_AUTH_HOLD_AUTHFIX_0227.json


## 0227-D1 retry2 connection PASS — raw review pending
User transcript: PG17.12, Psycopg3.3.9 binary, libpq180004, SCRAM loopback 55432, two separate DBs with non-superuser/non-BYPASSRLS test role; both write/read/rollback PASS; source before/after match, server stopped. Existing input-directory/copy errors preceded successful runner preflight; retain anomaly and do not rerun install. Raw evidence pending; 9/16 unchanged; PG13 and RLS NOT_RUN. tests/evidence/D1_WINDOWS_CONNECTION_TRANSCRIPT_0227.json


## 0227-D1 final raw review — PASS
Raw ZIP 8/8 CRC, 5/5 log/report hashes, 31/31 installed pins, original 28 E1 lock lines exact from reopened E1 archive, two PostgreSQL DB probes PASS; SCRAM loopback and stopped state evidenced. D1 accepted, 10/16 (62.5%). No independent replay, raw binaries absent, PG13/RLS/build open. Source unchanged. Next: docs/0227/D2_PG13_RUNBOOK.md. Evidence: tests/evidence/D1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D2 — original PG13 execution PASS, raw report pending
Uploaded Windows transcript parsed: 0194 5/5, 0196L 5/5, 0200S 3/3, all failure/error/skip counters zero; exact runner source and 13 source test names reviewed; source/DDL verified; exit 0 and server stopped. Raw D2_PG13_RESULT.json pending. Expected report hash reconstructed, not measured on original. 10/16 unchanged pending review; D3/RLS/B3 open. tests/evidence/D2_WINDOWS_PG13_TRANSCRIPT_0227.json


## 0227-D2 final raw review — PASS
Original Windows JSON: 937 bytes, SHA256 79085656ad4d782a012642518d9d8724514976082af0c5734c5d04dcfb82cf05, exact CRLF serialization and prior transcript match. 13/13 PG cases, source/DDL verified; 11/16 (68.75%). D3 separate RLS/non-owner contention, E2/E3/E4 and B3 open; source unchanged. Evidence: tests/evidence/D2_RAW_EVIDENCE_REVIEW_0227.json; next: docs/0227/D3_RLS_SCOPE_REVIEW.md.
