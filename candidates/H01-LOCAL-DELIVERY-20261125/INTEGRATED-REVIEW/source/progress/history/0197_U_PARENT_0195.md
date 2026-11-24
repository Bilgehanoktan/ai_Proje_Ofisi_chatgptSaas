# TRACK-0195 — 24 alan

Kanonik JSON: DEVELOPMENT_TRACKER_24.json. Puanlar ordinal, tamamlanma yüzdesi değil. 19 yeni + 60 regresyon PASS; 5 PG SKIPPED/NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 0194 retained; not separately rerun unless noted |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | 0194 retained; not separately rerun unless noted |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_ACTUAL_D0_OFFICE_PROJECTION | 0194 retained; not separately rerun unless noted |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0194 retained; not separately rerun unless noted |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0195_D0 | 19 new SQLite admission + 60 regression PASS; full suite NOT_RUN |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0195_CLAIM | Persisted canonical roster readiness used by first-claim mapping |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0195_CLAIM | Unique plan/task roster and QUEUED→ADMITTED→RUNNING test |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0195_CLAIM | Initial lease and claim mapping, expiry/epoch/race rollback PASS |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0194 retained; not separately rerun unless noted |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0194 retained; not separately rerun unless noted |
| 11 | Database | 75 | 25 | PG_NOT_RUN_SQLITE_CLAIM_PASS | Three candidate tables plus unique roster index; real PG NOT_RUN |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0195_D0 | Nine-role event/outbox/audit and readback PASS |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0194 retained; not separately rerun unless noted |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0195_D0 | Synthetic lease/epoch checks only; actual grant HOLD |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | 0194 retained; not separately rerun unless noted |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0195_D0 | Synthetic company-scoped budget only; real tenant isolation not proven |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0194 retained; not separately rerun unless noted |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0194 retained; not separately rerun unless noted |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0195_BUDGET | Shared sample budget reservation CAS/limit/unknown checks |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0195_SELECTED | 19 new + 60 regression PASS; 5 PG skipped |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_DNS_AND_PG_BINARY | 0194 retained; not separately rerun unless noted |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0194 retained; not separately rerun unless noted |
| 23 | Backup & Disaster Recovery | 75 | 25 | NOT_RUN | 0194 retained; not separately rerun unless noted |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture, technical catalog, tracker, manifest and handover |
