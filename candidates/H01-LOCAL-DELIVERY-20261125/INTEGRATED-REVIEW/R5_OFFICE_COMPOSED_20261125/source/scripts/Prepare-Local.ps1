# Read-only preparation. Does not install packages or start product processes.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$RepoRoot,
      [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ManifestBlob)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepoRoot).Path
$checker = Join-Path $PSScriptRoot 'verify_product.py'
if (-not (Test-Path -LiteralPath $checker -PathType Leaf)) { throw 'verify_product.py missing' }
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $checker --root $root --manifest-blob $ManifestBlob
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $checker --root $root --manifest-blob $ManifestBlob
} else { throw 'Python 3 is required for source preflight.' }
if ($LASTEXITCODE -ne 0) { throw 'Source preflight failed. Do not install or run.' }
if (Get-Command node -ErrorAction SilentlyContinue) { & node --version } else { Write-Warning 'Node.js not found' }
if (Get-Command npm -ErrorAction SilentlyContinue) { & npm --version } else { Write-Warning 'npm not found' }
Write-Host 'Source preflight complete. No package installation, build, product process or test was run.'
Write-Host 'See docs/0167/LOCAL_MVP_SETUP.md. Runtime authority remains separate.'
