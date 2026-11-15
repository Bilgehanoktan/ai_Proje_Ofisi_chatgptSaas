# 24 Teknik Alan — TRACK-0206

Ordinal olgunluk puanları korunmuştur; 24 seçili SQLite regresyon PASS. Bütünleşik ürün testi NOT_RUN. 0205/P05/P06 kanıtları tarihsel ve ayrı.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 77 frontend paths overall; historical projection and UI integrated, build NOT_RUN |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | EDS/Navigation/Workflow styles and components imported |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | Gallery, artwork and historical readback source integrated; live geometry join NOT_RUN |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 12/12 shared JSON blob parity; two new read-only routes to this baseline |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0206_SNAPSHOT_REGRESSIONS | 31 backend paths overall; 24 exact snapshot regression PASS |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Prior state retained; source carry verified where applicable |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Prior state retained; source carry verified where applicable |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0205R_QUARANTINE | Lifecycle projection and AI binding ports integrated; execution authority unchanged |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0196-MA model invocation envelope exact, provider disabled |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior state retained; source carry verified where applicable |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0205R_SQLITE | Prior state retained; source carry verified where applicable |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Prior state retained; source carry verified where applicable |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0194-M/0196-MA provenance, ACL, snapshot source integrated; combined memory suite NOT_RUN |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0205R_PIN | Prior state retained; source carry verified where applicable |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Prior state retained; source carry verified where applicable |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Prior state retained; source carry verified where applicable |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior state retained; source carry verified where applicable |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior state retained; source carry verified where applicable |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0205R_POOL | Prior state retained; source carry verified where applicable |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0206_SNAPSHOT_REGRESSIONS | 24 existing SQLite cases rerun; 12 core and 17 combined lifecycle tests NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | P05 candidate dependency pins imported; full checkout/lock/build blocked |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior state retained; source carry verified where applicable |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0205R_RECOVERY | Prior state retained; source carry verified where applicable |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | 108 path delta, symbol/API/DB/dependency/test catalog and handover updated |
