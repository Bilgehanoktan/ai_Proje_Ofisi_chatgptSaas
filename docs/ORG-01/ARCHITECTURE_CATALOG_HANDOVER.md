# ORG-01 — organization architecture source audit
2026-11-17. Read-only audit; isolated planning branch from core 167e5239882dc7b49bd96647412fe6761da0be5e. UI 33fabd52740dc79be6bb4847e6e9865f69556c09; Office 089a4a256cdf0fc835035041ac519b4c15250542; A6 review 438985fea059f0ffafdfa16f0d090cb854b5fc36 (previous observed heads, not locks). Core/UI/Office manifests: 392/491/415 entries. Nine source blobs inspected, no execution. Design Master 0155 lines 106594, 106994, 107021–107031, 107486, 116344; current roadmap PRODUCT_ROADMAP_8_PHASES.md. ORG-A P0 single default Company, ORG-B-ready; T-C, ROLE-B, D29-03/04. 267 templates != 267 employees or workers. Preserve four P0 roles, separate seven review principals. No new normative authority.

## Technical catalog delta (audit only)
| File | Git blob | Symbol | Finding |
|---|---|---|---|
| identity_registry.py | e1f52722e1d33841539b709036ed1a100216b9b6 | RegistrySnapshot / inspect_registry | D0 scope and revision pin; not authenticated hierarchy |
| development_review/model.py | ebd68c6245c21c7fce16c0b6206dc9626050310a | PrincipalPin / valid_roster | Exactly seven review principals; separate from staffing |
| scheduler_review.py | f354ee1fdceca013ad6cf32fdea7c41001794083 | inspect_schedule / inspect_pinned_schedule | Four operational roles; readiness only |
| research_slice.py | 720044a4e4954820b8d298f73b6b75f2189b4f94 | review_research_roster | Fixed Research revision and demo project |
| orchestrator/engine.py | f327ab8a69336cd1ba4d61f56035f540c66d700e | parse_plan / canonical_plan | RESEARCH only, 100 tasks max; not agent capacity |
| company.catalog.demo.schema.json | 963bfb2557628cea2696c0e557e5aeaf9a23ea62 | company.catalog.v0-D0 | Sample sections/lanes, not org CRUD |
| studioGovernance.ts | dfb4e7e8fb4c409f8bdfa0f021a3c7f3542ca62a | organizationTemplate | Exactly four templates, no assignment |
| premiumActorIdentity.ts | 1189295b372f2b9360cbecbf5357f2ad356f1824 | createVisualIdentityRegistry | Four roles, 32 extra test stations, null agentInstanceId |
| premiumDynamicFloors.ts | d53d8c78b6d980ddc531d2e0a3ea89f6d8e992c2 | createDynamicFloors | 32 floors, 128 actors, 32 portals; four roles; D0 only |

## Gaps and next
ORG-02: candidate immutable org revision with Tenant/Company/[Division]/Department/[Team]/[Position]/AgentDefinition; separate instance/seat binding, line_reporting, task_accountability/handoff, authorization/verification/effect. Test duplicate IDs, cycles, cross-scope parent, single parent, stale revision, temporary assignment not changing reporting or ACL, IV independence. Do not change existing scheduler, DAG, IAM, UI, Office or DB. ORG-03: read-only placement mapping proposal; no geometry join. ORG-04: 4/12/30/60/100/267 synthetic scenarios; measure catalog, render and runtime separately; 128 avatar guard must remain in old fixture. ORG-05: integration only after owner review and gates. No claim that full DB/API inventory was audited; inspect database and shared contracts before schema proposal. No live agents, grants, provider, spend, CI/main/merge. No product changes or tests run; gates unchanged. Rollback: abandon isolated planning branch, no DB changes. This document is a scoped architecture/catalog/handover addendum, not replacement of canonical trackers.
