# P10J16 isolated W8 runbook

Exact source candidate manifest 8b88d3e6ad080ab61bd91b95c9b98d28faea9b1a. Do not use historical A0 or P10J15 lock approvals as P10J16 review. Use an authorized fresh checkout and disposable stage. See P10J15_RUNBOOK.md for existing SQL/PG constraints; use this revision's manifest for union and keep core-only runner on core checkout.

```powershell
py -3 -B scripts/verify_product.py --root . --manifest-blob 8b88d3e6ad080ab61bd91b95c9b98d28faea9b1a
py -3 -B tests/integration/w8_p10j16.py audit --repo .
py -3 -B tests/integration/w8_p10j16.py prepare --repo . --stage C:\AICOS\p10j16-stage
```
Review REVIEW.json and actual locks before continuing.
```powershell
$stage = 'C:\AICOS\p10j16-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j16.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j16.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j16.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```
Require 468 source pins, all inherited W8 checks, ten premium suites, eight isolated UI tests, full build/typecheck, actual backend/Next smoke and 76 planned captures. Inspect raw logs, console, loopback and captures; actual independent approval remains separate. Stop on first failure; no live data/credentials/CI/main/PROD/external effects.
