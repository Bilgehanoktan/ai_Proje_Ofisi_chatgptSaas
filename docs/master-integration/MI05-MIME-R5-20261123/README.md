# AI Company OS — R5 scoped owner candidate source/evidence pack

This is a **two-file source candidate and local synthetic test evidence pack**, **not** a full Git checkout, product ZIP, original product-suite run, official W8 C07/C08/C05 or independent verification.

- Office child PR #50, commit `a92ac8a8e4d1303b66edc724d4f85c2abc52d456` (original owner PR #22).
- Three-proxy helper child PR #51, commit `e17c80a6552a8088372242e48abbb160fc24535a` (original owner PR #26).
- Each source SHA1 matches its exact Git blob and the previously tested R4 local proposal. Existing owner branches and product-dev were **not** edited.

## Reproduce local narrow synthetic checks (Node 22.16.0, tsc 5.8.3)

Run from this folder, without package installs:

```
tsc --target es2022 --module commonjs --lib es2022,dom --strict --skipLibCheck --outDir dist proxy/readBoundedD0Json.ts
node --test --test-reporter=tap evidence/pr51_mime_source_synthetic.test.cjs

tsc --target es2022 --module commonjs --lib es2022,dom --strict --skipLibCheck --rootDir frontend --outDir dist_office frontend/evidence-types.d.ts frontend/app/api/demo/office-workbench/route.ts
node --test --test-reporter=tap evidence/pr50_office_source_synthetic.test.cjs
```

Recorded result: PR #51 helper **11/11 PASS**, PR #50 route **10/10 PASS** in isolated in-memory no-network tests. Tests use exact Office parser + local port code, but they are **not the owner's full original Next/Chromium suite**. The historical R4 45/45 suite was not rerun here. Do not count these checks as production security, full W8, or product acceptance.

Owner ACCEPT/REJECT, shared `product/SOURCE_MANIFEST.json` recalculation, original regression, and independent security/W8 remain HOLD. See `evidence/RESULT.json` for SHA, rollback, and evidence scope.
