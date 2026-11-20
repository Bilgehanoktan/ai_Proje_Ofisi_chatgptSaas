# MI-01 / G1–G2 — cryptography 50.0.2 isolated source candidate

**Date:** 2026-11-20. **Classification:** REVIEW-ONLY / NOT OWNER APPROVED / NO CI OR PRODUCTION. Do not merge to the canonical product branch.

## Why and exact scope
The separately recorded real 2026-11-20 Windows OSV scan found seven distinct GHSA matches (six additional PYSEC aliases) at the existing 46.0.4 pin. This candidate changes only the optional D0 history-signature dependency from 46.0.4 to 50.0.2, regenerates its exact SHA-256 entry in the 552-file product manifest, and re-pins the top-level W8 U3 source adapter to the resulting manifest Git blob. All other product file and historical/NPM dependency pin bytes are unchanged. It does **not** alter signed history or Ed25519 runtime behavior, IAM, any security boundary, database/API/event, grants, CI, workflow, main or product-dev.

**Original PR33 base:** `9166afe299cd8f1ab9c52355ec21ec06c465d6ef`

| Evidence | Value |
|---|---|
| Original requirements Git blob | `b704e3dfd92b43d966dd4c023dab1ab576f57141` |
| New requirements Git blob | `921818de26b481ed94603d8e596a384abf04bfa9` (expected; independently re-read from GitHub) |
| New requirements SHA-256 | `14f7abb23f8fa599eec9103ef59f26ead5650b0075c7d93b1da5c2494473bcd2` |
| Requirements bytes | 120 (unchanged) |
| Original manifest Git blob | `27b4eb5816265d4e6e6d2458acb6220db7dd0c76` |
| New manifest Git blob | `589a77c2115bf255600d130087fc8973ecf2b7e5` |
| Original W8 adapter Git blob | `b4043035e75c5a18b7b19a9f18eecfef8e8fe677` |

## External G1 technical review, not an approval
[PyPI 50.0.2](https://pypi.org/project/cryptography/50.0.2/) publicly lists `Python !=3.9.0, !=3.9.1, >=3.9`, `cp311-abi3-win_amd64` (compatible with CPython 3.13 x64), package provenance metadata, and `Apache-2.0 OR BSD-3-Clause`. [Vendor change log](https://cryptography.io/en/latest/changelog/) documents API removals in 47/49 and OpenSSL wheel changes. Existing D0 consumers are `signed_history.py` and `signed_consume_reference.py`; unchanged APIs do not prove binary compatibility. Exact new-wheel SHA-256, embedded OpenSSL, live OSV queries, negative Ed25519 regression and distribution licensing are **not** accepted by public metadata alone.

## Exact gate status / next action
- G1: Public compatibility review complete; **MI-01 owner candidate approval HOLD**.
- G2: Isolated source patch; verify full GitHub manifest/tree and owner test pins before transfer; **owner review HOLD**.
- G3: Original W8 audit and fresh Windows C04 new wheelhouse/`python.lock`/`REVIEW.json` **NOT_RUN**.
- G4: New OSV, PyPI, npm, Windows wheel SHA, OpenSSL and all licensing + independent source/security reviewer **HOLD**.
- G5 C06 install / G6 C07 Ed25519-Python-Next.js regression / G7 C08 Chromium **NOT_RUN**; C05 has to be closed first.
- G8: Canonical integration and formal acceptance **HOLD**.

**Recovery:** normal isolated branch revert or close PR. Preserve original 46.0.4 evidence, PR20, PR33, the original Windows stage and canonical 553 product tree. No automatic merge, no secret/customer data, external effect, provider or production permission.
