# Teknik katalog v1.14 Delta — 0155

## CHG-0155-01 — dag.py
- Semboller: valid_id, topological_waves, ancestors, validate_release_boundary
- Ne/neden/nasıl: D0 field, graph, QA path checks; no production scheduler
- Teşhis: GraphError: TASK_FIELD_INVALID, DEPENDENCY_INVALID/MISSING, DAG_CYCLE, PRODUCER_QA_BYPASS
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

## CHG-0155-02 — orchestrator.py
- Semboller: parse_plan, canonical_plan, preview_plan
- Ne/neden/nasıl: Deterministic sorted tasks/edges/waves; content SHA-256; v0 projection unchanged in shape
- Teşhis: Compare scope, plan ID, digest, revision; HOLD only
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

## CHG-0155-03 — main.py
- Semboller: plan_projection
- Ne/neden/nasıl: Add fixed synthetic GET /demo/v1/core/plan-projection; GraphError => 409 HOLD
- Teşhis: Inspect local fixture, GraphError, old v0 shape; no runtime call
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

## CHG-0155-04 — core.plan.projection.schema.json / core.plan.projection.json / CONTRACT_PIN.md (BE+FE)
- Semboller: D0 projection v1
- Ne/neden/nasıl: Two new byte-identical schema/fixture pairs; independently prepared reference, not API capture
- Teşhis: Compare pins and shared bytes; no KS/NS acceptance
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

## CHG-0155-05 — planProjection.ts / CorePreview.tsx
- Semboller: readPlanProjection, CorePreview
- Ne/neden/nasıl: Remove independent wave scheduler; static reference guard checks IDs, roles, dependencies, edges, levels, pin; explicit HOLD
- Teşhis: Check PLAN_SCOPE_OR_PIN_MISMATCH, TASK_BINDING_MISMATCH, EDGE_MISMATCH, WAVE_*; no fetch
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

## CHG-0155-06 — tests/test_plan_projection.py
- Semboller: PlanProjectionTests
- Ne/neden/nasıl: Five unittest candidate methods, no extra dependency; NOT_RUN
- Teşhis: Future authorized test run only; compare actual compiler output against reference
- Geri dönüş: bütün R2 ZIP; tek dosya rollback yapma.

API: tek sentetik GET; v0 biçimi korunur, daha katı D0 girdi kontrolü; DB/dependency değişmedi. Dosya hashleri SOURCE_CHANGESET_0155.json.
