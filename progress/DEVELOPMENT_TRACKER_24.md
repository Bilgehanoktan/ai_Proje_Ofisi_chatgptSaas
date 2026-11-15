# TRACK-0196-L — 24 alan

Kanonik JSON: DEVELOPMENT_TRACKER_24.json. Puanlar ordinal, tamamlanma yüzdesi değil. 26 yeni + 79 regresyon PASS; 10 PG SKIPPED/NOT_RUN. 0196-MA ayrı dal, bu kanıta dahil değil.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 0195 retained; not separately rerun unless noted |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | 0195 retained; not separately rerun unless noted |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_ACTUAL_D0_OFFICE_PROJECTION | 0195 retained; not separately rerun unless noted |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0195 retained; not separately rerun unless noted |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0196L_D0 | 26 new SQLite + 79 regressions PASS; full suite NOT_RUN |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0195_CLAIM | 0195 scheduler/claim regression passed; no new scheduler |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0196L_CHAIN | Admission-bound ordinary→renewal→VERIFYING→FAILED sample path tested |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0196L_LEASE | Same-owner renewal, exact history and terminal failure closure tested |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0195 retained; not separately rerun unless noted |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0195 retained; not separately rerun unless noted |
| 11 | Database | 75 | 25 | PG_NOT_RUN_SQLITE_LIFECYCLE_PASS | 2 new candidate tables; 10 PG tests skipped |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0196L_D0 | Renewal/failure event/outbox/fence/audit readback tested |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0195 retained; not separately rerun unless noted |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0196L_D0 | Initial admission/lease/epochs/history comparison; no real grant |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | 0195 retained; not separately rerun unless noted |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0195_D0 | 0195 retained; not separately rerun unless noted |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0195 retained; not separately rerun unless noted |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0195 retained; not separately rerun unless noted |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0196L_SETTLEMENT | Synthetic reservation release with zero recognized cost; source and CAS checks |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0196L_SELECTED | 26 new + 79 regression PASS; 10 PG skipped |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_AND_DRIVER | 5 new opt-in PG tests NOT_RUN; existing 5 also skipped |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0195 retained; not separately rerun unless noted |
| 23 | Backup & Disaster Recovery | 75 | 25 | NOT_RUN | 0195 retained; not separately rerun unless noted |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture, catalog, tracker, manifest, handover and parallel branch conflict review |
