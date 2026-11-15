# TRACK-0184 — 24 alan

Ordinal scores unchanged. 26 new + 15 regression selected tests PASS; separate CLI/loopback evidence. Full product/Next/browser/PostgreSQL and pinned suites NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Ürün entegrasyonu | Test | Sonraki |
|---|---|---:|---:|---|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_OUTBOX_PROXY | Pinned full Next build/current browser incl panels |
| 2 | UI/UX Design System | 50 | 50 | EDS_SLICE_INTEGRATED | NOT_RUN_CURRENT_EDS_BROWSER | Run current EDS browser tests |
| 3 | Office Engine | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_OFFLINE_BROWSER | Current Phaser/browser controls |
| 4 | API & Contracts | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_OUTBOX_API | Register schema and test parity/full app |
| 5 | Backend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_OUTBOX | Full pinned backend |
| 6 | Orchestrator | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_WORKBENCH | Actual runtime only after applicable authority |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_WORKBENCH | Full DAG and lifecycle |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW_LEASE | Canonical trusted clock/lease |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_ADAPTER | Approved provider adapters, egress and policy |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | Actual ToolGateway and receipts |
| 11 | Database | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_PERSISTENCE | R03 approved mapping and PostgreSQL non-owner test |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_UNKNOWN_HOLD | Canonical outbox claim/send marker/receipt and reconciliation |
| 13 | Memory & Knowledge | 75 | 25 | SOURCE_PRESENT_UNVERIFIED | NOT_RUN | Memory retrieval and ACL tests |
| 14 | Security & IAM | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_DENIAL | Independent acceptance and real IAM |
| 15 | Independent Verifier | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | Independent IV trust root and receipts |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_FIXED_SCOPE | Actual tenant ownership/RLS |
| 17 | Ürün ve iş modülleri | 75 | 25 | EARLY_SOURCE | NOT_RUN | WorkType implementations |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_IMPLEMENTED | NOT_RUN | Separate authority and source work |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_FINANCE | Settlement, ledger, real billing gates |
| 20 | Test & QA | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_SELECTED_0184 | Full pinned suites and current browser |
| 21 | DevOps & Infrastructure | 75 | 25 | PARTIAL_INTEGRATED | BLOCKED_DEPENDENCY_DNS | Approved network and pinned dependencies |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_READONLY_PROJECTION | Canonical projection/freshness |
| 23 | Backup & Disaster Recovery | 75 | 25 | SOURCE_PREPARATION | NOT_RUN | Restore and witness design |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | MANIFEST_READBACK_PASS | Maintain catalog and evidence |
