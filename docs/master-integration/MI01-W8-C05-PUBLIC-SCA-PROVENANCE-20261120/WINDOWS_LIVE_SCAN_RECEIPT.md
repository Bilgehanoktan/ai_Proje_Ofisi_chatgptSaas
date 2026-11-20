# MI-01 / W8 C05 — Actual Windows live public OSV and registry scan receipt
**Date:** 2026-11-20; **source:** user-supplied PowerShell 5.1 stdout only; **C05 acceptance:** HOLD_OWNER.

## Actual Windows test, not an offline mock
The user ran the exact previous `AIOS_W8_C05_PUBLIC_SCA_R1_20261120.py` artifact after a PowerShell SHA256 check for
`0c3f400b1561c999adb3cf614bf9b8c65b9eb38c11475ec08b0fdcf421b8f1b0` on Windows Python 3.13.
It read the existing immutable `C05_EVIDENCE_20261120_214451.zip` (SHA256
`523ec7667047aa04652a6b9750dc28a5473835e924b2c05b67eb0caa377465c0`), PR33 original source commit
`9166afe299cd8f1ab9c52355ec21ec06c465d6ef` and original `REVIEW.json` SHA256
`92279e79b65ac14693779ec6d225d5b0a24c8f9522df495b491bab81c4bc3c80`.
The tool emitted:

```
PINNED ZIP/REVIEW/LOCK PASS: 8 files, 28 PyPI and 61 npm packages; NO INSTALL
OSV QUERY COMPLETED: 40 / 89
OSV QUERY COMPLETED: 80 / 89
OSV QUERY COMPLETED: 89 / 89
REGISTRY PROVENANCE COMPLETED: 25 / 89
REGISTRY PROVENANCE COMPLETED: 50 / 89
REGISTRY PROVENANCE COMPLETED: 75 / 89
REGISTRY PROVENANCE COMPLETED: 89 / 89
EVIDENCE_ZIP: E:\AIOS\W8\W8_PR20_20261120_211752\C05_PUBLIC_SCA_20261120_190126Z.zip
EVIDENCE_ZIP_SHA256: 771e30737a86145873afc1698a3086efe440b247d3662bb0c606dc08e795c5cd
OSV: COMPLETE REGISTRY: COMPLETE
STATUS: C05_PUBLIC_SCA_REVIEW_EVIDENCE_OWNER_HOLD
```

## Precisely what this proves
The exact tool (read back SHA256 from the previous artifact) returns `registry_status='COMPLETE'` **only** when **every one of the 89** npm/PyPI registry metadata comparisons has status PASS and no PyPI release reports `yanked=True`.
This is a user-reported **real public endpoint execution**, not the prior 9/9 mock tests. `OSV: COMPLETE` proves the all-89 querybatch results were returned and aligned with requests with no unresolved pagination. **It does not mean there are zero advisories.** The number of OSV-affected dependencies and advisory IDs is recorded in `C05_SCAN_SUMMARY.json` but **the actual result ZIP or JSON has not yet been uploaded**, so these counts are **UNKNOWN**.

Public metadata equality does **not** prove clean binary code, absence of supply-chain compromise, license compliance, a full SCA verdict, owner approval, or legal/production authorization. It does not approve the final C05 gate; C06 dependency install, C07 full build/test, C08 Chromium acceptance remain NOT_RUN.

## Evidence request and next handling
Ask the user to upload the existing, **already generated** `C05_PUBLIC_SCA_20261120_190126Z.zip` (observed SHA256 `771e30737a86145873afc1698a3086efe440b247d3662bb0c606dc08e795c5cd`) directly, no rerun. This ZIP is a small **public package metadata/advisory report only**, not wheel or source ZIP. Verify archive bytes/hash/CRC and parse `C05_SCAN_SUMMARY.json`, `OSV_RESULTS.json` and `REGISTRY_PROVENANCE_RESULTS.json`; report actual vulnerability IDs with affected package versions, conditional criticality and owner disposition. Pass exact evidence to MI01 owner PR20 and source repair PR33 review. Only the owner may decide C05 approval binding to the exact `REVIEW.json` SHA.

## Files/functions, integration, documentation, rollback
Tool functions: `checked_zip`, `local_checks`, `osv_query_batch`, `registry_scan`, `registry_one`, `run`; source exists as conversation artifact only, not canonical product. External public APIs OSV `/v1/querybatch`, PyPI release metadata, npm registry release metadata. No product API, database, event, source code, dependencies, source-tree branching, privileged PostgreSQL or security permissions changed. Canonical product unchanged `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`; original owner PR20 `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`; PR33 source `9166afe299cd8f1ab9c52355ec21ec06c465d6ef`.

MI01 current formal **3/8 → 3/8** (delta 0), C04 real preparation on review source pending owner acceptance, C05 hash and public registry metadata checks PASS with OSV report pending **review/owner HOLD**, C06–08 NOT_RUN, MVP **0/11**, independent IV **0/7**, weighted 15/35/20/20/10 global **HESAPLANAMADI**. No acceptance percentage inferred from proxy operations. Preserve historical receipts and ZIPs on E:. No local cleanup or product rollback needed; documentation may be normally reverted if later evidence contradicts claims.
