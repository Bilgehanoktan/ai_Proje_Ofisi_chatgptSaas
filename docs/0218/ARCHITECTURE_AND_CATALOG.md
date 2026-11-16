# DOC-REV-0218 — Architecture Realignment & Product Integration

User approved the 0218–0225 sequence on 2026-11-16. This is a development priority direction, not a normative ADR, new runtime grant, independent acceptance, or approval of a migration. Parent 8615b6bc86c183d9a294de7d93041c14c75d8112; unchanged product source 093d9674e3a753ae26f799217ffdc3ae5ed74b75. Product manifest c6c50d70884374ac27ccb2fc850b4430ef5bd10c.

## Result
Remote tree (not truncated): 1459 repo blobs, 365 product files; 364/364 paths and sizes match manifest, no extras; 55/55 locked core Git blob+size and 6/6 0217 delta Git blob+size match. Original v135 and 0155 bytes independently hash-matched locally. Full local checkout and 364 per-file SHA-256 rehash blocked by DNS; no product source/API/DB/event/dependency changes or test executions. Prior D0 evidence remains historical; integration 7/16, not overall completion. See [evidence](../../releases/SOURCE_PREFLIGHT_0218.json).

## Scope reconciliation (engineering direction, NOT implemented)
Reuse lifecycle.Scope and transaction.review.LogicalIntent. The 0217 signed_consume_reference.Scope is a D0 observation fixture, not a second principal or grant. It omits plan revision, agent instance, principal; runtime scope lacks project/effect, which already have separate owners. Do not flatten, rename signed historical payloads, or reinterpret old hashes. Resolve project from a unique, verified committed company Member relation; effect from LogicalIntent.effect_key. Bind all identities plus request/binding/transaction and current policy/witness epoch. A role, fixture caller, matched signature, local clock or readback alone cannot grant. Missing/ambiguous mapping => HOLD; contradictory scope => DENY. No blind retries after consumed/UNKNOWN. Current fixture continues HOLD, no gateway wiring until accepted real boundary. A changed signing profile would require explicit version and independent review, not a silent hash rewrite.

| Field | Existing owner | Required mapping |
| --- | --- | --- |
| tenant/company/environment | lifecycle.Scope tenant_id/company_id/environment_id | exact same; never request-only |
| plan_revision/task/run/agent_instance/principal | lifecycle.Scope, LogicalIntent.scope | all five remain bound; no role-as-instance substitution |
| project | company_coordination.Member.project_id + matching committed roster | resolve by tenant/company/env + revision/task/run/agent/principal; unique match, no caller-invented project |
| effect | LogicalIntent.effect_key | exact effect key; do not collapse to scope-only idempotency |
| request / tx / binding | LogicalIntent.request_digest, committed receipt, witnessed_mapping.binding_digest | bind exact request, transaction, canonical preimage/postimage, witness and memory/model pin; no caller-supplied independent proof |
| epochs / authority | current trusted policy and W-A head | validate freshness, lease and revocation at correct boundary; restore-external root absent => HOLD |

Existing 0209 witnessed mapping checks RUNNING→VERIFYING only; 0210/0211 local serialized intent wrapping is not external effect authorization; 0215 observation is read-only; 0216/0217 local references have restore residual and no independent custody. Keep them for historical regression, do not promote as an alternate production authority. Independent issuer/key/clock/nonce, durable receipt or UNKNOWN, revocation/provider serialization and bypass tests stay open (D-01–D-04).

## R03 / T1
Keep [0190 R03 decision packet](../0190/R03_T1_DECISION_PACKET.md) C review boundary. Use existing LogicalT1Coordinator, postgres_session, mappings, company coordination, lifecycle commands and readback; no extra engine or guessed physical table ownership. One local transaction with required logical roles, rollback and consistent independent readback; external effect outside T1 and disabled. Candidate DDL is D0, no ENABLE/FORCE RLS; no actual canonical mapping accepted. PG13 and separate non-owner RLS + company contention follow existing 0215/0217 runbooks, not a production migration.

## Environment / next action
Three Python direct pin mismatches, TypeScript mismatch; no PG or driver, no full checkout/locks. No fabricated lock or package install. Obtain authorized exact checkout of 0218 branch and reviewed dependency locks in isolated environment, verify manifest and 55 core pins, run locked core29 and original fixture6, then existing PG13 with disposable DB and runner ACK; separate RLS/lock tests. Do not claim gate closure from this preflight. W8 blocks its own runtime evidence, not other independent source design/development.

## Workstreams and delivery
| Lane | Scope | Existing paths (abbreviated within backend/FE) | Target | Acceptance |
| --- | --- | --- | --- | --- |
| W1 | Office/UI | product/ai-company-os-frontend/features/data/projectionScope.ts; features/data/projectionSession.ts; design-system/WorkflowProjection.tsx; features/mvp/HistoricalEvidenceStrip.tsx | 0222/0223 | same scoped committed sequence, stale/gap resync, actual React browser |
| W2 | Contracts/API | product/ai-company-os-backend/app/api/demo.py; app/core/agent_runtime/lifecycle.py; app/core/transaction/review.py; product/ai-company-os-frontend/features/data/projectionScope.ts | 0218/0222 | one authority contract, scoped read boundary |
| W3 | Orchestrator/DAG/Runtime | product/ai-company-os-backend/app/core/orchestrator/engine.py; app/core/task_engine/dag.py; app/core/agent_runtime/plan_binding.py; app/core/agent_runtime/transition_command.py | 0219/0220 | canonical plan, member binding, existing transaction path |
| W4 | T1/Event Store/Security | product/ai-company-os-backend/app/core/transaction/port.py; postgres_session.py; postgres_transition_mapping.py; postgres_admission_mapping.py; witnessed_mapping.py; fenced_transition.py; intent_authority.py; app/core/event_store/company_coordination.py | 0219 | atomic writes, CAS, lease, budget, no effects |
| W5 | Skill/Model/Memory | product/ai-company-os-backend/app/engines/model_gateway/runtime_binding.py; app/engines/memory_engine/runtime_binding.py; app/core/agent_runtime/joint_context.py; app/core/skill_review.py | 0221 | local fixture, permission and source binding; disabled real gateways |
| W6 | Research/IV | product/ai-company-os-backend/app/core/policy/iv_review.py; app/core/event_store/terminal_anchor.py; app/core/event_store/plan_history_review.py | 0224 | QA distinct from IV; no release without proof |
| W7 | SaaS/Finance | product/ai-company-os-backend/app/core/event_store/company_coordination.py; app/engines/budget_engine/reservation_review.py | 0219/0220 | scope and shared cap, no spend |
| W8 | Environment/QA | scripts/verify_product.py; scripts/run_pg_acceptance_0215.py; tests/integration/core_0207_source_lock.json | 0218/0225 | locked exact checkout; real disposable PG, backend/Next/browser evidence |

Follow [0218–0225](../implementation_plan/INTEGRATION_SEQUENCE_0218_0225.md) and [traceability](TRACEABILITY.json). Keep original v130 40 cards/v135 24 cards and 11 product targets distinct from 16 integration gates and 24-area maturity. Research-first prioritization does not remove Excel W1 or Obligation; they remain P0 scope beyond first Research slice. No changes to normative domain/phase counts or grants.

## Maintenance, troubleshooting, rollback
Wrong scope: compare immutable run, plan revision, authenticated principal, committed Member and intent; never infer assignment from UI. Unknown receipt: preserve consumed row, journal and independent observations; no retry/reset. Checkout mismatch: stop, compare commit/tree/manifest/lock; do not patch expected hashes. PG failure: preserve redacted report, SQLSTATE and role flags; no destructive auto-reset. UI stale/gap: invalidate projection, resync; no fabricated active state. Revert only this documentation commit on isolated branch if necessary; source and consumed/authority history unchanged. Do not merge main/CI/PROD.

[Technical catalog](../../catalog/revisions/TECHNICAL_CATALOG_0218.json) · [gates](../../progress/INTEGRATION_GATES_0218.json) · [next](../../handover/NEXT_STEP_0218.md).
