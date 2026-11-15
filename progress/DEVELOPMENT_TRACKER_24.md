# 24 Teknik Alan — TRACK-0205-R

Ordinal olgunluk puanları, tamamlanma yüzdesi değil. 148 seçili PASS (43 yeni,105 regresyon); tam T1, 12 önceki entegrasyon ve 13 PG NOT_RUN. Bağımsız witness ve kabul HOLD.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | Prior evidence retained, not rerun |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | Prior evidence retained, not rerun |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | Prior evidence retained, not rerun |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Prior evidence retained, not rerun |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0205R_RECOVERY | Read-only checkpoint and pending transaction recovery |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Prior evidence retained, not rerun |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Company roster/history hash and exact readback; no automatic restart |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0205R_QUARANTINE | No replay or grant refresh for unknown transactions |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | Prior evidence retained, not rerun |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior evidence retained, not rerun |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0205R_SQLITE | Separate local witness CAS and actual SQLite backup/reopen; PG open |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Company sequence, digest and monotonic witness |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0205R_PIN | Stale/tampered witness rejection; independent root unproven |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | External reference prerequisite; no independent issuance or publication |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Prior evidence retained, not rerun |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior evidence retained, not rerun |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0205R_POOL | Checkpoint binds caps and pool state; no spend or real accounting |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0205R_SELECTED | 43 new +105 rerun selected PASS; earlier integration/PG NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | Local exact checkout DNS failure, actual PG unavailable |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior evidence retained, not rerun |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0205R_RECOVERY | Actual backup and read-only recovery fixture; W-A independent custody HOLD |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture, source, tests, catalog, tracker and handover updated |
