# MI-01 / C05 — public advisory and registry provenance assessment, R1
**Date:** 2026-11-20, source-scope Windows PR33 review, **no C05 approval**.

## Decision / why / where
The user's latest request is to **continue actual tests and close the open gates**. Existing 8-file C05 uploaded ZIP, 28/28 Windows wheel hash evidence, 61/61 npm metadata integrity and real W8 C04 owner `audit/prepare` are already obtained; do not duplicate them. Remaining MI-01 gate requires independent online package advisory and publisher release provenance review, a license/distribution evaluation and source-owner PR33 decision *before* C06 install/C07 tests/C08 native browser.

Canonical `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, original owner [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20) SHA `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542` and isolated historical fixture [PR #33](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/33) SHA `9166afe299cd8f1ab9c52355ec21ec06c465d6ef` are **unchanged**.

## Delivered review-only tool — exact source traceability
Conversation artifact: `AIOS_W8_C05_PUBLIC_SCA_R1_20261120.py`, **19,636 bytes**, SHA256 `0c3f400b1561c999adb3cf614bf9b8c65b9eb38c11475ec08b0fdcf421b8f1b0`. Exact original 8-file input `C05_EVIDENCE_20261120_214451.zip`, SHA256 `523ec7667047aa04652a6b9750dc28a5473835e924b2c05b67eb0caa377465c0`, original `REVIEW.json` SHA256 `92279e79b65ac14693779ec6d225d5b0a24c8f9522df495b491bab81c4bc3c80`, immutable npm lock `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`.

The script uses Python 3 stdlib only; **not yet executed on Windows**. Its safe operation:
- Verify ZIP SHA, 8 expected members, no encryption, size cap and CRC before parsing any input. Validate 28 unique PyPI names/versions/wheel SHA references, seven direct Python pinned requirements, and 61 npm lock packages with root graph, overrides, integrity and original environment. Fail closed when a byte changes.
- For the 89 **public package names and versions only**, query `https://api.osv.dev/v1/querybatch` in 40-record batches and collect matching advisory IDs. Reject missing/misaligned/paginated responses. API is documented by [OSV batch endpoint](https://google.github.io/osv.dev/post-v1-querybatch/); an advisory-free result means **no matches in that database as of query time**, not a security guarantee.
- Compare each Python wheel exact filename and SHA256 to `https://pypi.org/pypi/{name}/{version}/json` published release metadata; compare 61 npm declared integrity records to `https://registry.npmjs.org/{package}/{version}` published metadata (never download or execute package content). Record uncertain 404, network failures, mismatches or yanked release as **HOLD**. Registry metadata checks are not signed attestations or actual binary malware/license inspection.
- Create a fresh dated folder solely under the explicitly provided existing E: output parent with `INVENTORY_89.json`, `OSV_RESULTS.json`, `REGISTRY_PROVENANCE_RESULTS.json`, `C05_SCAN_SUMMARY.json`, `C05_SCAN_SUMMARY.md`, plus a small upload-ready `C05_PUBLIC_SCA_<timestamp>.zip` of these reports; the scanned stage source, ZIP, locks, wheelhouse, npm cache, Git branch and PC policies remain untouched. If remote APIs fail, independent scanning stays HOLD and output retains failure status. Network query sends only public names+versions; no source ZIP, credentials, company code, tokens or secrets. Not an authorized test install/build/smoke.
- Two reproducibility boundaries: evidence bound to `win32/Python 3.13.14/Node v24.14.0` only; provenance and license classification require manual owner review. No on-prem model, no service runtime, no production or PG access.

### Actual local test evidence — not an OSV external result
This assistant environment physically executed original `AIOS_W8_C05_PUBLIC_SCA_R1_20261120.py --zip /mnt/data/C05_EVIDENCE_20261120_214451.zip --out /mnt/data --self-test` against the actual uploaded byte-exact ZIP.
Result: **9/9 PASS**: (1) positive verified 89 package inventory, (2–4) independent negative corruption guards for Python lock, REVIEW, npm lock, (5) OSV mock batch schema+alignment over all 89, (6) forced pagination HOLD, (7) npm metadata-integrity mock positive, (8) PyPI wheel digest mock positive, (9) PyPI mismatched digest negative HOLD. No network requests in self-test mode. Python syntax compilation PASS. Source content and actual Windows runtime **not independently executed online**; all mocked API checks must be labeled helper tests and cannot count as W8 original C06–C08.

## Windows instruction (read-only source and public internet metadata)
Save Python artifact in `$env:USERPROFILE\Downloads`. In Windows PowerShell 5.1:
```powershell
$tool = "$env:USERPROFILE\Downloads\AIOS_W8_C05_PUBLIC_SCA_R1_20261120.py"
$root = 'E:\AIOS\W8\W8_PR20_20261120_211752'
py -3.13 $tool --zip "$root\C05_EVIDENCE_20261120_214451.zip" --out $root
```
Note: `--self-test` option runs only offline fixture checks and creates no artifacts; full invocation above runs actual **public** APIs only. It uses no admin rights and installs nothing. If unable to reach public OSV/PyPI/npm, status HOLD, do not infer success. Request the newly produced `C05_PUBLIC_SCA_...\C05_SCAN_SUMMARY.json`, `OSV_RESULTS.json`, `REGISTRY_PROVENANCE_RESULTS.json` and review all findings before owner decision. Do not upload credentials/private source content.

## Technical catalog and acceptance boundary
- Existing source contracts unchanged: `tests/integration/w8_unified.py::{prepare,reviewed,lock_inventory}`, `w8_unified_u3.py::load_candidate`, `SOURCE_MANIFEST.json`, product frontend npm lock, backend requirements.
- New **conversation-only** Python read-only analyzer: `checked_zip`, `local_checks`, `parse_python_lock`, `osv_query_batch`, `registry_one`, `registry_scan`. External APIs: OSV `POST /v1/querybatch`; PyPI `GET /pypi/<name>/<version>/json`; npm `GET /<name>/<version>`. New product code, API, DB, events, database migrations, external command execution, local install or GitHub CI: **none**.
- C04 actual real Windows pinned PR33 prepare done but owner signoff pending; C05 static file integrity PASS, public SCA **NOT_RUN on Windows**, license binary compliance HOLD, independent source owner signoff HOLD. C06 install, C07 full tests/build, C08 Chromium native smoke **NOT_RUN**. Original W8 acceptance previous/current `3/8 → 3/8`, change `0`; MVP `0/11 → 0/11`, IV `0/7 → 0/7`; weighted development 15/35/20/20/10 **HESAPLANAMADI**. No invented acceptance percentage.
- Next: user runs public SCA, uploads actual results; review OSV advisories and publisher mismatches, get owner-specific C05 decision bound to `REVIEW.json` SHA; only then design authorized C06. In parallel, separately owned G7 current ORG original 7/7 still NOT_RUN; reuse [PR32](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/32) rather than duplicate a launcher.
- Recovery/rollback: preserve original ZIP, earlier HOLD stages/console receipts and owner branches. Analyzer makes a new isolated report directory only; manual report deletion (after inspection) restores pre-scan state. GitHub documentary rollback via normal revert. No force push, no product merge or security authority escalation.
