# MI-01 / W8 — PR37 exact-source Windows local D0 runbook

2026-11-21. Status: REVIEW-ONLY, NOT W8 C07 acceptance. The owner/dependency reviewer must assess this candidate and its source/lock provenance. This is a narrowly scoped optional local test only; not independent C05, fresh C07 or Chromium C08.

## Provenance and stage
- Branch: `review/mi01-w8-core0207-c50-r1-contract-20261121` (base PR36 exact SHA `683a26171ac54544260456ce84e19c38614aa5e2`).
- Exact GitHub runner blob `cc467843bf11857fbbd9df19e513626fb7de85bf` and contract blob `537e0c35592ca7366a52ab87c08db7e419f18b71`.
- Exact chat-delivered ZIP: `AIOS_CORE0207_C50_R1_PR37_EXACT_SOURCE_20261121.zip`, size 4506 bytes, SHA256 `48f194ab76182c11cfd9bed5864b3992236702b790c01ab2341c04166b675aad`; ZIP content Git blob pins 2/2 verified.
- Exact two ZIP members SHA256: runner `0902f736487273a7bc873934d0eef3ca0c87fd20d57f34698572e2fe329406cc`; contract `3a3b6a2cbb6f9d5762950d65873fd56533d0e377e17864f97bcfe5c1ed079b8b`.
- Original approved stage and venv: `E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\stage`. Original source-runner root: sibling `source\tests\integration`; 55 original sources from earlier R2 `E:\AIOS\W8\PR36_DIAGNOSTIC_ONLY_20261121_134455\historical_source_55`.
- Do not install, downgrade or mutate PR36 C06 stage. Do not run unsigned PowerShell .ps1 or change ExecutionPolicy. This inline PowerShell 5.1 block uses ZIP extraction to a distinct new `E:` directory and the original immutable venv.

## Interactive PowerShell 5.1 command

~~~powershell
& {
    $ErrorActionPreference = 'Stop'
    $zip = Join-Path $env:USERPROFILE 'Downloads\AIOS_CORE0207_C50_R1_PR37_EXACT_SOURCE_20261121.zip'
    $expectedZip = '48f194ab76182c11cfd9bed5864b3992236702b790c01ab2341c04166b675aad'
    if (!(Test-Path -LiteralPath $zip -PathType Leaf)) { throw 'PR37_ZIP_MISSING' }
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedZip) { throw 'PR37_ZIP_SHA256_HOLD' }
    $parent = 'E:\AIOS\W8'
    $work = Join-Path $parent ('PR37_C50_R1_D0_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    if (Test-Path -LiteralPath $work) { throw 'PR37_OUTPUT_ALREADY_EXISTS_HOLD' }
    New-Item -ItemType Directory -Path $work -ErrorAction Stop | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $work -ErrorAction Stop
    $contract = Join-Path $work 'CONTRACT.json'
    $runner = Join-Path $work 'run_core0207_c50_r1.py'
    foreach ($p in @($contract, $runner)) {
        if (!(Test-Path -LiteralPath $p -PathType Leaf)) { throw "PR37_BUNDLE_MEMBER_MISSING: $p" }
    }
    $contractSha = (Get-FileHash -LiteralPath $contract -Algorithm SHA256).Hash.ToLowerInvariant()
    $runnerSha = (Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($contractSha -ne '3a3b6a2cbb6f9d5762950d65873fd56533d0e377e17864f97bcfe5c1ed079b8b') { throw 'PR37_CONTRACT_SHA256_HOLD' }
    if ($runnerSha -ne '0902f736487273a7bc873934d0eef3ca0c87fd20d57f34698572e2fe329406cc') { throw 'PR37_RUNNER_SHA256_HOLD' }
    $stage = 'E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\stage'
    $runnerRoot = 'E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\source\tests\integration'
    $history = 'E:\AIOS\W8\PR36_DIAGNOSTIC_ONLY_20261121_134455\historical_source_55'
    $python = Join-Path $stage '.venv\Scripts\python.exe'
    $required = @($python, $runnerRoot, $history,
                  (Join-Path $runnerRoot 'run_core_0207.py'),
                  (Join-Path $runnerRoot 'run_lifecycle_p05.py'),
                  (Join-Path $runnerRoot 'core_0207_source_lock.json'),
                  (Join-Path $runnerRoot 'w8_p10j24.py'))
    foreach ($p in $required) { if (!(Test-Path -LiteralPath $p)) { throw "PR37_PREREQUISITE_MISSING_HOLD: $p" } }
    $report = Join-Path $work 'CORE0207_C50_R1_REVIEW_ONLY.json'
    & $python -B $runner --stage $stage --runner-root $runnerRoot --source $history --report $report
    $exit = $LASTEXITCODE
    Write-Output "NEW_CANDIDATE_EXIT_CODE: $exit"
    if (Test-Path -LiteralPath $report -PathType Leaf) {
        Get-Content -LiteralPath $report -Raw
        Write-Output ('REPORT_SHA256: ' + (Get-FileHash -LiteralPath $report -Algorithm SHA256).Hash)
    }
    Write-Output "PR37_REVIEW_ONLY_DIR: $work"
    if ($exit -ne 0) { throw 'PR37_CORE29_LOCAL_D0_HOLD_INSPECT_REPORT' }
}
~~~

## Interpretation and next gates
1. A preflight `PR37_PREREQUISITE_MISSING_HOLD` is an input-location failure, **not** a failed Core29 test. Preserve all files; compare verified original `stage` and `source` path roots before deciding on an amended runner.
2. `CORE0207_C50_R1_CANDIDATE: PASS passed=29` from the **new versioned candidate** is a new LOCAL D0 review result, not the old historical C07 suite. The runner requires PR36 C06 exact reviewer SHA, manifest, version 50.0.2 and historical 55-file/29-case scope; it writes a JSON outside the stage.
3. On HOLD or Python error, inspect exact new JSON and terminal output. Do not edit stage files, historic lock/runner, allow implicit downgrade, bypass source validation or count partial checks as acceptance.
4. Compare case IDs, direct/transitive lock and Windows binary/OpenSSL provenance; obtain actual owner and independent security decisions. Only then design/review versioned W8 adapter, run a fresh full C07 and Next.js build, actual Chromium C08 and independently scoped C05.
5. W8 acceptance remains 3/8 (37.5%) before/after, delta 0; weighted development HESAPLANAMADI. No PR merge, CI, product-dev/main mutation, provider or PROD.

## Recovery / rollback
Output is a uniquely named new `E:\AIOS\W8\PR37_C50_R1_D0_<timestamp>` folder. Inspect/archive it; there is no automatic cleanup. Rollback is to close PR37 or normally revert new files and archive that output. Preserve PR34/35/36 sources, old dependency evidence and original Windows stages. This document and review-only runner do not grant C05/C07 acceptance.
