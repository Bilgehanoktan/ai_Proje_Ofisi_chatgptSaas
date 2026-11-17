# 0227 D2 — Original PostgreSQL 13 tests

D1 accepted. Use preserved retry2 disposable cluster only. Do not initialize again, change permissions, use shared DB, or alter E1. Verify source HEAD `52219c7a222bae41735c9a9b9f7f7082462982b4`, clean status, original runner Git blob `7cde2a62eee46ce4e682451f82a1c6b3245cf94a`, current manifest `981a13fc226184dc3a911ae0d94e0042285ff302`, D1 review and lock hashes. Existing venv `C:\AIOS\core-0227-pg-retry2\.venv\Scripts\python.exe`. Server bin `server\pgsql\bin`, data `data`. Verify pg_ctl status=3 before start, start own cluster on 127.0.0.1:55432, stop in finally. Confirm test role password locally (never share or log) and explicit EVET for D2. Use process-only DSNs for `aicos_d0_0194_0227` and `aicos_d0_0196l_0227`, user `aicos_d0_runner`, sslmode=disable, connect_timeout=3. Escape libpq DSN backslash/single quote or use psycopg make_conninfo. Set `AICOS_PG_RUN_ACK=0215_DISPOSABLE_LOCAL_ONLY` only for run, clear afterward. Original command:

```powershell
& $py -B "$root\scripts\run_pg_acceptance_0215.py" --root $root --manifest-blob 981a13fc226184dc3a911ae0d94e0042285ff302 --report "$pg\D2_PG13_RESULT.json" --execute
```

Original runner verifies product and DDL pins, rejects remote/unsafe DSN, checks exact suite counts and no skips. Expected 0194=5, 0196L=5, 0200S=3. Report no raw DSNs or credentials. Preserve sanitized report on failure; no automatic retries or schema drop. D2 not run; 13 tests are original and separate from D1 probes. D3 RLS separate, no independent acceptance promotion.


## 0227-D2 — original PG13 execution PASS, raw report pending
Uploaded Windows transcript parsed: 0194 5/5, 0196L 5/5, 0200S 3/3, all failure/error/skip counters zero; exact runner source and 13 source test names reviewed; source/DDL verified; exit 0 and server stopped. Raw D2_PG13_RESULT.json pending. Expected report hash reconstructed, not measured on original. 10/16 unchanged pending review; D3/RLS/B3 open. tests/evidence/D2_WINDOWS_PG13_TRANSCRIPT_0227.json


## 0227-D2 final raw review — PASS
Original Windows JSON: 937 bytes, SHA256 79085656ad4d782a012642518d9d8724514976082af0c5734c5d04dcfb82cf05, exact CRLF serialization and prior transcript match. 13/13 PG cases, source/DDL verified; 11/16 (68.75%). D3 separate RLS/non-owner contention, E2/E3/E4 and B3 open; source unchanged. Evidence: tests/evidence/D2_RAW_EVIDENCE_REVIEW_0227.json; next: docs/0227/D3_RLS_SCOPE_REVIEW.md.
