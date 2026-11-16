# 24 Teknik Alan — TRACK-0227

E1 PASS; 9/16 integration gates (56.25%). Design/source ordinal scores unchanged. Prior selected 307 not rerun; 24 original SQLite tests separately raw-reviewed. Full acceptance remains open.

| ID | Alan | Tasarım | Kaynak | Gerçek test durumu | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_0217_STUDIO_CONTEXT | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 2 | UI/UX Design System | 50 | 50 | PARTIAL_PASS_0217_STUDIO_CONTEXT | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0217_HISTORICAL_LABEL | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0217_SIGNED_FIXTURE | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_ORIGINAL_0224_SQL8_RAW_REVIEWED | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0217_SIGNED_FIXTURE | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_0210_DENIAL | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0217_LOCAL_SQLITE_DDL_PINS | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0211_COMPONENT_CLAIM | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 13 | Memory & Knowledge | 75 | 25 | PARTIAL_PASS_ORIGINAL_0221_SQL10_RAW_REVIEWED | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0217_SIGNED_FIXTURE_RESTORE_RESIDUAL | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0205R_POOL | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 20 | Test & QA | 75 | 25 | E1_PASS_ORIGINAL24_RAW_REVIEWED_FULL_REGRESSION_OPEN | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 21 | DevOps & Infrastructure | 75 | 25 | E1_PASS_WINDOWS_REVIEWED_LOCKS_PG_BUILD_OPEN | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0217_RESTORE_RESIDUAL | 0227_CARRY_FORWARD_NO_SCORE_PROMOTION |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | 0227_E1_RAW_REVIEWED_ORIGINAL24_PASS |

Historical MD preserved in Git history. Current evidence: tests/evidence/E1_RAW_EVIDENCE_REVIEW_0227.json


## 0227-D1 — Windows inventory checkpoint
No PostgreSQL commands, default Program Files directory, service or Psycopg packages found in user checks. Proposed PG17.12 and Psycopg3.3.9 Windows cp314, separate loopback-only D0 stage. Candidate download and hash/provenance review pending; no install, DB, test or gate promotion. E1 remains accepted and unchanged, 9/16. Evidence: tests/evidence/D1_WINDOWS_INVENTORY_0227.json.


## 0227-D1 — candidate downloads and connection runner
Server ZIP checksum matches EDB (user transcript); Psycopg/psycopg-binary/tzdata downloads successful. Public PyPI hashes verified for pure Psycopg and tzdata; local JSON API exact check required for binary. New pinned scripts/run_d1_0227.py uses reviewed E1 wheelhouse read-only, new 31-package lock, disposable loopback-only SCRAM cluster, two non-superuser/non-BYPASSRLS DBs, write/read/rollback and graceful stop. Linux syntax/fixture checks only; no Windows execution or new gate. 9/16 unchanged; PG13/RLS pending. Evidence: tests/evidence/D1_WINDOWS_WHEELS_READY_0227.json.
