# MI-COMMON-07-MODEL344-CRYPTO-ENV-HOLD — dependency and execution catalog

Original file: `docs/master-integration/MI-07-08-JOINT-TRANSFER/run_combined.py`, original source `integration/mi-common-source-review-01` commit `bd57cc8235a13ba5bf10545a7879be98fd7b47f5`.
Python 3.13.5, SQLite 3.46.1, cryptography 46.0.4 hard-coded exact equality in `main`; metadata read through `importlib.metadata.version`; original selected 344 cases remain NOT_RUN when metadata missing. No code, symbol, API, DB, schema or event change. Never repin. `tests/integration/run_core_0207.py` retains separate 55 source lock and four direct dependency pins. Safe maintenance: new isolated venv only, inspect PyPI registry/wheels, freeze installed versions, preserve logs, delete venv to roll back.
