# 24 Teknik Alan — TRACK-0209

Ordinal puanlar korunmuştur; 138 seçili PASS (98 regresyon, 40 yeni). D-03 açık; tam ürün NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | Prior status retained; no new acceptance |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | Prior status retained; no new acceptance |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_HISTORICAL_READBACK | Prior status retained; no new acceptance |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Prior status retained; no new acceptance |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0209_SELECTED_BACKEND | 138 selected tests; 29 core not run |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Prior status retained; no new acceptance |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0205R_CHECKPOINT | Prior status retained; no new acceptance |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0209_WITNESSED_T1 | D0 joint witness and original ordinary six-role mapping on SQLite |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_0209_WITNESSED_CONTEXT | Model invocation remains DENY; joint witness checks |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior status retained; no new acceptance |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0209_ORIGINAL_SQLITE | Original 3 DDL, 6 roles and single writer verified on SQLite |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0209_ORDINARY_T1 | Original event/outbox/fence writes and readback verified |
| 13 | Memory & Knowledge | 75 | 25 | PARTIAL_PASS_0209_MEMORY_WITNESS | 23 signed witness tests; restore and CAS; independent custody HOLD |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0209_WITNESS_DENIAL | D-03 final-check race reproduced, independent authority HOLD |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Prior status retained; no new acceptance |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Prior status retained; no new acceptance |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior status retained; no new acceptance |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior status retained; no new acceptance |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0205R_POOL | Prior status retained; no new acceptance |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0209_138 | 98 rerun +40 new; 29 core tests NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_CHECKOUT_DEPENDENCIES_PG | 19/55 local exact, 36 missing; PG/lock still blocked |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior status retained; no new acceptance |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0209_RESTORE_WITNESS | D0 signed external head rejects restore with current pin; all-three rollback matches |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | 0209 source/test evidence, findings, tracker, handover |
