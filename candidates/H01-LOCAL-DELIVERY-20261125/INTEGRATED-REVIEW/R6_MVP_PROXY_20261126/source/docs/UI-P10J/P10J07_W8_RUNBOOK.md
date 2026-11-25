# P10J-07 — isolated W8 execution runbook
Source commit 182adb096cb7ae46103fe86e465df36217561a71; manifest Git blob 106bc3353d545cf4145093c766b8b9d18caecc5d; 390 pins. Use network-capable isolated development machine, authenticated GitHub access if required. No CI, real providers, external effects, main or PROD. PowerShell (new working directory):
```powershell
git init aicos-p10j07
Set-Location aicos-p10j07
git remote add origin https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git
git fetch --depth 1 origin 182adb096cb7ae46103fe86e465df36217561a71
if ($LASTEXITCODE -ne 0) { throw "Checkout HOLD" }
git -c core.autocrlf=false checkout --detach FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw "Checkout HOLD" }
if ((git rev-parse HEAD) -ne "182adb096cb7ae46103fe86e465df36217561a71") { throw "Source pin HOLD" }
python tests/integration/w8_p10j05.py audit
if ($LASTEXITCODE -ne 0) { throw "Audit HOLD" }
$stage = Join-Path (Split-Path -Parent (Get-Location).Path) "aicos-p10j07-stage"
python tests/integration/w8_p10j05.py prepare --stage $stage
if ($LASTEXITCODE -ne 0) { throw "Prepare HOLD" }
```
Review locks/REVIEW.json, package-lock provenance, python.lock, wheel SHA-256 and exact transitive versions. A fingerprint is not approval. Do not install until actual review and approval. Then:
```powershell
$approved = (Get-FileHash (Join-Path $stage "locks/REVIEW.json") -Algorithm SHA256).Hash.ToLowerInvariant()
python tests/integration/w8_p10j05.py install --stage $stage --approve $approved
if ($LASTEXITCODE -ne 0) { throw "Install HOLD" }
python tests/integration/w8_p10j05.py test --stage $stage --approve $approved
if ($LASTEXITCODE -ne 0) { throw "Test HOLD" }
# Set $chromium to a reviewed local Chrome/Chromium executable.
python tests/integration/w8_p10j05.py smoke --stage $stage --approve $approved --chromium $chromium
if ($LASTEXITCODE -ne 0) { throw "Smoke HOLD" }
```
Preserve console, lock inventory, exact commit, 52 baseline captures and sample DB hashes. Inspect new graph and lifecycle interactions separately in actual React browser. On failure preserve stage; use a new stage, never reset real claims. Core 0220 PG/RLS and independent acceptance remain separate. Archive alternative: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/182adb096cb7ae46103fe86e465df36217561a71.zip (not downloaded in current runtime).
