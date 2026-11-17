# EXT-02 — Manual engineering guidance candidate
Not an installed skill, not auto-discovered, not a runtime permission. Read repository AGENTS.md, PROJECT_INDEX.md, CURRENT/NEXT and docs/development/PARALLEL_WORK_PROTOCOL.md first. CEO-0174/0179 scope unchanged. The project design and prior decisions take precedence. Based on selected principles of obra/superpowers at 22f0b463e7a5e579904dd6211a520321035526f7; original guidance written here, no upstream executable copied.
## Before work
- Use an existing approved plan; clarify only genuinely unresolved decisions. Define exact file ownership, dependencies, expected behavior, tests and rollback.
- Read current relevant remote heads and complete inventories. Use the existing scripts/parallel_preflight.py with verified common ancestor for real shared-path reconciliation; do not invent a merge grant or rely on the EXT-02 packet linter.
- Verify isolated checkout/worktree and clean baseline; if isolation fails, HOLD, never fall back to a shared directory. Independent tasks may be planned in parallel, but no autonomous subagent launch.
## Implementation
- For new behavior reproduce failing test first, then minimal implementation and refactor. Existing code and historical artifacts are never deleted to satisfy TDD. Characterization tests for legacy behavior are not a fresh RED claim.
- Root cause: reproduce, gather relevant logs/diff and isolate failing layer; change one hypothesis at a time. Don't rewrite unrelated code.
- Review against exact plan, diff and source head. Separate developer review/QA from Independent Verifier. No external session-transcript collection.
## Verification and handoff
- Rerun permitted tests against exact source. Record actual command, environment, exit status, raw evidence hash, coverage and exclusions. Failed, blocked, historical and synthetic evidence are separate; no PASS without evidence.
- Record change / why / location / how, catalog, architecture delta, progress, rollback and handoff. Use revision-specific paths. No auto merge, push, branch deletion, package install, startup hook, visual server, telemetry or config edits by this guidance. Existing repository transfer process remains separate.
- A positive packet lint result is only a request to review evidence, not proof of isolation, ownership, grant, or completion. No runtime execution. See example packet and test harness.
## Manual prompt for Codex / Antigravity
Read the current project rules and this manual candidate as advisory input. Work only within explicitly assigned scope; use the project's existing preflight and approval gates. Do not install Superpowers or activate hooks. If a rule conflicts, preserve the existing project rule; if evidence or isolation is missing, HOLD. Report exact source and actual evidence; never auto merge or delete existing work.
