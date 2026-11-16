# 24 Teknik Alan — TRACK-0208

Ordinal puanlar korunmuştur; 98 seçili PASS (72 regresyon, 26 yeni). D-01 D0 ortak kontrol PASS; D-02 açık; bütünleşik ürün NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | Prior status retained; no new acceptance |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | Prior status retained; no new acceptance |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_HISTORICAL_READBACK | Static review of existing historical views/fixture geometry; no new runtime linkage |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Prior status retained; no new acceptance |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0208_SELECTED_BACKEND | 98 selected cases; 29 locked tests NOT_RUN |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Prior status retained; no new acceptance |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Prior status retained; no new acceptance |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0208_JOINT_CONTEXT | 26 new joint checks, D-01 D0 pass, mandatory effect gate HOLD |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_0208_JOINT_CONTEXT | Exact model input span/registry digest, DENY maintained |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior status retained; no new acceptance |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0205R_SQLITE | Prior status retained; no new acceptance |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Prior status retained; no new acceptance |
| 13 | Memory & Knowledge | 75 | 25 | PARTIAL_PASS_0208_JOINT_CONTEXT | Memory span/ACL/tombstone checks; D-02 copied DB gap reproduced |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0208_DENIAL | Joint denial scenarios pass; independent authority HOLD |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Prior status retained; no new acceptance |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Prior status retained; no new acceptance |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior status retained; no new acceptance |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior status retained; no new acceptance |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0205R_POOL | Prior status retained; no new acceptance |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0208_98 | 72 regression +26 new; 55 remote content hashes verified |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_CHECKOUT_DEPENDENCIES_PG | 47 missing files, mismatched direct pins, PG unavailable |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior status retained; no new acceptance |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0208_RESTORE_GAP | Old DB copy + old pin structurally matches; no grant |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | 0208 source/test/evidence and all handover documents |
