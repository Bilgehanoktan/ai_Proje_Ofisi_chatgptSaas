# MI03-GATE02 — Core / OperationsStore / IAM source compatibility
**2026-11-19 · A0/D0 isolated, no authority grant**

## Source-backed finding
Eight exact GitHub file blobs were fetched at candidate `65a0e978c20378041e98f70e6ed074151214a3bb` and checked at source-text level. 12/12 static structural guards matched their expected source contracts; these are **not** executable Python product tests, a new functional PASS, or security acceptance. Earlier 71 selected Python/SQLite tests and CI 42 D0 SQLite tests were separately reported and not rerun here.

## Architecture / ownership
- `durable_ops.OperationsStore.record_assignment_review()` validates the exact ORG history, invokes `assignment_lifecycle.verify_core_reference()` before `append_decision()` and ORG DB commit. `assignment_review()` rechecks retained state and Core reference for accepted D0 records.
- `assignment_lifecycle.verify_core_reference()` imports original `inspect_research_slice()`, `TaskHistory`, `Member`, `derive_request()`. Shared Core/ORG scope: `('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')`.
- `AssignmentPin`, `ApprovalObservation`, `AssignmentReview` remain synthetic. Result always HOLD and has no `authoritative`, dispatch, COMMIT or retry privileges. Revocation and single-acceptance rules are D0 only.
- `org_core_bridge.review_research_binding()` is a historical cross-store reference reader; no current cross-store atomicity or owner-issued permission. Existing Owner, G9, D4/IAM, W8 and IV responsibilities are preserved.
- The missing positive test is a **test-stage dependency closure**, not evidence that the original Core reader is absent from the full 552-file branch. Current 32-file stage excluded `app/core/development_review/research_slice.py`, `app/core/event_store/plan_history_review.py` and further original Core dependencies.

## Technical catalog delta
| Kind | Existing symbols / resources | Change |
|---|---|---|
| Class | `OperationsStore`, `AssignmentPin`, `AssignmentReview`, `Member`, `TaskHistory` | None |
| Function | `record_assignment_review`, `assignment_review`, `verify_core_reference`, `inspect_research_slice`, `derive_request` | None |
| API | No new endpoint | 0 |
| DB | `op_assignment_review` existing D0 candidate; schema not migrated | 0 |
| Dependency | ORG root modules → `app.core.development_review.research_slice` → original Core event/transaction readers | Needs complete pinned source closure |
| Test | Source contract inspection | 12 static checks only; zero product test executions in this review |

## Next integration gate
Original owner Core/ORG team shall run a **positive persisted Research readback** in a complete exact candidate checkout with the original `inspect_research_slice` and real Core transitive imports, then assert OperationsStore readback remains HOLD. Negative tests: stale Core version, wrong principal, wrong member, revoked assignment, expired clock, cross-scope, missing role registry, lost ACK, rollback. Retain separately pinned G9 7, G2 50, 0214 Memory/T1 10, PostgreSQL strict COMMIT and independent acceptance. Do not promote solely on structural PASS.
