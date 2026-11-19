# MI-COMMON-09 — Windows temporary path blocker; no architecture or product source change

2026-11-20. **HOLD.** Source: user-provided PowerShell transcript; raw attached-log SHA-256 `df3097e018707c7b9a08d9047243636c1ae5aca6a86cac52df43b5ec84aa9416`. This is observed user console output, not independently repeated Windows verification.

## Test state
Pinned private Python 3.13.5 / SQLite 3.46.1 / cryptography 46.0.4, cffi 2.0.0 and pycparser 2.23 imported successfully; 3/3 PyPI wheel SHA-256 checks reported PASS. Original source pins 114/114. The first MEM group **ran 184 tests and reported 157 errors**; the runner ended `TOTAL_PASSED_GROUP_TESTS=0`, `EXIT_CODE=1`. The four subsequent groups 80 + 16 + 28 + 36 were **NOT_RUN**. This is not a 344-test PASS.

## Technical diagnosis
The traceback passes through `product/ai-company-os-backend/app/engines/memory_engine/snapshot_store.py::_path()` to `ValueError('MEMORY_SNAPSHOT_PATH_HOLD')`. Temporary path in the traceback uses Windows user-directory short-name syntax. The existing `p.resolve() != p` canonical-path guard may reject that alias. This is a *hypothesis* until path preflight and rerun; do not relax the guard.

The original `docs/master-integration/MI-07-08-JOINT-TRANSFER/run_combined.py` uses `tempfile.TemporaryDirectory` and sequential groups. Its source and snapshot-store Git blobs at source commit `87272b6aebd1ce4b26d3a789b2ea75e4310cf60a` are `6536c6571f5f9b3b3059bbd7e0ebc3089bc252bb` and `bc8cd58a5e58a9043d5bf188af11521b1641b9c7` respectively.

## Controlled retry and rollback
A **local-only, unexecuted** PowerShell retry script was delivered to the owner: `MI_COMMON_09_TEMP_PATH_RETRY.ps1`, SHA-256 `c649752f1c1ca205bc4e1ecd58fe06b9e883a648f0875e1365fd3c9d4fb56170`. It reuses existing isolated Python and original source runner, sets process-local TEMP/TMP/TMPDIR to a new ASCII-only evidence folder, runs a canonical-path preflight, restores environment variables, and leaves the prior failed stage intact. It performs no installation, source mutation, CI run, protected commit or production action. The new log/JSON must be examined before changing any PASS status. On failure retain HOLD; revert by removing only the new retry directory *after* evidence preservation.

No Design Master, product source, public API, DB schema, dependency pin, class, function or security architecture change is made. `integration/product-dev` remains at `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`; joint candidate not promoted.

## Metrics
MI-07 development percentage: not computable from unfrozen evidence criteria, unchanged. MI-08 last recorded development percentage: 45%, delta 0. Product acceptance: unchanged, zero newly evidenced accepted criteria. Core29, full W8, browser, real PostgreSQL protected IAM–ORG–T1 and independent acceptance remain distinct NOT_RUN/HOLD gates. Repeat tests are not counted twice.
