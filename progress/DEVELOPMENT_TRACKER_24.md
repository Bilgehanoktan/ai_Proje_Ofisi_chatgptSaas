# TRACK-0201-R — 24 alan

Kanonik JSON: DEVELOPMENT_TRACKER_24.json. Puanlar ordinal; tamamlanma yüzdesi değil. 14 yeni arşiv testi PASS; 5 wrapper testi ve 13 PG NOT_RUN; önceki 164 seçili kontrol tekrar koşulmadı. W1/AI/MEM ayrı.

| ID | Alan | Tasarım | Kaynak | Test | Bu tur |
|---|---|---:|---:|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_PASS_COMPILED_PROXY | 0200-S evidence retained, not rerun |
| 2 | UI/UX Design System | 50 | 50 | NOT_RUN_CURRENT_EDS_BROWSER | 0200-S evidence retained, not rerun |
| 3 | Office Engine | 75 | 50 | PARTIAL_PASS_0199C_HISTORY | 0200-S evidence retained, not rerun |
| 4 | API & Contracts | 75 | 50 | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | 0200-S evidence retained, not rerun |
| 5 | Backend | 75 | 50 | PARTIAL_PASS_0201R_ARCHIVE | New reference module in product; 14 actual archive tests; wrapper integration NOT_RUN |
| 6 | Orchestrator | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | 0200-S evidence retained, not rerun |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_PASS_0199C_CAUSAL | Plan + command pins are serialized; real DAG history integration NOT_RUN |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_PASS_0199C_ROSTER | Run/admission/lease command types pinned; no actual runtime test |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_PASS_D0_SAMPLE_ADAPTER | 0200-S evidence retained, not rerun |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_PASS_D0_REVIEW | 0200-S evidence retained, not rerun |
| 11 | Database | 75 | 25 | PG_NOT_RUN_LOCAL_ARCHIVE_PASS | Separate local SQLite archive tested; PG remains NOT_RUN |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_PASS_0201R_ARCHIVE | Content-addressed reference archive; actual existing history wrapper NOT_RUN; global order design only |
| 13 | Memory & Knowledge | 75 | 25 | NOT_RUN | 0200-S evidence retained, not rerun |
| 14 | Security & IAM | 75 | 25 | PARTIAL_PASS_0201R_REFERENCE_TAMPER | Ordinary UPDATE/DELETE/REPLACE blocked, privileged corruption detected; no actual trust root |
| 15 | Independent Verifier | 75 | 25 | HOLD_INDEPENDENT_ACCEPTANCE | Separate failure terminal reference contract; actual independent receipt and success authority HOLD |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_PASS_0195_D0 | 0200-S evidence retained, not rerun |
| 17 | Ürün ve iş modülleri | 75 | 25 | NOT_RUN | 0200-S evidence retained, not rerun |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_RUN | 0200-S evidence retained, not rerun |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_PASS_0199C_BUDGET | Shared multi-project budget ownership design only; existing exclusive replay unchanged |
| 20 | Test & QA | 75 | 25 | PARTIAL_PASS_0201R_SELECTED | 14 new actual archive PASS; 5 wrapper candidates NOT_RUN; 164 prior selected tests not rerun |
| 21 | DevOps & Infrastructure | 75 | 25 | BLOCKED_PG_BINARY_DRIVER | Local git DNS failure, no postgres/psycopg/docker; exact checkout missing |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_PASS_HISTORICAL_READBACK | 0200-S evidence retained, not rerun |
| 23 | Backup & Disaster Recovery | 75 | 25 | PARTIAL_PASS_LOCAL_ARCHIVE_REOPEN | Actual read-only reopen and digest; no crash/backup/restore witness proof |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | Architecture, catalog, test evidence, 24 tracker, source manifest, handover, parallel checkpoint |
