# 0222 → 0223 — Agent Studio / Workflow Studio

0222 common historical CEO/Office source candidate landed at 7dbb696f8f3d5b639d2a00765566babd4108cf93. 39 selected checks + 18 positive payload schema checks, 2 TSX syntax checks; actual prefix DB integration and full browser acceptance NOT_RUN. 7/16 integration gates remain. Do not close UI-03/UI-05/UI-07/BE-01/BE-02 as live acceptance.

P0 W1/W2/W3: inspect existing Agent Studio, Workflow Studio, design-system/WorkflowProjection.tsx, projectionScope.ts, historicalJoin.ts, canonical plan, scheduler and existing project history readback. Reuse SharedSnapshotProvider only for exact compatible historical profile; do not infer company/project/world or task-run association from display labels. Keep missing or mismatched lineage HOLD; preserve static layout, read-only controls and no actual dispatch, edit/publish or provider call. Show task identity, dependencies, evidence lineage and known vs unknown status; avoid a second task engine or independent live cache.

P0 W8 parallel: actual fixed-prefix SQLite route test using exact historical DB writer/reader, full browser CEO/Office navigation, shared invalidation and timeout test, pinned dependency build. Run 0219/0220/0221 composed SQL, PG13/RLS, locked29 only in permitted isolated environment. DNS/driver/checkout remain blockers; no CI/main/PROD. Authenticated canonical project/world scoped SSE with retained cursor and verified lease/placement still pending; design as reuse of existing postgres_snapshot/plan_history_review, not arbitrary fixtures.

P1 W6: maintain Research end-to-end path for 0224, preserve QA/IV and result evidence-only constraints. 0225 full build and MVP evaluation remains the planned milestone.
