# MI-01 W8 / 553 — Avoid cross-chat collision and unblock manifest binding
**20 Nov 2026.** This is an isolated runner compatibility REVIEW candidate, **not** a complete W8 execution or acceptance.

## Cross-chat / ownership audit
- `MI-01 Unified` owns frozen source+dependency+full W8; MI-10 owns approved narrow diagnostic CI. The central MI-01 W8 operational register remains **3/8 PASS**: full checkout, original 539 audit, original npm lock only. Dependency prepare, provenance review, install, test and smoke are NOT_RUN/HOLD.
- Existing PR #14 is **open draft** for 505→553 source promotion (not merged, not full W8). CI #44628704044 tested ORG packaging/SQL only (15/15), not the full W8 chain. Nothing proves that a *different conversation is currently running* full 553 W8; GitHub evidence does prove it is **not yet completed**.
- Review branch `review/mi01-w8-553-manifest-bridge-20261120` extends source commit `a80932b6d5e99667889dfaa25b682feb267c6cba` without modifying this owner branch or old tests.

## New verified blocker
- Original W8 `tests/integration/w8_mi_common_02.py` Git blob `acd361f17331f512ce35a1611e8108d32e61680f` hard-pins 539 manifest Git blob `03af243e8683f92c5d9c0b24e90b70d2bd6af29f`.
- Common 553 owner candidate `a80932b6d5e99667889dfaa25b682feb267c6cba` has 552-entry manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`. Running the old adapter unchanged against this candidate would reject the source identity at its explicit `MI02_MANIFEST_HOLD` guard.
- Review candidate `tests/integration/w8_mi_common_553.py` checks the exact old adapter Git blob, rejects symlink/edited parent, binds only the new manifest, then invokes original nested W8 source / dependency / approval / test / browser gates. Original adapter and product code remain untouched. No authority, test, dependency or security gate bypass is intended.
- Six synthetic adapter tests ran in container Python 3.13.5: **6 PASS/0 FAIL/0 SKIP**. They test parent/missing/drift/symlink, mismatch rejection and manifest-only override; **they are not any of the original W8 or full product tests**.
- Test branch commit `ebee7053f55e9c3dd1c70053a2c3244929723906`. Two exact Git blobs: wrapper `e6e2d570f7fe935b3b00f514c6e8452a08eff261`, helper tests `f0fae186b350e7b20f618cfaa07a1a2070922579`. The local zipped reference SHA256 `6bdca1ce6fe7fe23f87761a45dbca1506a18f877f83ff00a7a8961677a1dcb63` remains available in current conversation.

## Blocked real validation
- This isolated assistant runtime does not possess a complete 553 checkout and GitHub archive cannot be downloaded via its git/DNS; no reviewed PyPI/npm wheelhouse and dependency owner fingerprint exist. Therefore **W8 prepare, install, full backend+Node/Next/TS test/build, original U3 Chromium/52-capture smoke all NOT_RUN**. No full original W8 PASS or build claim is made.
- `MI01-W8-C04` remains NOT_RUN, C05 HOLD_OWNER, C06-C08 NOT_RUN. Local synthetic 6/6 does not change operational 3/8, weighted project development percentage, canonical product or independent security acceptance.

## Technical catalog, ownership, recovery
- New code paths in **isolated review branch only**: `tests/integration/w8_mi_common_553.py` (functions `git_blob`, `load_pinned_parent`, `load_candidate`), `tests/integration/test_w8_mi_common_553.py` (6 Python unittest methods).
- Existing production code / class / API / SQL / event / schema / manifest / dependency source changes: **zero**; root schema and security contracts untouched.
- Owner MI-01 must verify the wrapper against the full exact 553 checkout and review lock/REVIEW/fingerprint before running original install/test/smoke. Do not enable CI beyond existing narrowly authorized PR #4/#6; no new workflow/PR produced here.
- Rollback: delete review branch or normal revert of review commit; revert this governance entry if contradictory evidence appears. Previous source candidate, product-dev/main, previous test evidence and user Windows logs preserved.
- Next action: MI-01 owner reviews lock/wheelhouse provenance, hashes, licensing and vulnerability; exact 553 full audit through this candidate; after explicit owner ratification original W8 prepare → install → test → browser smoke.
