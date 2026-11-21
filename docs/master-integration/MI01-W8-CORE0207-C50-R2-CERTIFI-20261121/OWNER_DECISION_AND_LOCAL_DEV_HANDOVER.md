# MI-01 / W8 — certifi 2026.11.20 H01 graph choice, R2 local DEV handover

Date: 2026-11-21. **Review-only successor**. No original W8 C07, actual Chromium C08, independent security C05 or product acceptance asserted.

## Source decision and conflict boundary
- User/H01 explicitly selected the new transitive **certifi 2026.11.20** graph instead of downgrading to 2026.10.23. This is a narrowly bounded source/dependency direction for isolated DEV only; not an independent security, legal, release or IV attestation.
- Parent PR37 exact source commit: `63fa94f5c73924940311b120e485c3ae34b87df6`, parent PR36: `683a26171ac54544260456ce84e19c38614aa5e2`; canonical `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` unchanged.
- PR37 C04 new Windows stage: `E:\AIOS\W8\PR37_INTEGRATED_DEV_20261121_151800\stage`. Its 552/552 product manifest audit, 17/17 source pairs and 31/31 inherited auxiliary pins PASS. Installed C06 on this new stage **NOT_RUN** as of writing. The prior PR36 stage has 2026.10.23; do not change or reuse it to claim the new graph.
- PR38 versioned R2 candidate adds only new test/contract/doc/catalog paths and never modifies PR34–37 sources, product code, SOURCE_MANIFEST, npm/Python product requirements or CI. No same-file conflict.

## New graph exact upstream provenance
- Windows fresh `REVIEW.json` SHA-256: `a5d5751047206186fad92098341c1f351648a8b012adc24df7dd83869a388009`. This is **not** the prior PR36 review `341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3`.
- Its Python `locks/python.lock` SHA-256 is `523b06d49b2069d072801a095f9f77d6a27aa65e7e3b95e7360de5ed16bad461`; npm lock SHA-256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`; product manifest Git blob `9660da1104617b4764d5f1e32009e4e3405b47f8`.
- Exactly 28 wheel entries; 27 unchanged. Only `certifi-2026.10.23-py3-none-any.whl` with SHA `e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1` was superseded by `certifi-2026.11.20-py3-none-any.whl`, SHA `7422df25243767b9877031a2248cb14d09ddac9beee846f4cef3d5c9191d488f`.
- Official PyPI: https://pypi.org/project/certifi/2026.11.20/ ; published Nov 20, 2026; publisher-file SHA matches user's Windows inventory; PyPI-verified GitHub Actions attestation from `certifi/python-certifi@bf6a4859116b0cba96673893e394298bbe529b1f`; independently verifying the sigstore attestation **NOT_RUN**. License publisher metadata: **MPL-2.0**. Distribution notice and third-party code compliance **NOT signed off**.
- GitHub-reviewed GHSA-6q48-6c7w-9gw2: affected `>=2019.03.09,<2026.10.19`, fixed `2026.10.19`; selected version `2026.11.20` is outside this specific affected range. Source: https://github.com/advisories/GHSA-6q48-6c7w-9gw2 . This is not an exhaustive vulnerability scan and does not certify use of all CA roots.
- Risk: renewed CA trust bundle could change TLS acceptance behavior; no real external providers, production certs, customer data or secrets used or authorized. Other `cryptography` signed provenance, `@img/sharp*` LGPL obligations and `caniuse-lite` CC-BY notice obligations remain separately under C05 independent owner HOLD.

## Versioned R2 sources
1. `tests/integration/core0207_crypto50_r2/CONTRACT.json`: contains both historical review reference and new immutable PR37 `REVIEW`/wheel/Python/npm/manifest pins, 55 historical file and four module/29 case invariants, explicit independent HOLD.
2. `tests/integration/core0207_crypto50_r2/run_core0207_c50_r2.py`: validates new wheel hash, exact 28-item review inventory and lock hashes, installed Python 3.13.17, installed certifi 2026.11.20 and cryptography 50.0.2; reuses unchanged historical P05 helper and exact 55 old source bytes for 29 cases. No `diagnostic-unpinned`, no formal W8 pass marker.
3. `tests/integration/w8_unified_u3_c50_r2_dev.py`: extends exact original U3 adapter and original P10J24 interception, runs R2 once during the inherited full DEV test, preserves original historical runner, removes any provisional W8 success markers, rejects C08 smoke. Bound to the new review SHA.
4. `tests/integration/test_w8_u3_c50_r2_dev.py`: versioned test contract: 11 inherited bridge negative tests plus two new certifi/R2 pin checks, **13 cases not run at time of commit**.

## Required sequence — no fake acceptance
1. Source owner reviews the exact R2 four-file source diff and new supplier evidence. R2 is a new candidate and cannot be presumed correct before actual tests.
2. From the **new PR38 exact source checkout** run original existing `w8_unified_u3_c50_r2_dev.py audit` and `prepare` in **fresh** E: staging (not old PR36 or PR37 stage). Verify 552/552 source hashes, 33 R2 auxiliary pins, and confirm the generated review SHA **equals** `a5d5751047206186fad92098341c1f351648a8b012adc24df7dd83869a388009`. If pip release graph drifts, HOLD (do not overwrite pins).
3. After exact match, use `--approve a5d...` only as a **technical lock fingerprint** to run isolated `install` (C06 DEV). It cannot serve as signed independent C05 security approval.
4. Run the R2 13 synthetic cases and full inherited W8 DEV chain, *only* if source/installed stage guards and C05 safety preflight permit. Keep R2-generated reports outside the stage and source. Do not allow acceptance markers or report substitution.
5. Full official C07 needs a separate owner-reviewed **release-capable** adapter (R2 deliberately review-only) and complete fresh test/build. Actual Chromium C08 requires formal C07 pass; independent C05/IV must independently decide provenance/license/security and H01 separately decides product release. No automatic release on D0 success.

## Prior test evidence and present gate status
- PR37 actual native Windows 29/29 historical-source successor D0 PASS; PR37 actual native 11/11 synthetic DEV PASS; C04 prepare new certifi graph PASS; prior PR36 Next build diagnostic exit 0. None counted again as product acceptance.
- R2 source checks and any full inherited R2 Windows suite: **NOT_RUN** until actual execution; cannot infer PASS from PR37 evidence.
- C06 on R2 fresh stage: **NOT_RUN**; official C07: **HOLD**; Chromium C08: **NOT_RUN**; independent C05: **HOLD**; W8 product acceptance **3/8 (37.5%) before and after**, delta 0 pp; weighted development **HESAPLANAMADI** because fixed phase-level denominator not reviewed.

## Maintenance/rollback
- New R2 runner symbols: `git_blob`, `require`, `exact_file`, `import_pinned`, `validate`, `main`. New R2 adapter symbols: `git_blob`, `demand`, `load_original`, `extend`, `load_candidate`. Test target `BridgeTest`. No production API, DB, event, schema, IAM or packaging diff.
- Error diagnostics: source/manifest/contract mismatch -> HOLD; certifi wheel/lock mismatch -> PR37_*_HOLD; historical 55 source mismatch -> original immutable helper failure; new version mismatch -> `CERTIFI_2026_11_20_VERSION_HOLD`; skipped or failed regression -> 29 of 29 not accepted. Prior stage and logs remain immutable.
- Rollback: close this review PR or normal revert only its newly introduced paths. Do not force push/rebase/merge or delete prior historical C06 stages and logs. Retain PR34–37 and main/product-dev history.

No new CEO authorization is required for scoped existing local DEV operation. **Independent approval remains an external authority and is not granted by these source decisions.**
