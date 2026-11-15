# TRACK-0183 — 24 alan

Ordinal rubric unchanged. 15 new selected tests (9 Python, 6 Node); 62 historical 0182 checks not rerun. Full Next build/browser, PostgreSQL and full backend NOT_RUN.

| ID | Alan | Tasarım | Kaynak | Ürün entegrasyonu | Test | Sonraki |
|---|---|---:|---:|---|---|---|
| 1 | Frontend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_SNAPSHOT_PARSER | Pinned Next build/current browser with lifecycle panel |
| 2 | UI/UX Design System | 50 | 50 | EDS_SLICE_INTEGRATED | NOT_RUN_CURRENT_EDS_BROWSER | Run current EDS browser tests |
| 3 | Office Engine | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_OFFLINE_BROWSER | Current Phaser/browser controls |
| 4 | API & Contracts | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_API | Pinned environment contract suite |
| 5 | Backend | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_ATOMIC_SAMPLE | Full pinned backend suite |
| 6 | Orchestrator | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_WORKBENCH | Actual runtime only after applicable authority |
| 7 | Task Engine & DAG | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_WORKBENCH | Full DAG and lifecycle |
| 8 | Agent Runtime | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_HEARTBEAT_FENCE | Trusted clock, canonical lease/admission |
| 9 | AI Model Gateway | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_ADAPTER | Approved provider adapters, egress and policy |
| 10 | Skill & Tool Engine | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | Actual ToolGateway and receipts |
| 11 | Database | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_ATOMIC_SAMPLE | R03 physical mapping and PostgreSQL test |
| 12 | Event Store & Messaging | 75 | 50 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_ATOMIC_SAMPLE | Canonical outbox claim/reconciliation and T1 |
| 13 | Memory & Knowledge | 75 | 25 | SOURCE_PRESENT_UNVERIFIED | NOT_RUN | Memory retrieval and ACL tests |
| 14 | Security & IAM | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_DENIAL | Independent acceptance and real IAM |
| 15 | Independent Verifier | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | Independent IV trust root and receipts |
| 16 | SaaS & Multi-Tenant | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_FIXED_SCOPE | Tenant ownership and independent RLS tests |
| 17 | Ürün ve iş modülleri | 75 | 25 | EARLY_SOURCE | NOT_RUN | WorkType implementations |
| 18 | Dış sistem entegrasyonları | 75 | 0 | NOT_IMPLEMENTED | NOT_RUN | Separate authority and source work |
| 19 | Finans & Billing | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_FINANCE | Settlement, ledger, real billing gates |
| 20 | Test & QA | 75 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_SELECTED_0183 | Full pinned suites and actual browser |
| 21 | DevOps & Infrastructure | 75 | 25 | PARTIAL_INTEGRATED | BLOCKED_DEPENDENCY_DNS | Approved network and transitive locks |
| 22 | Monitoring & Observability | 50 | 25 | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_PROJECTION | Observability pipeline |
| 23 | Backup & Disaster Recovery | 75 | 25 | SOURCE_PREPARATION | NOT_RUN | Restore and witness design |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | CATALOG_UPDATED | MANIFEST_READBACK_PASS | Maintain catalog and evidence |
