# 24 Teknik Alan — TRACK-0204-C

Ordinal olgunluk puanları, tamamlanma yüzdesi değil. 105 seçili PASS (51 yeni,54 regresyon); tam T1, 12 önceki entegrasyon ve 13 PG NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---:|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | Prior evidence retained, not rerun |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | Prior evidence retained, not rerun |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | Prior evidence retained, not rerun |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Prior evidence retained, not rerun |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0204C | Company coordination pre/post guards; T1 decorator not run |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Historical causal order; no executable scheduler |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0204C_REPLAY | Project/run membership and causal predecessor pins; no success dependency |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Explicit run/agent/principal membership, not grant |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | Prior evidence retained, not rerun |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Prior evidence retained, not rerun |
| 11 | Database | 75 | 25 | PARTIAL_PASS_0204C_SQLITE | Three candidate DDL tables; real PG/R03 open |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0204C_SQLITE | Company sequence CAS and exact index readback, SQLite race test |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Scope isolation, stale pin and mismatches denied; independent custody open |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Prior evidence retained, not rerun |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Company/project isolation D0, not actual multi-tenant RLS |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | Prior evidence retained, not rerun |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | Prior evidence retained, not rerun |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0204C_REPLAY | Shared fixed caps and reservation/settlement pre/post guards; actual T1 integration not run |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0204C_SELECTED | 51 new + 54 rerun selected PASS; 12 prior integration and 13 PG NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | Local exact checkout DNS failure, actual PG unavailable |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | Prior evidence retained, not rerun |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_0204C_SQLITE | Old-prefix rejection and rollback; real restore/W-A not run |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Source/catalog/test evidence/24 tracker/handover updated |
