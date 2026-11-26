# TRACK-0190 — 24 alan

Ordinal scores unchanged. 63 selected controls PASS; 14 actual PG checks NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Ürün entegrasyonu | Test | Sonraki |
|---|---|---:|---:|---|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_COMPILED_PROXY | Full pinned Next build/browser |
| 2 | UI/UX Design System | 50 | 50 | EDS_SLICE_INTEGRATED | NOT_RUN_CURRENT_EDS_BROWSER | Run current EDS browser tests |
| 3 | Office Engine | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_ACTUAL_D0_OFFICE_PROJECTION | Actual browser; trusted freshness |
| 4 | API & Contracts | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | Full application contract acceptance |
| 5 | Backend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_37_SELECTED_PYTHON | Full pinned backend |
| 6 | Orchestrator | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_ACTUAL_D0_CLI | Canonical admission and execution |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_ACTUAL_WORKBENCH | Canonical task/admission mapping |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_ADMISSION_BUNDLE | Canonical lease and clock |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_SAMPLE_ADAPTER | Provider boundary only, no egress |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | Actual ToolGateway and receipts |
| 11 | Database | 75 | 25 | PARTIAL_INTEGRATED | PG_BLOCKED_14_CHECKS_READY | Run PG and resolve R03 |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_EVENT_READBACK | Canonical event/outbox readback |
| 13 | Memory & Knowledge | 75 | 25 | SOURCE_PRESENT_UNVERIFIED | NOT_RUN | Memory retrieval and ACL tests |
| 14 | Security & IAM | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_FIXED_OWNER | Real identity and independent custody |
| 15 | Independent Verifier | 75 | 25 | PARTIAL_INTEGRATED | HOLD_INDEPENDENT_ACCEPTANCE | Actual independent custody/acceptance |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_MEMBERSHIP | Actual multi-tenant RLS/membership |
| 17 | Ürün ve iş modülleri | 75 | 25 | EARLY_SOURCE | NOT_RUN | WorkType implementations |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_IMPLEMENTED | NOT_RUN | Separate authority and source work |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_BUDGET | Canonical reserve and settlement |
| 20 | Test & QA | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_63_SELECTED_CONTROLS | Actual PG and full suites |
| 21 | DevOps & Infrastructure | 75 | 25 | PARTIAL_INTEGRATED | BLOCKED_DNS_AND_PG_BINARY | Network-enabled isolated DEV |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_HISTORICAL_READBACK | Trusted freshness |
| 23 | Backup & Disaster Recovery | 75 | 25 | SOURCE_PREPARATION | NOT_RUN | Restore and witness design |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | CATALOG_UPDATED_SOURCE_PRESERVED | Preserve evidence |

## TRACK-0192
Ordinal scores unchanged; partial source in core lines, new tests NOT_RUN. Canonical JSON updated.
