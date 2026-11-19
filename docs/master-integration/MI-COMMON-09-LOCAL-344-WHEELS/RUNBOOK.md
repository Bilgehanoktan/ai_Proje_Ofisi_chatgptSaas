# MI-COMMON-09 — isolated native Windows wheel bridge for original Model/Memory 344

This workstream follows the successful user Windows preflight: source archive full Git tree SHA `187f652f1b1ff8604981833f634c4531a33f8a47`, 1,953/1,953 files; exact pinned Model 114/114 and historic Core 55/55 source-only checks; isolated private Python 3.13.5 / SQLite 3.46.1 from `P0_ENV_3135_3461_20261120_004854`. Prior original 344 attempt was HOLD before tests because global Python 3.14.3 SQLite 3.50.4 or missing cryptography metadata. Do not count as product test PASS.

## Files and security boundary

- `MI08_MODEL344_PINNED_WHEELS.ps1` — Windows PowerShell 5.1 only; user must paste **reviewed full script text** into PowerShell, not change execution policy or run unsigned file directly. Code triggers new separate folder and asks `EVET` before any new file/network actions. It never modifies the frozen source, original private Python or system Python.
- `.ps1` uses host `py -3 -m pip` only to select and download exactly three binary packages for a target platform **CPython 3.13 Windows x64**, not the host Python 3.14 wheels. The three packages and versions are `cryptography==46.0.4`, `cffi==2.0.0`, `pycparser==2.23`. It resolves from official `https://pypi.org/simple`, then verifies SHA256 against official `https://pypi.org/pypi/<package>/<version>/json` for each actual wheel; no sdist/build. From **offline** `--no-index --find-links`, pip installs only into a private `--target`. The copied portable interpreter adds `_modeldeps` to its private `python313._pth` (not `PYTHONPATH`, because embedded Python ignores it).
- Verifies CPython 3.13.5, SQLite 3.46.1, cryptography 46.0.4, cffi 2.0.0, pycparser 2.23, native backend import, SHA256 primitive; only then original unchanged `run_combined.py` executes. Original runner enforces 114 source pins pre and post, exact reference environment and five distinct groups of 344 test IDs. `MODEL_344_RESULT.json` status `PASS_344_OF_344_SELECTED_REGRESSION` is possible only when original runner exit is zero and output contains both source-pin checks, `TOTAL_PASSED_GROUP_TESTS=344`, `EXIT_CODE=0`, and `PRODUCT_ACCEPTANCE=HOLD`. No product acceptance granted.

## Tests actually performed here

Synthetic pip wheel `demo_safe-1.0-cp313-cp313-win_amd64.whl` successfully installed with host pip using cross-target `--target` + `--platform win_amd64 --python-version 3.13 --implementation cp --abi cp313 --abi abi3 --abi none` into a private temp directory; this is **not** cryptography wheel verification or Windows execution. 16/16 static code presence/safety gates PASS; Windows PowerShell parser and actual Windows runner **NOT_RUN** in this chat. Official PyPI cryptography 46.0.4 metadata and Windows embeddable Python `._pth` behavior checked via current external sources. No wheel was downloaded by this chat container. No source or dependency pin changed.

## Failure diagnoses and recovery

- `HOST_PIP_NOT_AVAILABLE_HOLD`: global host Python 3.14 lacks pip. Halt; do not bootstrap by unverified scripts or use alternative interpreter blindly.
- `TARGET_WHEEL_DOWNLOAD_HOLD`: network or target compatibility. Keep wheelhouse diagnostics; do not choose host cp314 artifacts.
- `WHEEL_NAME_NOT_PINNED_HOLD`, `PYPI_FILE_METADATA_HOLD`, `PYPI_WHEEL_HASH_HOLD`: reject unknown or changed wheel hashes; do not substitute repacked source.
- `TARGET_WHEEL_INSTALL_HOLD`: pip cannot install into `--target`; inspect pip error before rerun. Never run global `pip install`.
- `PRIVATE_ENVIRONMENT_IMPORT_VERSION_HOLD`: wrong original versions or ABI incompatibility. Preserve original runtime and inspect private `_modeldeps` only.
- `TEST_FAIL_OR_HOLD`: inspect original test stdout+stderr log and verify output markers; do not count synthetic preflight as PASS.

User shares `MODEL_344_RESULT.json`, `MODEL_MEMORY_344.log`, `WHEEL_SHA256.json` and `ENVIRONMENT_PRECHECK.json` after local run. All commits made only to isolated candidate/governance logs; `integration/product-dev` remains frozen and product acceptance/weighted progress unchanged. Historical Core29, full W8 Next build, browser, protected COMMIT, independent IV remain HOLD or NOT_RUN. Rollback: retain logs, remove **only** new local `P0_MODEL_344_PINNED_*` folder after review. Repository rollback: normal non-force revert of candidate documentation commit.
