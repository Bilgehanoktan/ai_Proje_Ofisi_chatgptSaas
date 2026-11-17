# DOC-REV-0227 — MVP environment preflight (BLOCKED)

Pinned 0226 parent c715e1edfd1af021b4c0be0681c6958455b6a26f. No runtime/product changes, no new prototype or tests. Existing CEO-0174/0179=B boundary remains unchanged. Repo branch readback, exact manifest path/size 392/392, no missing/extra; 393 product files; 1571 repo blob paths. Historical lock at 614aa63efbd0a95d0fa5fe47390df043d773370f: 55/55 Git blob and size matches remotely, current source 52/55 (three expected changed paths), no local source execution. See [environment evidence](../../tests/evidence/TEST_EVIDENCE_0227.json).

Local network probes: git DNS failure exit 128, pip dry-run exit 1 and npm registry metadata exit 1; separate DNS queries all exit 2. Published exact versions were found on public package indexes, so the local resolver error does not prove the pins are unavailable. No transitive lock, installation, PostgreSQL, full checkout or build produced. The existing 307 selected passes are historical 0226 only, not rerun. A3, D1-D3, E1-E4 open, B3 HOLD. 7/16 unchanged. Do not substitute new package pins, change historical lock or infer independent acceptance.

Operational next: [connected workstation runbook](CONNECTED_WORKSTATION_0227.md). Execute source/lock preparation and original residual suites in an actual connected authorized isolated environment, then PG and build/browser. No new user-level authorization requested. No CI or main changes. This revision does not represent a working MVP.


## 0227-A3 — scoped historical evidence transfer
A3 only: 29/29 historical locked tests from pinned A0F review `6140e16edb2ddd943912908f3714ccd3a211b1d3`, actual A0C source `a79df6622e2eb9de63795ff6c0309984d1be6910`; 55/55 source lock, same exact lock/runner/helper, reviewed Python lock and report hashes, four raw markers checked in prior review. Current product is unchanged. No new local execution, no independent replay; raw Library ZIP materialization unavailable in this session. 8/16; 307 historical selected tests unchanged, no additive count. E1, D1-D3, E2-E4, B3 open. P10J15 exact three original test blobs match, but no execution or merge. Evidence: tests/evidence/A3_EVIDENCE_TRANSFER_0227.json.


## 0227-E1 — reviewed-lock reuse execution packet
scripts/run_e1_0227.py reuses original W8 lock inventory, exact A0C hash/wheels and a fresh source-bound review. It copies only pinned product and DB source into a new stage, installs Python offline with hash verification and npm ci with scripts disabled, runs original 6/10/8 suites with exact collection and exit counts. 10/10 synthetic runner mechanics PASS; Windows prepare/execute NOT_RUN and zero product tests. 8/16 unchanged. No runtime/product changes, no CI, no merge. If A0 raw wheel/lock bytes unavailable or mismatch, stop; retain failed stage, use separately reviewed recovery. Evidence: tests/evidence/E1_RUNNER_MECHANICS_0227.json.


## 0227-E1 Windows prepare review
User Windows prepare reports success. 16 DB pins match remote; reconstructed sorted CRLF new and A0 origin review hashes both match. No new source or product execution; install and 24 tests pending explicit local approval. 8/16 remains. Evidence: tests/evidence/E1_WINDOWS_REVIEW_0227.json.


## 0227-E1 Windows execution transcript
User explicitly approved new fingerprint and ran the isolated Windows stage. Six install/inventory commands and original 0219/0221/0224 suites exited zero; runner reported 24/24 PASS after source/lock rechecks. Actual SQLite D0 execution reported, not independent replay. Raw reports/logs/locks pending; E1 gate remains open, 8/16. No additive test aggregate, no product/source changes. Evidence: tests/evidence/E1_WINDOWS_EXECUTION_TRANSCRIPT_0227.json.


## 0227-E1 final raw review — PASS
User-uploaded raw ZIP 14/14 CRC, 9/9 report log hashes, 28 Python wheel/installed versions and 61 npm lock entries, 30 installed versions, 24 original test names match source and all pass. Two extraneous npm packages are exact optional lock entries; E3 recheck. No raw wheel binaries or independent replay. E1 closed, 9/16 (56.25%); product and DB source unchanged; prior 307 count separate. D1/D2 next; D3/E2/E3/E4/B3 open. Evidence: tests/evidence/E1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D1 — Windows inventory checkpoint
No PostgreSQL commands, default Program Files directory, service or Psycopg packages found in user checks. Proposed PG17.12 and Psycopg3.3.9 Windows cp314, separate loopback-only D0 stage. Candidate download and hash/provenance review pending; no install, DB, test or gate promotion. E1 remains accepted and unchanged, 9/16. Evidence: tests/evidence/D1_WINDOWS_INVENTORY_0227.json.


## 0227-D1 — candidate downloads and connection runner
Server ZIP checksum matches EDB (user transcript); Psycopg/psycopg-binary/tzdata downloads successful. Public PyPI hashes verified for pure Psycopg and tzdata; local JSON API exact check required for binary. New pinned scripts/run_d1_0227.py uses reviewed E1 wheelhouse read-only, new 31-package lock, disposable loopback-only SCRAM cluster, two non-superuser/non-BYPASSRLS DBs, write/read/rollback and graceful stop. Linux syntax/fixture checks only; no Windows execution or new gate. 9/16 unchanged; PG13/RLS pending. Evidence: tests/evidence/D1_WINDOWS_WHEELS_READY_0227.json.


## 0227 D1 initdb HOLD
User transcript confirms all 3 PyPI checks and reaches postgres 17.12/initdb after 31-pin installation sequence. Password mismatch aborts initdb; rerun intentionally refused by fresh-stage guard. Preserve failed stage; copy only ZIP and wheels to new sibling stage and repeat isolated D1. No connection or PG13/RLS test; 9/16 unchanged. tests/evidence/D1_WINDOWS_INITDB_HOLD_0227.json


## 0227-D1 retry1 connection HOLD
User reports initdb and PostgreSQL start/stop successful, child OperationalError masked by runner; exact failing statement unknown. No D1 acceptance. Preserve retry1 and diagnose with interactive read-only psql connection and role/database existence checks, then stop own cluster. No password or private log transfer; no reinstallation or grants. 9/16. Evidence: tests/evidence/D1_WINDOWS_RETRY1_CONNECTION_HOLD_0227.json


## 0227-D1 authentication diagnosis and candidate fix
User psql diagnostic starts server, reaches loopback 55432, FATAL password authentication failed (exit 2), stops successfully. Exact mismatch cause unknown. New scripts/run_d1_0227_authfix.py generates ephemeral ASCII admin, restricts and verifies temporary pwfile ACL before writing, removes file in finally, sends same credentials to child via stdin; SCRAM preserved; test password user-held. Compile and four synthetic controls PASS; Windows not run. Retry2 fresh input-only copy; old stages preserved. 9/16 unchanged. tests/evidence/D1_WINDOWS_AUTH_HOLD_AUTHFIX_0227.json


## 0227-D1 retry2 connection PASS — raw review pending
User transcript: PG17.12, Psycopg3.3.9 binary, libpq180004, SCRAM loopback 55432, two separate DBs with non-superuser/non-BYPASSRLS test role; both write/read/rollback PASS; source before/after match, server stopped. Existing input-directory/copy errors preceded successful runner preflight; retain anomaly and do not rerun install. Raw evidence pending; 9/16 unchanged; PG13 and RLS NOT_RUN. tests/evidence/D1_WINDOWS_CONNECTION_TRANSCRIPT_0227.json


## 0227-D1 final raw review — PASS
Raw ZIP 8/8 CRC, 5/5 log/report hashes, 31/31 installed pins, original 28 E1 lock lines exact from reopened E1 archive, two PostgreSQL DB probes PASS; SCRAM loopback and stopped state evidenced. D1 accepted, 10/16 (62.5%). No independent replay, raw binaries absent, PG13/RLS/build open. Source unchanged. Next: docs/0227/D2_PG13_RUNBOOK.md. Evidence: tests/evidence/D1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D2 — original PG13 execution PASS, raw report pending
Uploaded Windows transcript parsed: 0194 5/5, 0196L 5/5, 0200S 3/3, all failure/error/skip counters zero; exact runner source and 13 source test names reviewed; source/DDL verified; exit 0 and server stopped. Raw D2_PG13_RESULT.json pending. Expected report hash reconstructed, not measured on original. 10/16 unchanged pending review; D3/RLS/B3 open. tests/evidence/D2_WINDOWS_PG13_TRANSCRIPT_0227.json


## 0227-D2 final raw review — PASS
Original Windows JSON: 937 bytes, SHA256 79085656ad4d782a012642518d9d8724514976082af0c5734c5d04dcfb82cf05, exact CRLF serialization and prior transcript match. 13/13 PG cases, source/DDL verified; 11/16 (68.75%). D3 separate RLS/non-owner contention, E2/E3/E4 and B3 open; source unchanged. Evidence: tests/evidence/D2_RAW_EVIDENCE_REVIEW_0227.json; next: docs/0227/D3_RLS_SCOPE_REVIEW.md.
