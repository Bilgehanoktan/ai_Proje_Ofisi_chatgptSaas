# MI-01 / W8 C05 — real OSV scan triage and blocking remediation plan
**20 Nov 2026, actual H01 Windows artifact. Classification: source-bound security hold; no owner approval or version changes.**

## 1. Actual received ZIP / independently inspected
- Received exact `C05_PUBLIC_SCA_20261120_190126Z.zip`, **27,169 bytes**, SHA256 `771e30737a86145873afc1698a3086efe440b247d3662bb0c606dc08e795c5cd` — matches Windows console receipt and ZIP CRC **PASS**, 5 non-encrypted JSON/MD reports, no duplicate filenames or path traversal.
- Raw JSONs independently opened: `C05_SCAN_SUMMARY.json`, `INVENTORY_89.json`, `OSV_RESULTS.json`, `REGISTRY_PROVENANCE_RESULTS.json`, plus `C05_SCAN_SUMMARY.md`. OSV run `2026-11-20T19:01:26Z` through `19:01:33Z`, platform `win32`, Python `3.13.14`, Node `v24.14.0`.
- Bound existing C04 source: `review/mi01-w8-p10j24-historical-session-recovery-20261120@9166afe299cd8f1ab9c52355ec21ec06c465d6ef`, SHA256 of original `REVIEW.json` `92279e79b65ac14693779ec6d225d5b0a24c8f9522df495b491bab81c4bc3c80`. Input ZIP `C05_EVIDENCE_20261120_214451.zip` SHA256 `523ec7667047aa04652a6b9750dc28a5473835e924b2c05b67eb0caa377465c0`. Exact pin matches retained, no re-prepare or new lock created.
- **89/89 real OSV public queries COMPLETE, 89/89 npm/PyPI registry metadata digest comparisons PASS**, 0 yanked PyPI releases, no unresolved external query errors. These metadata equality claims do not guarantee safe code or license compliance.
- OSV reports **1 affected PyPI package `cryptography==46.0.4`**, **13 raw advisory IDs** comprising **7 distinct GitHub GHSA records + 6 matching PYSEC aliases**. All other **88 package versions** have no OSV match *at this query time*; zero match does not imply permanently vulnerability-free.

## 2. Advisory identity reconciliation (source + public primary advisories)
The 13 exact original results deduplicate to these seven records:

| GHSA identifier | PYSEC alias | GitHub / maintainer severity | First patched version | Scope |
|---|---|---|---|---|
| [GHSA-537c-gmf6-5ccf](https://github.com/advisories/GHSA-537c-gmf6-5ccf) | — | High | 48.0.1 | Bundled wheel OpenSSL |
| [GHSA-g6cj-pr64-35w5](https://github.com/advisories/GHSA-g6cj-pr64-35w5) | PYSEC-2026-3552 | High | 50.0.0 | PKCS#7 EnvelopedData oracle |
| [GHSA-jwv3-5hgf-82ww](https://github.com/advisories/GHSA-jwv3-5hgf-82ww) | PYSEC-2026-3553 | High | 49.0.0 | Duplicate self-signed intermediates path-building amplification |
| [GHSA-m2h6-j472-rp4c](https://github.com/advisories/GHSA-m2h6-j472-rp4c) | PYSEC-2026-3554 | Moderate | 49.0.0 | DNS wildcard permittedSubtrees |
| [GHSA-m959-cc7f-wv43](https://github.com/advisories/GHSA-m959-cc7f-wv43) | PYSEC-2026-35 | Medium / maintainer low | 46.0.6 | X.509 peer name constraints |
| [GHSA-p423-j2cm-9vmq](https://github.com/advisories/GHSA-p423-j2cm-9vmq) | PYSEC-2026-36 | Moderate | 46.0.7 | Non-contiguous buffers |
| [GHSA-r6ph-v2qm-q3c2](https://github.com/advisories/GHSA-r6ph-v2qm-q3c2) | PYSEC-2026-2141 | High | 46.0.5 | SECT curve subgroup public key validation |

Cross references: [PyPI 50.0.2 available](https://pypi.org/project/cryptography/50.0.2/), release 2026-09-30; **a candidate, not tested nor approved**. The maximum displayed first patched threshold is `50.0.0`, but a new version must be **requeried against OSV, checked for Python 3.13 + Windows wheel compatibility and fully regression tested** before security approval. This report does not assert 50.0.2 safe/fully compatible.

## 3. Original source/static use review — actual Git blobs
- `product/ai-company-os-backend/requirements-history-signatures.txt` Git blob `b704e3dfd92b43d966dd4c023dab1ab576f57141` pins **`cryptography==46.0.4`** and labels it `Optional D0 verification adapter only`. W8 full C04 `prepare` downloads the optional adapter, so the wheel is in its frozen C05 security inventory even though it is not a required default production runtime dependency.
- `app/core/event_store/signed_history.py` Git blob `d4d379a7e4e55fd6f81f102d3fcb0903d50db0a1` imports `Ed25519PublicKey` to verify signed historical checkpoints; module header `D0 signed history readback, not a trust root or execution authority`.
- `app/core/transaction/signed_consume_reference.py` Git blob `477bcde63418dd43f886df7b32c5acd006d64a79` imports `InvalidSignature`, `Ed25519PrivateKey` and `Ed25519PublicKey` for D0 reference receipt. Its module header says `Never an execution grant`.
- No evidence from a full call-graph or execution path test shows seven issues non-applicable, so severity is **not waived** and no operational authority is elevated.

## 4. Blocking gate and narrow remediation proposal
1. **HOLD** current `46.0.4` candidate for formal C05 owner signoff. Treat 7 canonical GHSA findings as an active unresolved vulnerability review until an owner ratifies a documented fix or justified exposure-based exception.
2. **Proposed, not executed:** MI-01 source owner reviews an isolated `cryptography==50.0.2` version-change candidate. Alternatively, owner may evaluate removing the optional D0 adapter from the W8 packaging only with evidence that original W8 core29 and signed-history tests still perform intended assertions. No workaround or guard bypass accepted.
3. Product code is manifest-locked. Any authorized change to `requirements-history-signatures.txt` requires updating corresponding `SOURCE_MANIFEST.json` entries, dependency wheel/Python lock, W8 auxiliary pins and complete source-provenance tracing on **a new isolated branch**. Do **not** mutate owner PR20, PR33 historical fixture, or `integration/product-dev` without owner approval. Never reuse the old `REVIEW.json` approval hash.
4. After source owner selection, actually run **fresh exact original W8 `audit` → C04 `prepare` → C05 independent 89-package-or-changed-size public scan**; verify no unresolved advisories for the new version, all artifacts/Windows Python 3.13 metadata digest equivalence, license notices & third-party provenance and submit exact owner approval tied to the new SHA.
5. Only after C05 security/license/source-owner **PASS** may existing authorization be reviewed for C06 isolated wheel/npm install → C07 Next.js/Python original full tests → C08 native Chromium/real browser tests. Independently protected PostgreSQL, real IAM/ORG authority, A1 root/sink, IV/release still HOLD.

## 5. Architecture, progress, test/evidence and rollback
- Changed product source, database, APIs, events, dependency pins, build output, CI, auth grants, main, product-dev: **0**.
- Actual new result: full independent readback of a **real Windows external OSV report** and public advisory triangulation; **no new W8 original install/test/smoke** and no fresh C04.
- C05 public package metadata integrity/supplier release checks **PASS**, security clearance **HOLD due to cryptography==46.0.4**, optional Sharp/libvips LGPL and nonoptional caniuse-lite CC-BY licensing still open. C06–C08 `NOT_RUN`. W8 operational **3/8 → 3/8**, delta zero; MVP 0/11, independent IV 0/7; evidence-driven global 15/35/20/20/10 percent `HESAPLANAMADI`.
- Technical catalog touched: source pin `requirements-history-signatures.txt`; modules `signed_history.py` / `signed_consume_reference.py`; original W8 `w8_unified.py::prepare/lock_inventory/reviewed`, immutable generated `locks/REVIEW.json`, `locks/python.lock`; read-only OSV/PyPI/npm scan external APIs. No product symbol or persistent storage contract changed.
- Rollback of this documentation: normal revert. Preserve original user uploaded ZIP, existing Windows C04 source & report stages and the former HOLD receipts, current owner PR20, isolated PR33 and canonical source. Do not force push or delete evidence.
