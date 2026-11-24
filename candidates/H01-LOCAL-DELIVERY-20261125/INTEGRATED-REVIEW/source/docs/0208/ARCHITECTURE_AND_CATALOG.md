# DOC-REV-0208 — D0 Joint Runtime Context

Baseline `9bbc4bed75c56a36bcacc8c430a79bf3612aa85b`; source `596529ed3d3de59b29065239b42033774e31af6e`. 338 product files / 337 manifest entries. Two additions, one append-only module change; 334 prior non-manifest blobs unchanged. No API/DB/event/schema/dependency version change.

## What / why / how
New `app/core/agent_runtime/joint_context.py` binds exact SnapshotPin generation, metadata/graph SHA-256 and InvocationEnvelope/registry digest. `inspect_joint_context` uses two read-only SQLite observations around the existing model inspection. Memory access checks run/version/attempt, lease and fence, policy/witness epochs, complete tombstone/ACL and lineage, provenance; model input bytes must equal the approved source span. The new `inspect_stored_memory_input` is appended to snapshot_store.py; existing reader unchanged. Model and memory permissions remain false; no raw bytes, receipt, actual tokens/cost or selected model returned. This is intentionally a single source-span D0 profile, not arbitrary/multi-source prompt assembly.

## Evidence
98/98 selected actual local cases: 72 regressions, 26 new (zero failures/skips). 31 exact product source files hashed; remote 55-file core lock content read and rehashed (49 SHA-256 matches; 6 SQL git SHA-1/size matches). Only 8 of those 55 files available locally, 47 absent. New source/test bytes match Git blob readback. [Evidence](../../tests/evidence/TEST_EVIDENCE_0208.json). 29 core/lifecycle cases, full T1, PG13, full build/browser NOT_RUN.

## Open P0
D-01: D0 joint inspection implemented and tested; independent legacy reader remains available as a diagnostic, no mandatory effect boundary. D-02: old DB copy plus old external caller pin can structurally match; restore-external latest witness required. Double read catches committed revocation between reads, not revocation after final read, or true effect atomicity. No security acceptance or actual grant.

## Parallel review
C: exact original T1 coordinator/transport and CompanyCoordinatedMapping/TerminalAnchorMapping inspected. Correct terminal composition is outer company mapping, inner terminal anchor (which delegates lifecycle writer), original T1 commit, same cursor. Ordinary transitions use original commit_transition; terminal-only anchor lacks transition methods. Actual full composition NOT_RUN. E: Dashboard already has manual historical task-budget/lifecycle/prefix readbacks, fixture geometry separate; no active KPI or new integration. G: Chromium installed, full source checkout blocked, frontend deps absent, backend pins mismatch. F: PostgreSQL binary and psycopg unavailable.

## Diagnosis, maintenance, rollback
Verify product manifest `268f575b534bda97d8ed57a1f7f3f4de8bdf62cd`. Joint mismatch codes: JOINT_CONTEXT_DIGEST_HOLD, JOINT_INPUT_SPAN_HOLD, MEMORY_SNAPSHOT_CAS_HOLD, STALE_HOLD, MEMORY_ACL_DENY, MEMORY_LEASE_HOLD. A matching result is not an execution token. Preserve original 0207 lock/runner. Reproduce local slice with Python 3.13.5/SQLite 3.46.1 using unittest discovery. Full checkout with approved pinned lock required before 29 tests and build. Roll back to exact 0207 commit, no schema migration. Retain independent evidence; no CI/main/PROD/provider calls.
