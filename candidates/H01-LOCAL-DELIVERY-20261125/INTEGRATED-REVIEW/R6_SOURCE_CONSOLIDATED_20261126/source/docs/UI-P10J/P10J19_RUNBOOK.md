# P10J19 W8 — connected disposable workspace

Use exact commit, new manifest 6caabe5948967e1532a117e99780e7fb90b1b968, never reuse P10J18/core E1 REVIEW hash. From authenticated clean checkout run:

```powershell
py -3 -B scripts/verify_product.py --root . --manifest-blob 6caabe5948967e1532a117e99780e7fb90b1b968
py -3 -B tests/integration/w8_p10j19.py audit --repo .
py -3 -B tests/integration/w8_p10j19.py prepare --repo . --stage C:\AICOS\p10j19-stage
```

Review REVIEW.json and locks. Only with actual reviewed hash and disposable D0 environment:

```powershell
$stage = 'C:\AICOS\p10j19-stage'
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B tests/integration/w8_p10j19.py install --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j19.py test --stage $stage --approve $approve
py -3 -B tests/integration/w8_p10j19.py smoke --stage $stage --approve $approve --chromium '<reviewed browser path>'
```

Require 482 pins, inherited tests, 11 roadmap checks, original A4 checks, actual build/typecheck and 90 planned captures. Record raw evidence, failures and screenshot pixel review separately. No independent grant or native performance acceptance inferred.
