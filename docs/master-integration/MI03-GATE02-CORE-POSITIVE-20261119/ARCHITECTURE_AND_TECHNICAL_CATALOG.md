# MI03-GATE02 — Original Core ↔ OperationsStore persisted D0 readback candidate
2026-11-19 · **TEST CANDIDATE / NOT_RUN** · Core/ORG/IAM owners retain authority.

## Architecture
This candidate adds one new unittest module to the unchanged original MI03 GATE03 owner source (commit \`d6b82dc412b7bb0f048ece2fd43fe83f6627cc59\`). It directly reuses the original \`ResearchFixture\` and its SQLite Core records, original \`inspect_research_slice()\`, \`OperationsStore\`, \`derive_request()\` and \`AssignmentPin\`. No mock reader, no second IAM/ORG engine.

Intended call: synthetic Core persisted Research plan → \`derive_request()\` → historical Core consistent read cursor → \`record_assignment_review()\` with independent ORG snapshot → fresh ORG SQLite assignment row → \`assignment_review()\` with exact retained pin → **HOLD**. Countercases exercise wrong principal, old version, role, member, scope, revocation, persisted Core drift, and unavailable reader. This is not the authoritative issuer chain: approval identifiers are synthetic observations; cross-store concurrency/atomicity is unproven.

## Catalog delta
| Kind | Exact symbol/path | Delta |
|---|---|---|
| New test | \`product/ai-company-os-backend/tests/test_core_operations_assignment_mi03.py\` | +1 (10 methods; NOT_RUN) |
| Manifest | \`product/SOURCE_MANIFEST.json\` | 552 → 553 entries, new test byte-pinned |
| Existing classes | \`OperationsStore\`, \`AssignmentPin\`, \`ApprovalObservation\`, \`ResearchFixture\`, \`Member\`, \`Scope\` | 0 changed |
| Existing functions | \`inspect_research_slice\`, \`derive_request\`, \`record_assignment_review\`, \`assignment_review\` | 0 changed |
| API/routes | None | 0 |
| DB | Existing \`op_assignment_review\` D0 schema; fresh disposable file only | 0 schema changes |
| Runtime dependencies | Existing original Python modules and SQLite SQL fixtures; no new packages | 0 |
| Test evidence | Python 3.13.5 \`py_compile\` PASS, AST 10 unique, native Git blob and SHA-256 match | No functional PASS |
| Acceptance | Core 12/16, MVP 0/11, IV/security 0/7 | Unchanged |

## Diagnostic result
The test script was executed in the temporary local workspace. Import failed at \`test_canonical_research_0224\` because the exact product checkout is unavailable locally. Exit 1 is an environment/import **BLOCKED**, not a failed positive integration assertion and certainly not a functional PASS. The original 71 and 11 and 42 selected tests are separate historic evidence and were not repeated.

## Owner next steps
1. Review actual source/test schema and source manifest at the immutable base SHA; do not repin the shared source.
2. In an isolated **complete** exact checkout with original Core transitive SQL modules and reviewed pinned dependencies, run the exact 10 unittest methods.
3. If failures identify fixture/source errors, record diagnostics, repair only in a controlled owner-owned candidate, rerun and retain before/after evidence.
4. Only after D0 positive suite and owner review: independently test authenticated assignment/role issuance, G9/G2, Memory/T1 fullchain, strict PostgreSQL COMMIT, rollback, stale readback and W8. No implied authority.

## Rollback
Revert the added test + candidate SOURCE_MANIFEST.json entry on this review branch; source base \`d6b82dc412b7bb0f048ece2fd43fe83f6627cc59\` and \`integration/product-dev\` / main remain untouched. No database migration, claim reset, CI workflow, or production operation.
