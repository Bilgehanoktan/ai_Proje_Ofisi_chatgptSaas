# DOC-REV-0177 — Executive Design System integrated source candidate
Base 889796c5878c5c9cba342869cfa0c7664cd99080. Full frontend candidate under quarantine/0177/frontend (Git tree a5fe3be5c456aaa932135f80ed51954899d04b59), cloned from pinned R11 frontend tree 12eaaf95a34ab7006f27bbdcb728887821e75295. Product tree and product/SOURCE_MANIFEST.json remain unchanged. CEO-0174 user approval covers development, but PRE/T01/T06 independent promotion remains HOLD. No PROD, CI, main merge, paid calls, real data or agent execution.
## Architecture
Next.js / React / Phaser remain unchanged; no new dependencies, API, DB, event or contract changes. EDS is view-only. Original 13 navigation entries, floor/display reset, scene and geometer fallback, station list, JOIN_HOLD, plan validation, DAG selection, replay gap and reason codes retained. All four KPI fixtures are null; null/invalid values show em dash, numeric zero remains 0. Theme lives in React context; defaults dark on remount, no persistence or network. CSS imported after globals; bridges inherited tokens and overrides known legacy selected/surface/status rules. Original CSS unchanged. No inferred active agents or finance values.
## Technical catalog
| Path (candidate frontend relative) | Responsibility | Change |
|---|---|---|
| design-system/ThemeFrame.tsx | ThemeFrame, ThemeToggle, ThemeContext; local presentation | new |
| design-system/Navigation.tsx | Navigation, NavItem; existing callbacks, /office Link | new |
| design-system/MetricCards.tsx | MetricCards, formatMetric; finite number or em dash | new |
| design-system/OfficeControls.tsx | FloorControls, DisplayControls; typed parent callbacks | new |
| design-system/WorkflowProjection.tsx | WorkflowProjection; guarded PlanTask groups and selection | new |
| design-system/EvidencePanel.tsx | EvidencePanel; explicit user authorization vs independent HOLD | new |
| design-system/eds.css | Theme and semantic tokens, responsive, reduced motion | new |
| app/layout.tsx | ThemeFrame mount and global CSS order | modified |
| features/ceo-dashboard/Dashboard.tsx | Navigation and ThemeToggle, candidate version | modified |
| components/dashboard/MetricsStrip.tsx | existing fixture to MetricCards | modified |
| components/dashboard/OfficePanel.tsx | control composition, preserves scene, link and JOIN_HOLD | modified |
| features/core-review/CorePreview.tsx | WorkflowProjection, EvidencePanel, retains guards | modified |
| features/uiCatalog.json | separates user authorization from normative status | modified |
## Verification
37 source transformation/invariant assertions (including 8 color pair contrast check), selected text/background ratios 13.66, 7.55, 9.16, 10.92, 16.27, 6.31, 7.50, 7.25. These are static source checks only, not browser/WCAG certification. Candidate tree comparison: 6 modified, 7 added, 0 removed, 33 unchanged; package, globals, fixtures and plan guard pinned. Actual typecheck/build/browser/product tests NOT_RUN; 14 acceptance checks remain NOT_RUN. No product runtime evidence. 
## Maintenance and troubleshooting
Theme mismatch: inspect layout import order, ThemeFrame context, inherited vars and selected !important rules. Missing nav: compare 13 catalog entries and callback/route. KPI: inspect fixture, formatMetric; never replace null by zero. Floor issue: inspect parent handlers and layout revisions, preserve JOIN_HOLD. DAG: inspect readPlanProjection and reason code before rendering, do not recreate scheduler. Evidence: distinguish CEO authorization and normative gates. Rollback: candidate is isolated; revert revision changes, no migration or runtime rollback.
## Next
Exact independent PRE on the 13-file candidate delta and R11 baseline; source promotion only if permitted. Parallel W8 pinned archive, dependency lock and isolated execution acceptance; W2 55/20 field owners; W3/W4 T1/lease/UNKNOWN; W5 provenance; W6 IV custody; W7 settlement. R12 readback branch diverged and not merged. No maturity or acceptance counters advanced.
