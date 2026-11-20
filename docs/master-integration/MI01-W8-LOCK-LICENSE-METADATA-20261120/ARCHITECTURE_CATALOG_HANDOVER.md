# MI-01 / W8 — independent immutable npm lock license metadata screening

**2026-11-20.** Source: open [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20), head `6678a7fd3aa50842b70b2b8a922c02b002884397`, Git blob `4cd33f437df85d7e74c7946a0999f76adf2e31fe`, the previously existing 33,618-byte npm v3 lock. This is a **read-only metadata pre-screen, not the owner-approved supply-chain, license compliance, or security review**.

## Actual new observations

- 61/61 transitive package records have metadata license, exact registry.npmjs.org HTTPS `resolved` URL, and syntactically present `sha256-` or `sha512-` integrity metadata. **No downloaded archive or calculated tarball digest was verified.**
- Root dependencies and devDependencies are value-for-value equal to exact `package.json` Git blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3`, ignoring JSON key ordering; postcss `8.5.32` and sharp `0.35.5` overrides match.
- License labels from `package-lock.json`: `{"MIT":26,"Apache-2.0":16,"LGPL-3.0-or-later":10,"Apache-2.0 AND LGPL-3.0-or-later AND MIT":1,"Apache-2.0 AND LGPL-3.0-or-later":3,"CC-BY-4.0":1,"ISC":2,"BSD-3-Clause":1,"0BSD":1}`.
- **14** platform-optional `@img/sharp*` records contain `LGPL-3.0-or-later` in their metadata license expression (not necessarily all installed on one platform). **One non-optional** `caniuse-lite` has `CC-BY-4.0` metadata. Need distribution, linkage, notices, attribution, source and actual deployed artifact review by license owner before C05 sign-off.
- **39** packages have `optional` flag; **32** OS-restricted and **32** CPU-restricted entries. This is package-lock metadata, not installed artifact evidence.

## Ownership and delivery

- MI-01 owner is **actively working** on frozen-lock W8 PR20, with its own local 15/15 synthetic helper results. MI-04 G2–ORG PR19 is concurrently active; its previous isolated 65/65 CI is not security approval. **No PR changes, reruns or source overwrites** by this screening.
- Original W8 C04 `prepare`, Python wheelhouse/`python.lock`/`REVIEW.json`, C05 owner review, C06 install, C07 full Next/TS/backend build, C08 native Chromium smoke all **NOT_RUN/HOLD**. Native tarball hash checks, SPDX artifact content, external vulnerability/repository advisories not evaluated here. C01-C03 previous limited evidence preserved.
- MI01 operational 3/8→3/8, IAM/ORG 42.5%→42.5%, MI08 45%→45%; global weighted development HESAPLANAMADI, independent acceptance Δ0pp.

## Technical catalog / maintenance / rollback

- Source lock `tests/integration/locks/mi01-frozen-npm/package-lock.json` Git blob `4cd33f437df85d7e74c7946a0999f76adf2e31fe`; frontend `product/ai-company-os-frontend/package.json` blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3`, root exact matching pins and overrides.
- Modified in this round: *governance docs and central progress only*. Product files, class/function/API, SQL schema, event contracts, npm/Python dependency pins, CI workflow, permissions and source branches: **unchanged**.
- If PR20 head or lock Git blob changes, evidence must be recalculated. Keep C05 HOLD pending owner license/security sign-off, platform-native package contents, actual wheel/tarball hashes and vulnerability checks. Rollback: normal revert of this new governance commit without rewriting owner PR20/PR19 or product-dev.
