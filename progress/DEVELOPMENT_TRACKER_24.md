# TRACK-0181 — 24 alan

Ordinal design/source scores retained; actual selected test evidence tracked separately. 38/38 selected local synthetic tests; full build/browser/acceptance NOT_RUN/HOLD.

| ID | Alan | Hat | Tasarım | Kaynak | Gerçek test | Bu tur | Sonraki |
|---|---|---|---:|---:|---|---|---|
| 1 | Frontend | W1 | 75 | 50 | PARTIAL_PASS_D0_TS_PROXY_BROWSER_NOT_RUN | 14 Node tests incl. actual backend proxy GET; TS route/guard compiled; panel and Dashboard source integrated; browser/build NOT_RUN | Full pinned Next build, browser UI EDS/MVP/Office |
| 2 | UI/UX Design System | W1 | 50 | 50 | NOT_RUN | Prior state retained; no new test evidence | Token, erişilebilirlik ve responsive kabul; UX NOT_RUN |
| 3 | Office Engine | W1 | 75 | 50 | PARTIAL_PASS_D0_API | Office snapshot GET in 7 endpoint tests; no browser scene test | Office browser and layout tests |
| 4 | API & Contracts | W2 | 75 | 50 | PARTIAL_PASS_D0_API | GET diagnostics + proxy; 7 backend GET routes; exact schema and negative guard | Full contract suite and pinned environment |
| 5 | Backend | W2,W3,W4 | 75 | 50 | PARTIAL_PASS_D0_BACKEND | 24 selected Python tests, actual Uvicorn loopback; not full suite | Full backend suite pinned |
| 6 | Orchestrator | W3 | 75 | 50 | PARTIAL_PASS_D0_PLAN | Canonical plan digest and plan binding inspection; no dispatch | Runtime integration gates and remaining tests |
| 7 | Task Engine & DAG | W3 | 75 | 50 | PARTIAL_PASS_D0_PLAN | 5 plan projection tests plus diagnostics graph checks | Expanded DAG tests, real execution separately gated |
| 8 | Agent Runtime | W3 | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Lifecycle inspection, missing lease HOLD; no agent run | Lease/authority and actual runtime separately gated |
| 9 | AI Model Gateway | W5 | 50 | 25 | PARTIAL_PASS_D0_REVIEW | Pinned registry and fallback inspection; DisabledModelGateway | Provider runtime and egress gated |
| 10 | Skill & Tool Engine | W5,W4 | 75 | 25 | PARTIAL_PASS_D0_REVIEW | Skill/capability review; independent receipts absent | Tool adapters and receipts separately gated |
| 11 | Database | W4 | 75 | 25 | PARTIAL_PASS_D0_SQLITE | 8 in-memory SQLite tests; rollback; no persistent database | PostgreSQL schema/migration/T1 review |
| 12 | Event Store & Messaging | W4 | 75 | 50 | PARTIAL_PASS_D0_SQLITE | 3 sample events readback; gaps/duplicates denied | Persistent event store/outbox and messaging |
| 13 | Memory & Knowledge | W5 | 75 | 25 | NOT_RUN | Prior state retained; no new test evidence | Kaynak ACL, index, tombstone, cache ve retrieval |
| 14 | Security & IAM | W4 | 75 | 25 | PARTIAL_PASS_D0_DENIAL | Unexpected effect flags, mutations and cross-tenant scope rejected; no independent acceptance | Security acceptance remains HOLD |
| 15 | Independent Verifier | W6 | 75 | 25 | PARTIAL_PASS_D0_REVIEW | IV trust boundary inspection; no receipt | Independent IV trust root and signed receipts |
| 16 | SaaS & Multi-Tenant | W7 | 75 | 25 | PARTIAL_PASS_D0_SCOPE | Wrong-tenant negative tests; no onboarding | Tenant isolation persistence, onboarding, authorization |
| 17 | Ürün ve iş modülleri | W6 | 75 | 25 | NOT_RUN | Prior state retained; no new test evidence | Üç WorkType motoru, readback ve IV |
| 18 | Dış sistem entegrasyonları | W4,W5 | 75 | 0 | NOT_RUN | Prior state retained; no new test evidence | Adapter, izinli egress, readback; dış yazma kapalı |
| 19 | Finans & Billing | W7 | 75 | 25 | PARTIAL_PASS_D0_FINANCE | Synthetic budget review, actual cost/revenue null | Billing ledger, provider cost, real funds gated |
| 20 | Test & QA | W8 | 75 | 25 | PARTIAL_PASS_D0_TEST | 24 Python + 14 Node selected local tests, 38 total | Full suites, pinned locks, browser |
| 21 | DevOps & Infrastructure | W4,W8 | 75 | 25 | PARTIAL_PASS_D0_RUN | Local Uvicorn started/stopped; observed env non-pinned; lock NOT_GENERATED | Clean isolated dependency resolution and full build |
| 22 | Monitoring & Observability | W4,W8 | 50 | 25 | PARTIAL_PASS_D0_PROJECTION | Finance projection exposed as UNVERIFIED; no real metrics | Observability integration and monitoring |
| 23 | Backup & Disaster Recovery | W4 | 75 | 25 | NOT_RUN | Prior state retained; no new test evidence | Fenced startup, bağımsız W-A, gerçek backup/restore ve reconciliation kabulü |
| 24 | Teknik katalog & dokümantasyon | W8 | 75 | 75 | NOT_RUN | 162 manifest paths/sizes; 48 backend and 6 frontend files exact blob matched; catalog and handover | Keep per-turn pins and actual test evidence |
