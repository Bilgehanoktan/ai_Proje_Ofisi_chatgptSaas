# P10J22 — Finance & Security Studio

Parent: df4c95688424c7c43d38941d219cf05932dd9040. Scope: read-only source inspection, not live accounting, grant, receipt or execution. Existing FinanceStudio and SecurityStudio model guards/readbacks remain unchanged. New source tabs mount a shared inspector with domain-isolated Turkish multiword search, selected visible row, file path, function, pinned Git blob, requirements and explicit boundary. Finance 3; security 5. Eight backend references verified at candidate HEAD; no backend files edited.

## Changes
- Add controlSourceCatalog.ts, ControlSourceInspector.tsx and ui-p10j22-control-sources.test.cjs.
- Modify FinanceStudio.tsx and SecurityStudio.tsx to mount domain tabs; retain existing tabs and guard checks. Security details only on control/trust views.
- Update product manifest and append W8 wrapper; no dependency, API, DB, Office Engine or runtime changes.

## Maintenance and rollback
Use the source catalog to inspect paths/symbols against pinned backend revision; stale references require explicit review and re-pin, not inferred acceptance. Search is presentation-only and invalid domain/query returns empty. Filter changes clear selected rows. Unknown financial values must stay null/—; UNKNOWN outbox never grants retry. A structural match never grants access, spend or release. Revert the P10J22 branch to parent through a reviewed rollback or create fresh branch from parent; do not reset shared heads. For expansion add domain-specific source references and tests; do not insert mock economic data or receipts.

## Evidence and limits
12/12 isolated model tests; strict isolated TS compilation; 3/3 TSX transpile diagnostics zero; W8 AST PASS only. Full W8, Next build, browser, Windows/native and independent acceptance NOT_RUN. Source grouping and UI copy are implementation choices, not new policy. 491 manifest entries + manifest itself = 492 files; 486 retained pins, 3 added, 2 modified, 0 deleted. No gate promotion.
