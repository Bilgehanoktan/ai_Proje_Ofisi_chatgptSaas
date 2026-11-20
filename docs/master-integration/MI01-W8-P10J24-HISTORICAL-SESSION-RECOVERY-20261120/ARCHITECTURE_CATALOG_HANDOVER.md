# MI-01 W8 C04 — exact P10J24 historical PostgreSQL session source recovery
**2026-11-20 · draft/review only · no product/security acceptance**

## Observed failure / diagnosis
Windows PowerShell 5.1 C04 execution after successful authenticated preflight `552/552` product SHA-256, `6/6` owner blobs, npm lock SHA-256:
```
START C04: verified original PR20 source, wheel downloads only
HOLD: P10J24_HISTORICAL_AUX_HOLD: tests/integration/historical_0207/app/core/transaction/postgres_session.py
STATUS: HOLD
```
User console evidence only: `E:\AIOS\W8\W8_PR20_20261120_211752\C04_RUN_RESULT.json` not yet uploaded. The W8 `prepare` failed in **original source auxiliary preflight**, before package downloads or W8 install; this is **not a Python/npm test failure**.

The original `tests/integration/w8_p10j24.py` Git blob `0728ba08494bb8d67c7cec42fe27dd8606bdc7f3` implements `verify_aux_candidate()`, and fails closed if any path declared in `HISTORICAL` is missing or differs by exact Git blob. The `tests/integration/w8_unified_u3.py` owner adapter blob `b4043035e75c5a18b7b19a9f18eecfef8e8fe677` adds the original historical `postgres_session.py` pin `8e65e4575a77b11c38c2d2e62ec91fc89d75e23c`, but PR20 only tracked the previous three historical paths. The source lock `tests/integration/core_0207_source_lock.json` blob `223f6fbd28cf4c428c07eb60dda4a36f644fa58c` declares 55 files with `source_commit=614aa63efbd0a95d0fa5fe47390df043d773370f`, including expected historical PostgreSQL session file **2,495 bytes**, SHA-256 `99846c47151ccce5dc9a49c8fcf442c73f2e537fb4365c4e2e59f01d041d25cb`.

Current **product** `product/ai-company-os-backend/app/core/transaction/postgres_session.py` blob `6c0995712bd368f72c239cb19cd3e85aa781c1b9` is a different later version and must **never replace** the historical original.

## Source-only exact recovery, ownership, provenance
- Baseline existing owner: [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20), SHA `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`; baseline `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` unchanged.
- Isolated review branch: `review/mi01-w8-p10j24-historical-session-recovery-20261120` created directly from **exact PR20 head**, without changing PR20 or rebasing.
- Exactly one recovered W8 **non-product** source: `tests/integration/historical_0207/app/core/transaction/postgres_session.py`, content read from GitHub original blob `8e65e4575a77b11c38c2d2e62ec91fc89d75e23c`, new GitHub readback matched same **exact blob**. No change to W8 source code, tests, dependency versions, locks, product manifest, DB, API or CI.
- PR20 → review candidate code delta: exactly **one added historical fixture**, 2,495 bytes, 69 lines; original `product` Git tree remains `f4cdcf68115917ab69ba6441414539fe32a59369` (553 product files, 552 manifest entries). Nothing in `product/` changed.
- Full historical source target map checked against GitHub untruncated recursive tree and **each exact original 55-lock record**: 4/4 `historical_0207` files now exist at their exact mapped Git blobs, zero mismatches.
- This makes the specific preflight blocker structurally satisfiable. **Actual Windows W8 `audit`/C04 `prepare` of the candidate are not yet executed.** Any other failure remains explicit HOLD until reproduced and fixed; do not imply C04 PASS.

## Windows C04 source selection and acceptance boundaries
The user has an existing authenticated, exact PR20 shallow Git working directory on E:, already source-verified. The controlled Windows continuation should **fetch this isolated review branch using Git Credential Manager**, verify its expected commit SHA, confirm the product tree Git SHA did not change, verify all 4 original historical blob pins and complete 552/552 source manifest, and run the owner's original `w8_unified_u3.py audit` before `prepare`. No new full source clone or changed W8 implementation. Preserve source-only PR20 report as historical; label later results as **REVIEW_VARIANT**, never misattribute them to unmodified PR20. Use fresh stage and isolated E: pip/npm/TEMP caches. The owner must approve recovery before it can replace the canonical owner W8 packaging.

Independent dependency C05 remains HOLD; no install/test/smoke, no real PostgreSQL/root/sink/IV, no system-wide execution-policy change, no permissions or main/PROD. The first failed stage is preserved as evidence, not force-cleaned or overwritten.

## Catalog / failure recovery / next owner action
- File: `tests/integration/historical_0207/app/core/transaction/postgres_session.py`; symbol/class history: `CommitOutcomeUnknown`, `PostgresSession` restored **historical original**, not the current product class.
- Reader: original `w8_p10j24.py::verify_aux_candidate`, `materialize_history`, `w8_unified_u3.py::load_candidate`.
- Data provenance: `core_0207_source_lock.json::files[postgres_session.py]` original 55-lock + source commit, owner PR20.
- New API/DB/event/dependency/test-runner/CI/rights: **none**. No numeric acceptance credit; W8 previous/current **3/8**, C04 NOT_RUN (attempted but preflight failed), C05 HOLD, C06–C08 NOT_RUN, MVP 0/11, independent IV 0/7. Weighted 15/35/20/20/10 global HESAPLANAMADI.
- Rollback: close review PR or normal revert the one fixture addition. For Windows, retain PR20 source HEAD and restore it with `git switch --detach 99571c...` only after staging results are preserved; never use `git clean -fdx` or delete prior stage evidence. No force push.

**Owner requested:** MI-01/Unified review byte-exact original historical source, confirm 4/4 map and local `audit`/C04 candidate run, then decide controlled incorporation into PR20. Do not automatically merge.
