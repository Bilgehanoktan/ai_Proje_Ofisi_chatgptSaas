# MI-COMMON-04 — Pinned source recovery and regression handover

Source of truth: `integration/mi-common-source-review-01` commit `61bb06efbba7544bfc68260ed8eb4d342cab9b8e`; unchanged product manifest `03af243e8683f92c5d9c0b24e90b70d2bd6af29f`. Security: CEO-0174/0179=B. This recovery helper adds **no** product/runtime/DB/API change and cannot authorize protected COMMIT, installation, CI, external providers, main merge or independent acceptance.

## What is implemented and actually verified

`pinned_source_recovery.py` retrieves exact content-addressed GitHub **blob SHA** sources, verifies SHA256 when present, writes to an immutable cache and atomically promotes a fresh isolated stage only when all pins pass. It does **not** auto-run tests, install dependencies, regenerate npm lock, or start servers. `--offline` denies any cache misses without a network request. `test_pinned_source_recovery.py`: 14/14 synthetic helper tests PASS, Python 3.13.5, exit 0; real fixed-file Git blob vector and one authentic old blob validated. Initial helper incorrectly required SHA256 on all entries; corrected after original pins revealed **28/114 Model/Memory** and **6/55 historical Core** entries have only Git blob SHA1+size. Original source pins unchanged. Never invent missing SHA256.

Remote repository metadata: 114/114 Model/Memory paths match current common blobs/sizes; 55/55 historical Core blobs/sizes available via current or historical overlay; 17/17 shared frontend/backend schema/fixture pairs. Remote complete source is **not** a local complete source. Only five *distinct* old blob bytes from uploaded legacy archives were available in current local cache, matching five of the 114 and five of the 55 pinned paths; no 344/29 test has been executed in this turn.

**Important historical collision:** 26 same-path source references shared across Model/Memory and historical Core; 24 byte-identical, **two differ** (`scheduler_review.py` and `postgres_admission_mapping.py`). Both sets must be materialized in separate stage roots. Historical `0207` original runner also maintains its own exact helper and direct dependencies.

## How to recover (only on a machine with approved GitHub access)

Keep all previous checkout/Windows directories untouched. No PC work was requested in this session. For a future approved host, use a **new** stage path and a reviewed token in `GITHUB_TOKEN` or `GH_TOKEN` environment only if repository access requires it; never pass a token on the command line. The tool fetches only `/repos/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/git/blobs/{SHA}` from `api.github.com`, rejects redirects, checks all hashes before writing, and prevents overwrite:

```powershell
py -3 -B pinned_source_recovery.py --cache C:\AIOS\MI04-cache --stage C:\AIOS\MI04-stage --mode both --evidence C:\AIOS\MI04-report.json
```

An offline cache preflight uses `--offline` and **must** report HOLD while pins are missing. Do not interpret a remote catalog check or metadata-only PASS as local source recovery.

### Run existing original tests after complete verified recovery

**Model/Memory 344:** exact original runner, not a new reimplementation. Requires Python **3.13.5**, SQLite **3.46.1** and cryptography **46.0.4**, and all 114 original source pins:

```powershell
py -3 -I -B C:\AIOS\MI04-stage\model\docs\master-integration\MI-07-08-JOINT-TRANSFER\run_combined.py
```

Expected five groups: Memory 184, W5-A-F without duplicate router 80, W5-G 16, W5-H 28, W5-I 36. All 344 unique test IDs, no fail/skip, original source postcheck, `TOTAL_PASSED_GROUP_TESTS=344` and `EXIT_CODE=0` required. If a pin or version does not match: HOLD without changing original reference or borrowing another environment.

**Historical Core 29:** exact original `run_core_0207.py` with 55 historical files. Run `--check-only` first; this verifies sources but is **not** a test PASS. Real test mode requires reviewed exact direct dependencies **FastAPI 0.163.0, Starlette 1.10.0, cryptography 46.0.4, Uvicorn 0.34.2** and separately reviewed transitive dependencies. Current chat container has FastAPI **0.128.2**, Starlette **0.50.0**, Uvicorn **0.48.0**; no attempt to bypass version gate:

```powershell
py -3 -I -B C:\AIOS\MI04-stage\core\tests\integration\run_core_0207.py --source C:\AIOS\MI04-stage\core --report C:\AIOS\MI04-core-source-only.json --check-only
# Later, only with reviewed pinned environment and a *new* report path:
py -3 -I -B C:\AIOS\MI04-stage\core\tests\integration\run_core_0207.py --source C:\AIOS\MI04-stage\core --report C:\AIOS\MI04-core-29.json
```

## W8/build/browser policy

Only the original common W8 adaptor `tests/integration/w8_mi_common_02.py` is eligible. Its current 538-path source manifest and original 33,618-byte npm lock are pinned. The old base runner's `npm install --package-lock-only` is replaced by exact copy of the original lock in the separate adaptor; **do not run the legacy prepare directly**. Full exact checkout and reviewed direct/transitive npm+wheel provenance, new REVIEW.json fingerprint approval, locked install, full Next build+`tsc --noEmit`, original 344+29 and U3 browser/loopback still NOT_RUN. Original lock contains 61 non-root packages (static npm registry/SRI checks only; actual tarballs/audit not verified). No W8/Chromium launch until these gates pass. In a future connected, owner-reviewed checkout:

```powershell
py -3 -I -B tests\integration\w8_mi_common_02.py audit
py -3 -I -B tests\integration\w8_mi_common_02.py prepare --stage C:\AIOS\new-exact-review-stage
# Stop. Inspect and approve fresh dependency inventory and original lock before install.
```

## Defects, diagnosis, rollback, ownership

- `CACHE_MISS_OFFLINE`: source data not available locally; authenticated GitHub read required; do not repin/fill with unrelated previous archive bytes.
- `SOURCE_BLOB_MISMATCH`, `SIZE_MISMATCH`, `SHA256_MISMATCH`: stop, preserve original cache for analysis, compare immutable source commit and exact pin map.
- `HISTORICAL_OVERLAY_SCOPE_HOLD`: compare 26 overlap paths, keep separate historic source; owner review required if count changes.
- `DIRECT_DEPENDENCY_PIN_MISMATCH`: hold the historical 29 tests; no unpinned diagnostic acceptance.
- `GITHUB_FETCH_HOLD`: DNS/network inaccessible in this ChatGPT container; use a separately permitted connected host, not CI or production.
- Any failure leaves `*.partial` separately and never promotes an apparently complete stage. Preserve logs; delete or retry only after inspection. No database rollback is involved.

Owner lanes MI-07 Model, MI-08 Memory, MI-01 Unified build, MI-02 Core/PG, MI-03/04 IAM/T1 remain separate. Full product and independent acceptance remain HOLD. The existing product-dev SHA and common source SHA are not modified by this recovery helper. Normal revert of candidate helper commit is rollback; no force-push or security permission changes.
