# TRACK-0200-S — 24 alan

Kanonik JSON: DEVELOPMENT_TRACKER_24.json. Puanlar ordinal; tamamlanma yüzdesi değil. 11 yeni protokol +153 regresyon PASS; 13 PG SKIPPED/NOT_RUN. W1/AI/MEM ayrı hat.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 0199-C retained; not separately rerun unless selected regression |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | 0199-C retained; not separately rerun unless selected regression |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | 0199-C retained; not separately rerun unless selected regression |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0199-C retained; not separately rerun unless selected regression |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0200S_PROTOCOL | 11 new DB-API protocol tests + 153 selected regressions PASS; no full suite |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | 0199-C retained; not separately rerun unless selected regression |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | 0199-C retained; not separately rerun unless selected regression |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0199C_ROSTER | 0199-C retained; not separately rerun unless selected regression |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0199-C retained; not separately rerun unless selected regression |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0199-C retained; not separately rerun unless selected regression |
| 11 | Database | 75 | 25 | PG_NOT_RUN_SNAPSHOT_PROTOCOL_PASS | Repeatable read/read-only setup protocol tested; actual server NOT_RUN |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0200S_PROTOCOL | Consistent snapshot adapter source added; no actual PG isolation evidence |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0199-C retained; not separately rerun unless selected regression |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0200S_PROTOCOL | Disposable database and role guard, fail closed cleanup; no real authorization |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | 0199-C retained; not separately rerun unless selected regression |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0195_D0 | 0199-C retained; not separately rerun unless selected regression |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0199-C retained; not separately rerun unless selected regression |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0199-C retained; not separately rerun unless selected regression |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0199C_BUDGET | 0199-C retained; not separately rerun unless selected regression |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0200S_SELECTED | 11 new + 153 regression PASS; 13 PG skipped |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | No postgres/initdb/psql/psycopg/container engine in local environment |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0199-C retained; not separately rerun unless selected regression |
| 23 | Backup & Disaster Recovery | 75 | 25 | NOT_RUN | 0199-C retained; not separately rerun unless selected regression |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture, catalog, tracker, manifest, evidence and parallel checkpoint |
