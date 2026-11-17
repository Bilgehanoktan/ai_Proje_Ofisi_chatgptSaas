# P10J24 — Acceptance continuation runbook
Use an authenticated clean checkout of the exact integration/p10j24-product-acceptance delivery commit. Do not reuse P10J23 stage/review; no dependency install before review. Keep Windows/native deferred until the permitted environment is available.

```powershell
py -3 -B -m unittest discover -s tests/integration -p test_p10j24_historical.py -v
py -3 -B tests/integration/w8_p10j24.py audit --repo .
py -3 -B tests/integration/w8_p10j24.py prepare --repo . --stage C:\AICOS\p10j24-stage
```
Expected audit if exact clean checkout: 491 source SHA-256 pins, 17 shared pairs, 24 auxiliary blob pins. The 55-file historical closure is materialized during test. Inspect npm lock, Python wheels, provenance, direct pins, hashes and REVIEW.json. Only after explicit review of the actual fingerprint:
```powershell
$stage = 'C:\AICOS\p10j24-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j24.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j24.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j24.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```
Stop on any nonzero exit. Retain core29-p10f.json, raw W8 logs, actual REVIEW.json and lock hashes, BUILD_TEST_OK/SMOKE_OK/HYBRID_NATIVE_OK and real 94+5 product captures. Separately exercise both themes, 320/390/768/1440 px, dashboard routes, all Studio interactions, source search/selection resets, keyboard navigation and office context. No marker/gate manual creation, no bypass, no synthetic image substitution. PG/RLS and independent acceptance remain separate. No main/CI/PROD, provider calls or real effects.
