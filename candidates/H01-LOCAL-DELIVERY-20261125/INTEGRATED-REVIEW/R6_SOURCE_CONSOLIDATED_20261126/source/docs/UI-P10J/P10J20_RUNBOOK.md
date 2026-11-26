# P10J20 W8 — connected disposable workspace

Use exact P10J20 source, new manifest 9672f2e26f0635448f56cc02d338641bbe3ed5a5. Do not reuse core E1 or P10J19 REVIEW approval. From authenticated clean checkout:

```powershell
py -3 -B tests/integration/test_w8_p10j20.py
py -3 -B tests/integration/w8_p10j20.py audit --repo .
py -3 -B tests/integration/w8_p10j20.py prepare --repo . --stage C:\AICOS\p10j20-stage
```

Review transitive locks and provenance, then use actual reviewed REVIEW.json SHA256 only:

```powershell
$stage = 'C:\AICOS\p10j20-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j20.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j20.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j20.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```

Stop on nonzero. Require 486 product SHA pins, original inherited checks, inspector 16, A1-A4 inherited model suites, actual build/typecheck, UI 94 planned PNGs and native 5 planned PNGs. Review INSTALL_OK, BUILD_TEST_OK, SMOKE_OK, HYBRID_NATIVE_OK equal approval; native-ux-a4r2/HYBRID_NATIVE_EVIDENCE.json plus actual captures and raw log. Do not infer GPU, formal art or independent acceptance. No repeat over used stage.
