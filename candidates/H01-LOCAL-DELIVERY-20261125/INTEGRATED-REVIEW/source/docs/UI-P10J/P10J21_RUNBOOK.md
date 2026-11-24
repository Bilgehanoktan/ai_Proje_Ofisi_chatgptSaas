# P10J21 — reviewed W8 runbook
Use a fresh authenticated checkout and new stage. Manifest ce8b61352b9b56825a8ecd01238025fc07b7d2d2. Never reuse P10J20 review.
```powershell
py -3 -B tests/integration/w8_p10j21.py audit --repo .
py -3 -B tests/integration/w8_p10j21.py prepare --repo . --stage C:\AICOS\p10j21-stage
```
After independent lock review, use only actual REVIEW.json hash:
```powershell
$stage = 'C:\AICOS\p10j21-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j21.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j21.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j21.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```
Stop on failure. Inherited planned captures remain 94 UI + 5 native; no new automatic screenshot claims. Additional P10J21 manual browser cases NOT_RUN: open Beceriler (6 source candidates), intersect Memory + Research (2), inspect lineage and change filter (selection cleared), search unmatched/reset (6 restored, diagnostic reset), verify no install/retrieval/grant controls and light/dark responsive layout. Capture separately and label manual. Verify actual build and parent markers; no native or independent acceptance inferred.
