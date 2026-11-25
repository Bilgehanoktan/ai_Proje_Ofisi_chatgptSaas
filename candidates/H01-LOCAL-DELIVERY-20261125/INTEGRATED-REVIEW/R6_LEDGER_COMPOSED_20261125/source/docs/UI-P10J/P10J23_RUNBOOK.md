# P10J23 — standalone fixture and W8
From exact candidate checkout in a permitted test environment with reviewed Playwright and Chromium:
```powershell
py -3 tests/integration/p10j23_visual_fixture.py --frontend product/ai-company-os-frontend --chromium '<browser path>' --output C:\AICOS\p10j23-fixture
```
This produces 8 standalone images and JSON, not W8 acceptance. Do not use with modified CSS parent. For full acceptance use fresh stage and fresh review:
```powershell
py -3 -B tests/integration/w8_p10j23.py audit --repo .
py -3 -B tests/integration/w8_p10j23.py prepare --repo . --stage C:\AICOS\p10j23-stage
$stage = 'C:\AICOS\p10j23-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j23.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j23.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j23.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```
Stop on failure. Inherited planned 94 UI + 5 native captures are distinct from the 8 fixture captures. Manually inspect actual route layout, desktop/mobile navigation, both themes, Finance/Security and Skill/Memory source inspectors, keyboard focus and office geometry. No automatic gate promotion.
