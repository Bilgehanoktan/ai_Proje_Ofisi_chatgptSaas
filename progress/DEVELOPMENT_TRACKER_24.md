# 24 Teknik Alan — TRACK-0203-T

Ordinal olgunluk puanları, tamamlanma yüzdesi değil. 54 seçili PASS; 7+5 entegrasyon ve 13 PG NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | Prior evidence retained, not rerun |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | Prior evidence retained, not rerun |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | Prior evidence retained, not rerun |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Prior evidence retained, not rerun |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0203T_ANCHOR_SQL | T1 extension and strict readback source; actual 4-table SQLite fixture, full writer NOT_RUN |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | Prior evidence retained, not rerun |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | Prior evidence retained, not rerun |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0203T_ANCHOR_SQL | Failure-only T1 anchor source; original eight-role lifecycle integration NOT_RUN |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | Prior evidence retained, not rerun |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior evidence retained, not rerun |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0203T_DDL_SQLITE | Candidate DDL executed on actual SQLite; PG/R03 open |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0203T_ANCHOR_SQL | Exact command anchor and same-snapshot strict source; full integration NOT_RUN |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0203T_STRICT_MOCK | Strict anchor and mismatch rejection; external pin custody HOLD |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Fixture signature + strict anchor; no independent issuer or acceptance |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0195_D0 | Prior evidence retained, not rerun |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior evidence retained, not rerun |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0203T_SQL_FIXTURE | Settlement binding tested in minimal fixture; shared project budget NOT_IMPLEMENTED |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0203T_SELECTED | 54 selected PASS; 7 new lifecycle and 5 prior integration NOT_RUN; 13 PG NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | No actual PG; local checkout blocked by DNS |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior evidence retained, not rerun |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0203T_REOPEN | SQLite commit/reopen and rollback; real W-A restore NOT_RUN |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture/technical catalog/evidence/devir/manifest/24 tracker updated |
