# MI-01-R1 — U3B exact-source preflight
Base 8a3b05aadd32b214f3f8988fc9c793f853fbe3d0; product unchanged. No newer U3B branch found in 257 branch snapshot. Prior W8/U3A results remain historical. 505 remote source pins, 504 manifest entries, 17 pairs, 55 historical paths, 23 runner files, 26 selected final auxiliary pins match (static only). Four direct dependency files locally SHA256 + Git blob exact. Git DNS fails; offline npm/pip cache misses. No full local checkout/build or reviewed transitive lock. 
## Connected Windows workstation
Use authenticated Git if needed, never log secrets. Fresh source/stage; no changes to older checkouts. Exact SHA, local core.autocrlf=false. Use original U3A runner audit then prepare; stop at REVIEW.json. Review npm lock, python.lock, wheel hashes and provenance before install; older approval not reusable. No dependency downgrades, no CI, main, real grants, provider, spend, PROD or IV.
```powershell
& {
    $ErrorActionPreference = 'Stop'
    $sha = '8a3b05aadd32b214f3f8988fc9c793f853fbe3d0'
    $root = Join-Path 'C:\AIOS' ('MI01_U3B_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    $stage = "$root-stage"
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    git -C $root init
    if ($LASTEXITCODE -ne 0) { throw 'GIT_INIT_HOLD' }
    git -C $root config core.autocrlf false
    if ($LASTEXITCODE -ne 0) { throw 'GIT_CONFIG_HOLD' }
    git -C $root remote add origin 'https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git'
    if ($LASTEXITCODE -ne 0) { throw 'GIT_REMOTE_HOLD' }
    git -C $root fetch --depth=1 origin $sha
    if ($LASTEXITCODE -ne 0) { throw 'GIT_FETCH_HOLD' }
    git -C $root checkout --detach $sha
    if ($LASTEXITCODE -ne 0) { throw 'GIT_CHECKOUT_HOLD' }
    $actual = git -C $root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -ne $sha) { throw 'COMMIT_HOLD' }
    Push-Location $root
    try {
        py -3 -B tests/integration/w8_unified_u3.py audit --repo .
        if ($LASTEXITCODE -ne 0) { throw 'AUDIT_HOLD' }
        py -3 -B tests/integration/w8_unified_u3.py prepare --repo . --stage $stage
        if ($LASTEXITCODE -ne 0) { throw 'PREPARE_HOLD' }
        Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $stage 'locks\REVIEW.json')
        Write-Host "STAGE=$stage"
        Write-Host 'REVIEW_REQUIRED; INSTALL_NOT_RUN'
    } finally { Pop-Location }
}
```
## Evidence and recovery
Keep REVIEW.json, npm package-lock.json, python.lock and raw audit/prepare logs. No passwords/DSN. Failed stage is retained; retry fresh. After review use original U3A install/test/smoke. No accepted full build, browser or native test this round. Core PG/RLS and IAM/ORG/T1 owners stay independent. Product-dev unchanged; governance rollback via reviewed revert; no force or history rewrite.
