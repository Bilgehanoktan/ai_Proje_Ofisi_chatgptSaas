# UI-P10J-12 — integration matrix

Core tracker TRACK-0223 at c94753b4f2bc8a3e739ffa997ca9547772deeaf2; UI parent 9cd9ebee9f0760eeec24a86bf02487f02096eea8. Historical status from core, UI increment separately; all unified build/acceptance NOT_RUN/HOLD.

| ID | Area | Core integration | Core test | This UI round |
|---|---|---|---|---|
| 1 | Frontend | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_STUDIO_CONTEXT | AgentDirectory and Office UI wired in UI branch; React NOT_RUN |
| 2 | UI/UX Design System | EDS_SLICE_INTEGRATED | PARTIAL_PASS_0217_STUDIO_CONTEXT | Responsive role/room presentation source integrated in UI branch |
| 3 | Office Engine | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_HISTORICAL_LABEL | Local room context/filter; geometry and JOIN_HOLD preserved |
| 4 | API & Contracts | PARTIAL_INTEGRATED | PARTIAL_PASS_ACTUAL_SCHEMA_HTTP | UNCHANGED_THIS_UI_ROUND |
| 5 | Backend | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_SIGNED_FIXTURE | UNCHANGED_THIS_UI_ROUND |
| 6 | Orchestrator | PARTIAL_INTEGRATED | PARTIAL_PASS_0204C_REPLAY | UNCHANGED_THIS_UI_ROUND |
| 7 | Task Engine & DAG | PARTIAL_INTEGRATED | PARTIAL_PASS_0205R_CHECKPOINT | Reference plan display only; Task Engine unchanged |
| 8 | Agent Runtime | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_SIGNED_FIXTURE | Role template context only; runtime unchanged |
| 9 | AI Model Gateway | PARTIAL_INTEGRATED | PARTIAL_PASS_0210_DENIAL | UNCHANGED_THIS_UI_ROUND |
| 10 | Skill & Tool Engine | PARTIAL_INTEGRATED | PARTIAL_PASS_D0_REVIEW | UNCHANGED_THIS_UI_ROUND |
| 11 | Database | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_LOCAL_SQLITE_DDL_PINS | UNCHANGED_THIS_UI_ROUND |
| 12 | Event Store & Messaging | PARTIAL_INTEGRATED | PARTIAL_PASS_0211_COMPONENT_CLAIM | UNCHANGED_THIS_UI_ROUND |
| 13 | Memory & Knowledge | SOURCE_PRESENT_UNVERIFIED | PARTIAL_PASS_0210_LOCAL_FENCE | UNCHANGED_THIS_UI_ROUND |
| 14 | Security & IAM | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_SIGNED_FIXTURE_RESTORE_RESIDUAL | UNCHANGED_THIS_UI_ROUND |
| 15 | Independent Verifier | PARTIAL_INTEGRATED | HOLD_INDEPENDENT_ACCEPTANCE | UNCHANGED_THIS_UI_ROUND |
| 16 | SaaS & Multi-Tenant | PARTIAL_INTEGRATED | PARTIAL_PASS_0204C_REPLAY | UNCHANGED_THIS_UI_ROUND |
| 17 | Ürün ve iş modülleri | EARLY_SOURCE | NOT_RUN | UNCHANGED_THIS_UI_ROUND |
| 18 | Dış sistem entegrasyonları | NOT_IMPLEMENTED | NOT_RUN | UNCHANGED_THIS_UI_ROUND |
| 19 | Finans & Billing | PARTIAL_INTEGRATED | PARTIAL_PASS_0205R_POOL | UNCHANGED_THIS_UI_ROUND |
| 20 | Test & QA | PARTIAL_INTEGRATED | PARTIAL_PASS_0217_SELECTED_37 | 6/6 local model tests; W8/browser candidate updated, NOT_RUN |
| 21 | DevOps & Infrastructure | PARTIAL_INTEGRATED | BLOCKED_CHECKOUT_DEPENDENCIES_PG | UNCHANGED_THIS_UI_ROUND |
| 22 | Monitoring & Observability | PARTIAL_INTEGRATED | PARTIAL_PASS_HISTORICAL_READBACK | UNCHANGED_THIS_UI_ROUND |
| 23 | Backup & Disaster Recovery | SOURCE_PREPARATION | PARTIAL_PASS_0217_RESTORE_RESIDUAL | UNCHANGED_THIS_UI_ROUND |
| 24 | Teknik katalog & dokümantasyon | CATALOG_UPDATED | CATALOG_UPDATED | Revisioned architecture, technical catalogue, matrix and handover updated |

## P10J-12 work items

| ID | Item | Source | Tests | Union | Acceptance |
|---|---|---|---|---|---|
| P12-01 | Agent Studio catalogue and profile context | INTEGRATED_UI_SOURCE | MODEL_PARTIAL_PASS; REACT_NOT_RUN | PENDING_0223 | HOLD_OR_NOT_RUN |
| P12-02 | Reference plan predecessor/follower display | INTEGRATED_UI_SOURCE | 3 MODEL_PASS | PENDING_0223 | HOLD_OR_NOT_RUN |
| P12-03 | Office room focus/filter/reset and styling | INTEGRATED_UI_SOURCE | 3 MODEL_PASS; BROWSER_NOT_RUN | PENDING_SHARED_PATH_REVIEW | HOLD_OR_NOT_RUN |
| P12-04 | Real avatar/live location and authenticated placement | NOT_IMPLEMENTED_THIS_ROUND | NOT_RUN | HOLD | HOLD_OR_NOT_RUN |
| P12-05 | Core shared snapshot and StudioContextPanel | CORE_BRANCH_ONLY | CORE_HISTORICAL_SELECTED_PASS | NOT_MERGED | HOLD_OR_NOT_RUN |
| P12-06 | W8 68 screen browser suite | HARNESS_UPDATED | NOT_RUN | NOT_APPLICABLE | HOLD_OR_NOT_RUN |
| P12-07 | Architecture/catalog/matrix/handover | UPDATED_UI | DOCUMENT_READBACK_PENDING | SEPARATE_RECORD | HOLD_OR_NOT_RUN |
