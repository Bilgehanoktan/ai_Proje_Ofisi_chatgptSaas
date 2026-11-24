# Windows PowerShell: reuse the already verified E: PR20 source; no checkout/fetch on it.
$ErrorActionPreference = 'Stop'
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
python -B (Join-Path $folder 'aios_pc_runner.py') --mode w8prepare --w8-reuse 'E:\AIOS\W8\W8_PR20_20261120_211752\source' --root 'E:\AIOS\W8\C04_TEST_20261120'
if ($LASTEXITCODE -ne 0) { throw 'W8 C04 HOLD/FAIL; inspect E: PC_TEST_RESULTS.json and logs.' }
