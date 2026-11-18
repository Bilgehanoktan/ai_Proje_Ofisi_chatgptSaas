# R8 closed Studio — isolated product source integration
Parent 8a3b05aadd32b214f3f8988fc9c793f853fbe3d0; evidence dd734bf31977c84fee85ab6d23d11cd9804804a0. CEO-0174/0179=B. No actual IAM, no backend route, no grant, no production, CI or merge. Eight exact R6/R7 product paths (3 modified, 5 added), 509 manifest entries. Default frontend GET returns 503 HOLD; do not configure a provider. Prior R7 31 tests transferred unchanged; not rerun yet.
## Workstation
Use clean checkout of this integration commit, core.autocrlf=false. No install or dependency changes for the selected tests. Use existing reviewed Node and TypeScript compiler, record versions; if missing stop, do not use npx or regenerate a lock. Run from root:
```powershell
$manifest = (git rev-parse HEAD:product/SOURCE_MANIFEST.json).Trim()
py -3 -B scripts/verify_product.py --root . --manifest-blob $manifest
node --version
tsc --version
$front = (Resolve-Path 'product/ai-company-os-frontend').Path
$work = (Resolve-Path 'tests/integration/org-07c-r8').Path
tsc --strict --target es2022 --module commonjs --lib es2022,dom --rootDir $front --outDir "$work/build" "$work/tests/process.d.ts" "$front/app/api/demo/organization/route.ts" "$front/features/data/projectionRead.ts"
node --test "$work/tests/owner_binding_product.test.cjs" "$work/tests/route.test.cjs" "$work/tests/closed_reader.test.cjs"
```
Stop after any nonzero exit. Expected 31 PASS. This is direct execution of compiled product modules with injected fetch, not Next/browser or real auth. No backend server/PG needed. Save stdout/stderr, versions, exit codes, commit and manifest verification. Full Next build remains Unified-owned and blocked on reviewed exact npm lock; no npm install. No actual provider/route registration acceptance. Rollback: use parent commit in separate checkout, preserve test logs, no database restore.
