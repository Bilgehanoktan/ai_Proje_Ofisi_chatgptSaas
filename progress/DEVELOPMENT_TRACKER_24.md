# TRACK-0194 — 24 alan

Kanonik JSON: DEVELOPMENT_TRACKER_24.json. Puanlar ordinal, tamamlanma yüzdesi değil. 35 yeni + 25 regresyon seçili test PASS; 5 gerçek PG testi SKIPPED/NOT_RUN. Full suite/build NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 0193 preserved; not rerun |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | 0193 preserved; not rerun |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_ACTUAL_D0_OFFICE_PROJECTION | 0193 preserved; not rerun |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0193 preserved; not rerun |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0194_D0 | 25 SQLite mapping + 25 mock regression PASS; no full suite |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0194_SCHEDULER | 10 scheduler tests PASS; no worker claim |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0194_SCHEDULER | Canonical plan dependency and scope checks; 10 scheduler tests |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0194_D0 | Lease lock/recheck, transition state writes in SQLite shim; no lease issuance |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0193 preserved; not rerun |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0193 preserved; not rerun |
| 11 | Database | 75 | 25 | PG_NOT_RUN_SQLITE_MAPPING_PASS | Candidate 3 tables; actual SQLite rollback/race PASS; real PG 5 skipped |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0194_D0 | Existing event/outbox/fence integrated in local SQLite transition tests |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0193 preserved; not rerun |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0194_D0 | Synthetic lease reference/epoch/fence checks only; no real PEP |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | 0193 preserved; not rerun |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_D0_MEMBERSHIP | 0193 preserved; not rerun |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0193 preserved; not rerun |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0193 preserved; not rerun |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_D0_BUDGET | 0193 preserved; not rerun |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0194_SELECTED | 35 new + 25 regression PASS; 5 PG skipped |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_DNS_AND_PG_BINARY | Opt-in actual PG harness added; not executed |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0193 preserved; not rerun |
| 23 | Backup & Disaster Recovery | 75 | 25 | NOT_RUN | 0193 preserved; not rerun |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Source manifest, symbols, database, evidence, tracker and handover updated |
