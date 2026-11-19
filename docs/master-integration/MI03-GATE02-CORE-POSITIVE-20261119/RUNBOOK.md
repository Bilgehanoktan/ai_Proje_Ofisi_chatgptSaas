# MI03-GATE02 — Reproducible execution / diagnosis (D0)
Exact candidate base: \`d6b82dc412b7bb0f048ece2fd43fe83f6627cc59\`. New test is isolated to \`review/mi03-gate02-core-positive-20261119\` and is not an approval or product promotion. Only run in a *complete*, source-pinned isolated Python 3.13.5 checkout with exact original Core SQL fixture dependencies; never on production or existing ORG databases.

From \`product/ai-company-os-backend\`:
\`\`\`sh
python -B -m unittest discover -s tests -p 'test_core_operations_assignment_mi03.py' -v
\`\`\`
First verify \`product/SOURCE_MANIFEST.json\`: 553 entries, including \`ai-company-os-backend/tests/test_core_operations_assignment_mi03.py\`, 10313 bytes and SHA-256 \`1ef392356f7f605cff573069d77da31d9188f874636d1179eb7a3751a32e636d\`. Verify \`git hash-object\` of new test equals \`23c2f019a27bc9e16d8de3f2af72c239eefac035\` (not equivalent to SHA256). Verify original owner source pins in CATALOG_AND_EVIDENCE.json before each run.

Success conditions: ten methods PASS, 0 ERROR/FAIL/SKIP; accepted D0 persists and is reread with exact original \`inspect_research_slice\`; all results retain \`HOLD\`, \`dispatch_allowed=False\`, \`commit_allowed=False\`; negative attempts leave org assignment row count unchanged. Capture environment, test names, stdout/stderr, exit code, relevant Git SHA, hashes, and independent readbacks. Report *only* what was actually executed.

Failure classes:
- \`ModuleNotFoundError test_canonical_research_0224\`: missing original checkout/test dependency; **BLOCKED**, never fix by mocking.
- Missing \`app.core.*\` or SQL fixture: recover exact pinned original transitive closure, no counterfeit data readers.
- SQLite schema/constraint mismatch: check \`schema.sql\`, \`operations.sql\`, \`assignment_review.sql\` owner hashes; no migration or repinning.
- Wrong type or role: inspect exact \`Member\`, \`AssignmentPin\` and \`Staffing\` factories; only owner-approved changes.
- Unexpected role grant, an effect or commit: **STOP/HOLD**; quarantine candidate.
- Already-consumed claim: never reset or downgrade witness / IAM store; use fresh disposable D0 tests only.

Local attempt 2026-11-19: Python 3.13.5 / SQLite 3.46.1; source compile PASS; actual import BLOCKED \`ModuleNotFoundError\`, exit 1; 0/10 executed. Running this exact test via GitHub Actions would **expand** MI-10's existing narrowly scoped CI permission and is not authorized under its current grant. No workflow added.
