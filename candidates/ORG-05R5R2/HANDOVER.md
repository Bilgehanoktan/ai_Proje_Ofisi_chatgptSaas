# ORG-05R5R2 — offline evidence review delta

Parent: `a49c20d8e0e9d1e69400a710385a5434b43f577c` (ORG-05R5). R4 controlled parent `49499807a9a0c37d34375a17d1f5fbacc31ac4b3`; independent R4-PG `fd083f15bd8523aed5130ade021ed5d9b079d27a` remains separate.

Architecture: preserve existing R5 PgOperations, R3 validation, R4 schema, T1 and IAM ownership. New offline review tool has no database connection, no migration, API, or external event. It checks 12 R5 files plus 7 R3 files and one R4 SQL pin, and validates the existing 26-check runner report without claiming provenance. A complete report remains UNATTESTED and HOLD until raw execution evidence and independent scope/custody review. The parent runner is unchanged. This is an acceptance tooling delta, not product integration. No source or acceptance promotion in Core, U3, W1, A6 or independent security.

Actual local tests: 20/20 synthetic JSON report validator tests, Python 3.13.5; 2 files compile. PostgreSQL server/client and psycopg absent; DNS download unavailable. PG 0/26 executed, prior 29 protocol and 141 R3 tests not rerun. Full source preflight across a checkout not executed here. Fixture report tests do not demonstrate PG behavior. Report can be fabricated and cannot establish custody, runtime identity or authentic execution. Design choices: strict exact report fields/sequence, fixed driver 3.3.9 per parent runbook, report size 64 KiB. No new authority.

## Use
From a fresh verified checkout of the pinned parent or isolated child containing this delta, with Git byte preservation (`core.autocrlf=false` before checkout), run from repo root:

```powershell
python candidates/ORG-05R5R2/review_pg_evidence.py --candidates candidates
```

Only after independent review of the existing R5 RUNBOOK.md, run the existing 26-check acceptance on a NEW disposable PostgreSQL 17 cluster (not Core/U3). Do not reuse ports or directories. After generating the report:

```powershell
python candidates/ORG-05R5R2/review_pg_evidence.py --candidates candidates --report candidates/ORG-05R5/ORG_R5_PG_RESULT.json
```

`COMPLETE_REPORT_UNATTESTED` is not acceptance. An incomplete or malformed report returns exit 2; preserve failed stage and logs. If SOURCE_HASH_MISMATCH, compare exact bytes against pinned commit; do not regenerate pins or normalize newline silently. If REPORT_PINS, inspect driver and original runner. If status contradicts results, do not retry blindly. Unknown commit/cleanup HOLD follows parent runbook; no destructive rollback. Source rollback: return to pinned R5, do not apply database rollback. Next: real PG run, raw evidence review, resolve failures and then coordinated canonical identity/API integration and Runtime/Office readback.
