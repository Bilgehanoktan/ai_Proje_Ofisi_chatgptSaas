# AI Company OS — MI-COMMON-09 local-only Python 3.13 Windows wheel staging.
# NO global package installation, NO source mutation, NO CI/main/production.
# Source: user's immutable MI05 verified git tree and MI08 reference runtime.
& {
    $ErrorActionPreference = 'Stop'

    $base = 'C:\AIOS\MI05_20261120_001126'
    $verified = Join-Path $base 'verified_manual'
    $runtime = Join-Path $base 'P0_ENV_3135_3461_20261120_004854'
    $runner = Join-Path $verified 'pinned_regression_stage\model\docs\master-integration\MI-07-08-JOINT-TRANSFER\run_combined.py'
    $transferPath = Join-Path $verified 'TRANSFER_REPORT.json'
    $environmentPath = Join-Path $runtime 'ENVIRONMENT_PRECHECK.json'

    foreach ($path in @($runner, $transferPath, $environmentPath)) {
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "REQUIRED_FILE_MISSING: $path"
        }
    }

    $transfer = Get-Content -LiteralPath $transferPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $environment = Get-Content -LiteralPath $environmentPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($transfer.status -ne 'SOURCE_RECOVERED_TESTS_NOT_RUN' -or
        $transfer.git_tree -ne '187f652f1b1ff8604981833f634c4531a33f8a47' -or
        [int]$transfer.checkout_files_verified -ne 1953 -or
        [int]$transfer.model_rows -ne 114 -or
        [int]$transfer.core_rows -ne 55) {
        throw 'SOURCE_PIN_HOLD'
    }
    if ($environment.status -ne 'ISOLATED_PYTHON_SQLITE_READY_CRYPTO_NOT_INSTALLED' -or
        $environment.python -ne '3.13.5' -or
        $environment.sqlite -ne '3.46.1' -or
        $environment.cryptography -ne 'NOT_INSTALLED' -or
        $environment.python_archive_sha256 -ne '7D2650FD9D1B9D002D4A315D5F354247FD6A44F30517C7EF577B08F57A0FB6D9' -or
        $environment.sqlite_archive_sha256 -ne '300CB2918946F42A1A2F7F31A8DD89EDC202570E4E49D21E13D33ECDF80A6B67') {
        throw 'REFERENCE_ENVIRONMENT_LOCK_HOLD'
    }

    $sourcePy = Join-Path $runtime 'python'
    $oldPython = Join-Path $sourcePy 'python.exe'
    if (!(Test-Path -LiteralPath $oldPython)) { throw 'REFERENCE_PYTHON_NOT_FOUND' }
    $oldVersion = @(& $oldPython -I -B -c 'import sys,sqlite3;print(sys.version.split()[0]);print(sqlite3.sqlite_version)')
    if ($LASTEXITCODE -ne 0 -or $oldVersion.Count -ne 2 -or
        $oldVersion[0] -ne '3.13.5' -or $oldVersion[1] -ne '3.46.1') {
        throw 'REFERENCE_RUNTIME_CHANGED_HOLD'
    }
    $pipStatus = & py -3 -m pip --version
    if ($LASTEXITCODE -ne 0) { throw 'HOST_PIP_NOT_AVAILABLE_HOLD' }
    Write-Host "Wheel indirme araci: $pipStatus" -ForegroundColor Cyan

    Write-Host 'Yalnizca yeni bir izole test klasorune uc sabit wheel kurulacak.'
    Write-Host 'cryptography 46.0.4, cffi 2.0.0, pycparser 2.23'
    Write-Host 'Sistem Python/SQLite ve dogrulanmis urun dosyalari degismeyecek.'
    $approved = Read-Host 'Izole paket indirme ve 344 test kosumunu onayliyorsan EVET yaz'
    if ($approved -cne 'EVET') {
        Write-Host 'Kurulum ve test baslatilmadi.'
        return
    }

    $stage = Join-Path $base ('P0_MODEL_344_PINNED_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    $wheels = Join-Path $stage 'wheels'
    $privatePythonDir = Join-Path $stage 'python'
    $targetPackages = Join-Path $privatePythonDir '_modeldeps'
    New-Item -ItemType Directory -Path $wheels | Out-Null
    $summaryPath = Join-Path $stage 'MODEL_344_RESULT.json'

    $summary = [ordered]@{
        revision = 'MI-COMMON-09-PINNED-WHEELS'
        status = 'HOLD'
        source_git_tree = $transfer.git_tree
        original_source_pins = '114/114'
        reference_python = '3.13.5'
        reference_sqlite = '3.46.1'
        cryptography = '46.0.4'
        core_29 = 'NOT_RUN'
        full_w8_build = 'NOT_RUN'
        browser = 'NOT_RUN'
        protected_commit = 'HOLD'
        independent_acceptance = 'HOLD'
    }
    try {
        $pins = [ordered]@{
            cryptography = '46.0.4'
            cffi = '2.0.0'
            pycparser = '2.23'
        }
        Write-Host '=== PYTHON 3.13 WIN_X64 WHEEL INDIRME ===' -ForegroundColor Cyan
        # Host pip is only the wheel downloader/installer into the new --target.
        # Never perform a global pip install or run pip from the embedded Python.
        & py -3 -m pip --isolated download `
            --disable-pip-version-check --no-input --no-deps `
            --index-url 'https://pypi.org/simple' --only-binary=:all: `
            --platform win_amd64 --python-version 3.13 --implementation cp `
            --abi cp313 --abi abi3 --abi none `
            --dest $wheels `
            'cryptography==46.0.4' 'cffi==2.0.0' 'pycparser==2.23'
        if ($LASTEXITCODE -ne 0) { throw 'TARGET_WHEEL_DOWNLOAD_HOLD' }

        $downloaded = @(Get-ChildItem -LiteralPath $wheels -File)
        if ($downloaded.Count -ne 3) { throw 'UNEXPECTED_WHEEL_COUNT_HOLD' }
        $seen = @{}
        $digests = @()
        foreach ($wheel in $downloaded) {
            if ($wheel.Extension -ne '.whl') { throw 'UNEXPECTED_DOWNLOAD_FILE_HOLD' }
            $matches = @($pins.Keys | Where-Object {
                $wheel.Name.StartsWith(($_ + '-' + $pins[$_] + '-'), [StringComparison]::OrdinalIgnoreCase)
            })
            if ($matches.Count -ne 1) { throw 'WHEEL_NAME_NOT_PINNED_HOLD' }
            $package = [string]$matches[0]
            if ($seen.ContainsKey($package)) { throw 'DUPLICATE_PACKAGE_HOLD' }
            $metadataUrl = 'https://pypi.org/pypi/' + $package + '/' + $pins[$package] + '/json'
            $metadata = Invoke-RestMethod -Uri $metadataUrl -TimeoutSec 90
            $record = @($metadata.urls | Where-Object { $_.filename -ceq $wheel.Name })
            if ($record.Count -ne 1 -or $record[0].packagetype -ne 'bdist_wheel' -or
                $record[0].yanked -or !($record[0].digests.sha256)) {
                throw ('PYPI_FILE_METADATA_HOLD:' + $wheel.Name)
            }
            $digest = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($digest -cne ([string]$record[0].digests.sha256).ToLowerInvariant()) {
                throw ('PYPI_WHEEL_HASH_HOLD:' + $wheel.Name)
            }
            $seen[$package] = $true
            $digests += [ordered]@{ package = $package; version = $pins[$package]; filename = $wheel.Name; sha256 = $digest }
            Write-Host ('SHA256 PASS: ' + $wheel.Name) -ForegroundColor Green
        }
        if ($seen.Count -ne 3) { throw 'WHEEL_DEPENDENCY_SET_HOLD' }
        $digests | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage 'WHEEL_SHA256.json') -Encoding UTF8

        # Preserve the already verified reference environment; copy only into NEW stage.
        Copy-Item -LiteralPath $sourcePy -Destination $privatePythonDir -Recurse
        $privatePython = Join-Path $privatePythonDir 'python.exe'
        if (!(Test-Path -LiteralPath $privatePython)) { throw 'COPIED_PYTHON_NOT_FOUND' }
        $pth = Join-Path $privatePythonDir 'python313._pth'
        if (!(Test-Path -LiteralPath $pth)) { throw 'EMBEDDED_PYTHON_PTH_MISSING' }

        Write-Host '=== YALNIZCA YENI TEST HEDEFINE WHEEL YERLESTIRME ===' -ForegroundColor Cyan
        & py -3 -m pip --isolated install `
            --disable-pip-version-check --no-input `
            --no-index --find-links $wheels --only-binary=:all: `
            --no-deps --no-compile --no-warn-script-location `
            --platform win_amd64 --python-version 3.13 --implementation cp `
            --abi cp313 --abi abi3 --abi none `
            --target $targetPackages `
            'cryptography==46.0.4' 'cffi==2.0.0' 'pycparser==2.23'
        if ($LASTEXITCODE -ne 0) { throw 'TARGET_WHEEL_INSTALL_HOLD' }

        # The embeddable Python ignores PYTHONPATH; explicitly permit only this private path.
        $currentPth = @(Get-Content -LiteralPath $pth)
        if ($currentPth -contains '_modeldeps') { throw 'ALREADY_MODIFIED_PTH_HOLD' }
        Add-Content -LiteralPath $pth -Value '_modeldeps' -Encoding ASCII

        Write-Host '=== REFERANS SURUM + NATIVE MODUL KONTROLU ===' -ForegroundColor Cyan
        $envVerifier = Join-Path $stage 'VERIFY_ISOLATED_RUNTIME.py'
        @(
            'import sys'
            'import sqlite3'
            'from importlib import metadata'
            'from cryptography.hazmat.primitives import hashes'
            'import _cffi_backend'
            'print(sys.version.split()[0])'
            'print(sqlite3.sqlite_version)'
            "print(metadata.version('cryptography'))"
            "print(metadata.version('cffi'))"
            "print(metadata.version('pycparser'))"
            'print(hashes.SHA256().digest_size)'
        ) | Set-Content -LiteralPath $envVerifier -Encoding ASCII
        $versions = @(& $privatePython -I -B $envVerifier)
        if ($LASTEXITCODE -ne 0 -or $versions.Count -ne 6 -or
            $versions[0] -ne '3.13.5' -or $versions[1] -ne '3.46.1' -or
            $versions[2] -ne '46.0.4' -or $versions[3] -ne '2.0.0' -or
            $versions[4] -ne '2.23' -or $versions[5] -ne '32') {
            throw 'PRIVATE_ENVIRONMENT_IMPORT_VERSION_HOLD'
        }
        $summary['environment_status'] = 'EXACT_ISOLATED_ENV_VERIFIED'
        $summary['wheel_hashes'] = $digests
        Write-Host '3.13.5 / 3.46.1 / 46.0.4 / cffi 2.0.0 / pycparser 2.23 OK' -ForegroundColor Green

        Write-Host '=== OZGun 344 MODEL / MEMORY REGRESYONU ===' -ForegroundColor Cyan
        $stdout = Join-Path $stage 'MODEL_344_STDOUT.log'
        $stderr = Join-Path $stage 'MODEL_344_STDERR.log'
        $log = Join-Path $stage 'MODEL_MEMORY_344.log'
        $proc = Start-Process -FilePath $privatePython `
            -ArgumentList @('-I', '-B', ('"' + $runner + '"')) `
            -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $raw = ([string](Get-Content -LiteralPath $stdout -Raw)) + "`n" + ([string](Get-Content -LiteralPath $stderr -Raw))
        $raw | Set-Content -LiteralPath $log -Encoding UTF8
        $summary['runner_exit_code'] = $proc.ExitCode
        if ($proc.ExitCode -eq 0 -and
            ([regex]::Matches($raw, 'SOURCE_PINS=114/114')).Count -ge 2 -and
            $raw.Contains('TOTAL_PASSED_GROUP_TESTS=344') -and
            $raw.Contains('EXIT_CODE=0') -and
            $raw.Contains('PRODUCT_ACCEPTANCE=HOLD')) {
            $summary['status'] = 'PASS_344_OF_344_SELECTED_REGRESSION'
        } else {
            $summary['status'] = 'TEST_FAIL_OR_HOLD'
        }
    }
    catch {
        $summary['error'] = $_.Exception.Message
        Write-Host ('HOLD: ' + $_.Exception.Message) -ForegroundColor Yellow
    }
    finally {
        $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
        Write-Host ('SONUC: ' + $summary['status']) -ForegroundColor Cyan
        Write-Host ('KANIT KLASORU: ' + $stage) -ForegroundColor Cyan
        Write-Host ('RAPOR: ' + $summaryPath) -ForegroundColor Cyan
        $log = Join-Path $stage 'MODEL_MEMORY_344.log'
        if (Test-Path -LiteralPath $log) {
            Get-Content -LiteralPath $log -Tail 20
        }
    }
}
