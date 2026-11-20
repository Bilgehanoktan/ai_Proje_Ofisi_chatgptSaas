# Run on the user's own Windows PowerShell. No execution-policy changes.
$ErrorActionPreference = 'Stop'
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $folder 'aios_pc_runner.py'
python -B $runner --mode allsafe --root 'C:\AIOS\TEST_RUN_20261120'
if ($LASTEXITCODE -ne 0) { throw 'AIOS test preflight has HOLD/FAIL; inspect PC_TEST_RESULTS.json and logs.' }
