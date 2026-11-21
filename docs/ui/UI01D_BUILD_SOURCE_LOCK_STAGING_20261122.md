# UI-01-D — isolated exact-lock source co-location, OWNER REVIEW / BUILD HOLD
Date: 2026-11-22
Task: `MI05-UI01D-FULL-BUILD-CHROMIUM-GATE-20261122`

## What this source candidate means
This isolated child of PR #39 **puts the previously existing exact npm lock bytes inside the versioned frontend source tree**. It prepares a reproducible checkout candidate; it does **not** claim that a Windows/Linux checkout exists in the model's execution container, that `npm ci` ran, or that MI-05 / MI-01 approved the dependency graph. Draft status and independent security/IV restrictions remain in force.

- Parent PR #39 head: `8e614ec744b59bb1c3cb6c1166f59c3a6eb4941e` (one parent, no PR #39 source edit)
- Canonical product base at review: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`; canonical manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`
- Parent PR #39 exact manifest blob: `e0f4ff504c63325a51829492ac2fe031de3fee9f`, 554 entries. GitHub full recursive tree of PR #39, tree `51a6573c0e6b28e41d5f4d90d8b9041e6082ba3a`, was not truncated and contained 555 product blobs (554 manifest entries + self); 554/554 path/byte sizes matched, no missing or unexpected product files. This is a GitHub tree check, **not local file SHA-256 for 554 sources**.
- Original pre-existing lock: `integration/mi-common-source-review-01:docs/ORG-07C-R8-INTEGRATION/original-lock/package-lock.json`, Git blob `4cd33f437df85d7e74c7946a0999f76adf2e31fe`, SHA-256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`, UTF-8 bytes 33618, lockfileVersion 3 and 62 packages.
- Candidate new frontend file: `product/ai-company-os-frontend/package-lock.json`, **same exact original blob**. No npm reinstall, lock regeneration or dependency version bump.
- Scoped manifest is extended 554 -> **555** entries, one new lock path; all previous manifest fields, owner-specific source and old source history are preserved; candidate status is in this addendum, not forged in inherited root metadata.
- Static lock compatibility check with canonical package.json: exact name, version, sorted direct deps, sorted dev deps, resolved Next 15.5.29, React 19.1.10, TypeScript 5.9.3, PostCSS 8.5.32, Sharp 0.35.5 all matched. Does not certify license or network-transitive dependency safety.

## Distinct gate outcomes
- Exact GitHub co-located source and lock at one isolated commit: **SOURCE_READY_FOR_OWNER_REVIEW** (readback required on the created commit).
- MI-05 and MI-01 independent owner sign-off: **HOLD** (PR #39 had 0 submitted reviews when this candidate was prepared). This is an owner review request, not self-approval.
- Complete authenticated checkout into one real local test environment: **BLOCKED** (container DNS cannot resolve GitHub, no exact full repo archive available).
- `npm ci`: **NOT_RUN/BLOCKED** (no approved dependency install, no reviewed wheel/npm supply-chain).
- `npm run typecheck`, `npm run build`: **NOT_RUN/BLOCKED**. Local TS version 5.8.3 is not the locked 5.9.3.
- Desktop/mobile Chromium: **NOT_RUN** without running exact Next.js product. Does not count as official W8 C08.
- W8 PR #38 C07: HOLD; C08: NOT_RUN; independent C05: HOLD.
- Canonical UI 21/40; W8 3/8; both delta 0. Weighted progress HESAPLANAMADI.

## Next, after MI-05 and MI-01 source/lock review
1. Use authenticated Git checkout of the **exact child candidate SHA** in a clean isolated directory. Check `git rev-parse HEAD`, all 555 manifest entries' SHA-256/bytes, no untracked/extraneous product files, and lock blob/SHA against this addendum.
2. Under approved dependency provenance/license rules, `npm ci` **without regenerating the lock**, then `npm run typecheck`, `npm run build` in `product/ai-company-os-frontend`; record exact environment, command, exit code, logs and package tree. Fail closed on mismatch.
3. Run existing React/Chromium desktop and mobile UI tests against exact built product, capture screenshots, console and hydration warnings. Keep the formal W8 C08 separate and gated by official C07.
4. Recheck current PR conflicts (especially shared manifest) and source owner. Only then consider a separately owner-approved fresh-manifest transfer. Do not merge this child DRAFT directly into `product-dev` or main.

## Rollback and scope
Close this child source-review PR or normally revert its isolated commit. The parent PR #39, PR #20, lock-source branch, product-dev, main and all prior tests remain unchanged. Only one new frontend lock file plus matching manifest and review docs/catalog; no W8 runner, API, DB, IAM, ORG, T1, CI or production change. No new CEO architecture decision is necessary; owner sign-off and existing independent release gates remain mandatory.
