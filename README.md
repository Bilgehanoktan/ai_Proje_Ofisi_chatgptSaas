# W1-0198-P05 — immutable fixture recovery transport

TRANSPORT ONLY — NEVER MERGE. This tree is deliberately a minimal 44-file subset of P04, not a replacement product branch. Parent: 4ead00903f34e0226f0ca6475c89aaeacb9de364. All original source files are reused by Git blob identity. No product code changed. The three P05 helper scripts and pinned lock are separate additions.

From the extracted archive root, with an existing Python >=3.10, SQLite >=3.37 and FastAPI installed:

```
python tests/integration/run_lifecycle_p05.py --source . --report lifecycle-p05-evidence.json
````

No dependency installation, CI, actual provider call, production or real PostgreSQL. Runs only P02 8 and P03 9 selected SQLite fixture/direct API handler cases; report PASS only if all 17 run and pass without skips. Package prepared on GitHub; actual 17 cases NOT_RUN in the current environment due local source transfer blocker. No guarantee of successful run before evidence. Full P04 and later product branches remain separate.
