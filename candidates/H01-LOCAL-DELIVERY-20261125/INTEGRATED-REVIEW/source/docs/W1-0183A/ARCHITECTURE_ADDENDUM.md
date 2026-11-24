# W1-0183A — Workflow Studio and role detail
Parent 02e94c07fa8b56668b322184b95f1af2f3e76123; isolated branch w1/0183a-workflow-studio. Other chat's backend/runtime work is not merged or edited. CEO-0174/0179=B apply; runtime and independent security unchanged.

## Actual source changes
- EDS-07: replace WorkflowProjection's wave list with a horizontally scrollable SVG dependency graph, graph/list switch and direct predecessor/successor context. The already validated canonical plan waves are consumed, not re-scheduled. All tasks remain HOLD; no dispatch or release.
- EDS-06: seven role details now show differentiated static descriptions; instance, model, grant, cost, QA and IV remain absent or unverified. No agent creation.
- W8: standalone strict TypeScript compile and eight Node tests passed on local 5.8.3/22.16.0; this is not a Next build or React browser result.

## Scope and design choices
Fixed column/row sizes, maximum 100 tasks/waves, bezier edges, local selection and list fallback are presentation choices, not normative domain decisions. Edges can cross intermediate nodes for general nonadjacent waves; edge routing and label overflow for arbitrary future datasets are not accepted. Existing exact D0 fixture has 7 tasks, 7 edges, 6 waves. No extra packages, API, DB or contract changes. No real agent/provider, spend, CI, main merge or PROD.

## Maintenance and rollback
Check planProjection guard first on HOLD; then graph helper and CSS. Build and browser-check both themes, mobile horizontal scrolling, keyboard navigation, 7 nodes/edges and role detail tabs. On conflict cherry-pick only five W1 source paths onto latest authorized integration branch, then regenerate manifest from target tree. Do not overwrite other chat's progress or handover. Revert only W1 changes if needed. See technical catalog and exact scope.
