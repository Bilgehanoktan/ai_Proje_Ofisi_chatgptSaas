# P10J22 — W8 runbook

Fresh authenticated checkout and fresh stage required. Manifest 3d7bb6a05f523b2691c8a7cfe048f030e2d94c91. Do not reuse P10J21 review or stage. Existing W8 chain retained.

```powershell
py -3 -B tests/integration/w8_p10j22.py audit --repo .
py -3 -B tests/integration/w8_p10j22.py prepare --repo . --stage C:\AICOS\p10j22-stage
```
After actual lock review use the reviewed REVIEW.json SHA-256:
```powershell
$stage = 'C:\AICOS\p10j22-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j22.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j22.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j22.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```
Stop on any failure. Inherited planned captures 94 UI + 5 native; additional manual P10J22 cases NOT_RUN: both new source tabs, 3/5 counts, no cross-domain results, Turkish search, selection reset, existing tabs, unknown metrics, keyboard and narrow viewport. Record actual captures separately. No new automated capture count or independent approval.
