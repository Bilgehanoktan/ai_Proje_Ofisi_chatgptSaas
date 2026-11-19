# AI Company OS / P0 - isolated Windows x64 reference runtime, environment only.
# No global Python installation, no pip, no product writes, no tests.
& {
    $ErrorActionPreference = 'Stop'

    $base = 'C:\AIOS\MI05_20261120_001126'
    $source = Join-Path $base 'verified_manual\TRANSFER_REPORT.json'
    if (!(Test-Path -LiteralPath $source)) {
        throw 'Dogrulanmis aktarim raporu bulunamadi.'
    }
    $transfer = Get-Content -LiteralPath $source -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($transfer.git_tree -ne '187f652f1b1ff8604981833f634c4531a33f8a47' -or
        $transfer.status -ne 'SOURCE_RECOVERED_TESTS_NOT_RUN' -or
        [int]$transfer.model_rows -ne 114 -or
        [int]$transfer.core_rows -ne 55) {
        throw 'Kaynak sabitlemesi uyusmuyor: HOLD.'
    }
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
        throw 'Bu referans paket yalniz Windows x64 icindir: HOLD.'
    }

    $stage = Join-Path $base ('P0_ENV_3135_3461_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
    $pythonZip = Join-Path $stage 'python-3.13.5-embed-amd64.zip'
    $sqliteZip = Join-Path $stage 'sqlite-dll-win-x64-3460100.zip'
    $pythonDir = Join-Path $stage 'python'
    $sqliteDir = Join-Path $stage 'sqlite_original'

    $pythonUrl = 'https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip'
    $sqliteUrl = 'https://www.sqlite.org/2024/sqlite-dll-win-x64-3460100.zip'
    $pythonSha = '7D2650FD9D1B9D002D4A315D5F354247FD6A44F30517C7EF577B08F57A0FB6D9'
    $sqliteSha = '300CB2918946F42A1A2F7F31A8DD89EDC202570E4E49D21E13D33ECDF80A6B67'

    Write-Host '=== RESMI KAYNAK ARSIVLERI ===' -ForegroundColor Cyan
    Write-Host "Yeni klasor: $stage"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing -TimeoutSec 120
    Invoke-WebRequest -Uri $sqliteUrl -OutFile $sqliteZip -UseBasicParsing -TimeoutSec 120

    $actualPythonSha = (Get-FileHash -LiteralPath $pythonZip -Algorithm SHA256).Hash.ToUpperInvariant()
    $actualSqliteSha = (Get-FileHash -LiteralPath $sqliteZip -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actualPythonSha -ne $pythonSha -or $actualSqliteSha -ne $sqliteSha) {
        throw 'INDIRILEN ZIP SHA256 DOGRULAMASI BASARISIZ: HOLD.'
    }

    Expand-Archive -LiteralPath $pythonZip -DestinationPath $pythonDir -ErrorAction Stop
    Expand-Archive -LiteralPath $sqliteZip -DestinationPath $sqliteDir -ErrorAction Stop

    $oldDll = Join-Path $sqliteDir 'sqlite3.dll'
    $privateDll = Join-Path $pythonDir 'sqlite3.dll'
    $pythonExe = Join-Path $pythonDir 'python.exe'
    if (!(Test-Path -LiteralPath $oldDll) -or
        !(Test-Path -LiteralPath $privateDll) -or
        !(Test-Path -LiteralPath $pythonExe) -or
        !(Test-Path -LiteralPath (Join-Path $pythonDir 'python313._pth'))) {
        throw 'Beklenen resmi Python/SQLite dosyalari bulunamadi: HOLD.'
    }

    # ONLY the freshly extracted private Python folder is modified.
    # Both original ZIPs are retained untouched for rollback and provenance.
    Copy-Item -LiteralPath $oldDll -Destination $privateDll -Force

    $versions = @(& $pythonExe -I -B -c 'import sys,sqlite3;print(sys.version.split()[0]);print(sqlite3.sqlite_version)')
    if ($LASTEXITCODE -ne 0 -or $versions.Count -ne 2) {
        throw 'Izole Python/SQLite calistirilamadi: HOLD.'
    }
    if ($versions[0] -ne '3.13.5' -or $versions[1] -ne '3.46.1') {
        throw "REFERANS SURUM UYUSMAZLIGI: Python=$($versions[0]), SQLite=$($versions[1]); HOLD."
    }

    $receipt = [ordered]@{
        status = 'ISOLATED_PYTHON_SQLITE_READY_CRYPTO_NOT_INSTALLED'
        source_tree = $transfer.git_tree
        python_version = $versions[0]
        sqlite_version = $versions[1]
        cryptography = 'NOT_INSTALLED'
        python_archive_sha256 = $actualPythonSha
        sqlite_archive_sha256 = $actualSqliteSha
        python_executable = $pythonExe
        model_344 = 'NOT_RUN'
        core_29 = 'NOT_RUN'
        full_w8_build = 'NOT_RUN'
        protected_commit = 'HOLD'
        independent_acceptance = 'HOLD'
    }
    $report = Join-Path $stage 'ENVIRONMENT_PRECHECK.json'
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $report -Encoding UTF8
    Write-Host ''
    Write-Host 'IZOLE REFERANS ORTAM HAZIR (TESTLER HENUZ CALISMADI)' -ForegroundColor Green
    Write-Host "Python: $($versions[0]) | SQLite: $($versions[1])"
    Write-Host "Rapor: $report" -ForegroundColor Green
}
