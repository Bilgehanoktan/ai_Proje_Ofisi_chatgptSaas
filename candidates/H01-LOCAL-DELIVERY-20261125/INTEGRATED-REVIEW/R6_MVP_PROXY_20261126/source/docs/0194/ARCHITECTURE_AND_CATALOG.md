# DOC-REV-0194 — D0 transition mapping, lease recheck, scheduler/readback
Parent: `f7a0258103b72b6052491b162c3a8fe73b99546e`. CEO-0174 / CEO-0179=B isolated source, development branch, local synthetic test scope only. No real grants, providers, customer data, CI, production or main merge. R03 physical mapping and independent acceptance remain HOLD.

## What / why / where / how
- `app/core/transaction/postgres_transition_mapping.py`: new single-use `D0PostgresTransitionMapping`, implements the 0193 transition-specific T1 port; only STATE_MUTATION and exactly HEAD/MUTATION/FENCE/EVENT/OUTBOX/AUDIT. Generic commit, admission, terminal, lease/budget changes denied. Lock run head then lease; compare eight scope fields, grant, policy/witness epoch, reference, heartbeat, expiry and clock. Recheck before readback and reject backward sample time. No real trusted clock or grant validation.
- `transaction_ref` and `lease_digest`: deterministic SHA-256 logical intent and complete lease snapshot (not signatures). Event/outbox reuse 0192 primitives, fence uniqueness denies collisions. Audit persists original lease digest and fence. `verify_transition_rows` reads five auxiliary roles and current head in one transaction/snapshot, exact equality, unique rows. Later head advancement intentionally yields HOLD; historical proof chain is not implemented.
- `database/0194/candidate_transition_roles.sql`: new candidate run_leases, run_mutations and run_audit; extends prior candidate events/outbox/fences/run_heads, no production migration. The schema depends on 0192 and 0193 DDL; no RLS/tenant owner tests; mapping is provisional and only synthetic.
- `app/core/transaction/transition_reconciliation.py`: no blind retry after ambiguous commit. Caller must supply separate consistent read-only transaction. Missing evidence, mismatch or unavailable readback -> HOLD, exact match still HOLD, never sets committed or retry_allowed. Independent verification is not supplied by a sample digest.
- `app/core/agent_runtime/scheduler_review.py`: validates canonical plan via existing compiler and checks every AI task observation is tied to plan revision and synthetic scope, unique task/run ID and causal predecessor success. Independent-verifier/human tasks excluded. Uses existing readiness function; no claim, lease issuance, actual agent or external call.
- `tests/test_transition_mapping_0194.py`: SQLite shim removes PostgreSQL schema and FOR UPDATE, translates %s to ?, BEGIN IMMEDIATE serializes writers. Tests actual persistent local SQLite file and transaction rollback, not PostgreSQL. 25 mapping cases + 10 scheduler cases; 35 PASS. Prior 0193 25 selected mock tests rerun PASS. Interim audit bind-count error triggered 12 errors, fixed by explicit column list + 15 bind parameters; full selected suites then passed. Failure log preserved.
- `tests/test_pg_transition_mapping_0194.py`: 5 opt-in real PG cases, guarded local numeric loopback host/address, named disposable database, non-superuser/no BYPASSRLS, advisory test guard and existing-schema refusal. Only its newly created schema may be removed. All 5 SKIPPED/NOT_RUN; psycopg and server unavailable. No dependency added to product, no actual migration. PG test implementation itself remains unvalidated on PG.

## Candidate mapping
| Logical role | Candidate physical storage | Status |
|---|---|---|
| HEAD | run_heads | ordinary transition D0 only |
| MUTATION | run_mutations | D0 only |
| FENCE | fences | D0 only |
| EVENT | events | D0 only |
| OUTBOX | outbox | D0 only |
| AUDIT | run_audit | D0 only |
| LEASE | run_leases | locked read; no issuance/renewal |
| ADMISSION/BUDGET | unresolved | HOLD |

## Diagnostics / maintenance / rollback
- `D0_HEAD_CAS_HOLD`: reload scope/version; never blindly replay. `D0_LEASE_SCOPE_HOLD` / `D0_LEASE_INTENT_HOLD`: compare run, lease, grant and epochs; reject wrong owner. `LEASE_EXPIRED`, `HEARTBEAT_STALE`, `ERR_WA_EPOCH_STALE`, `ERR_POLICY_EPOCH_STALE`, `D0_CLOCK_REGRESSION_HOLD`: inspect authority and clock, stop before commit. `FENCE_CONFLICT_RECONCILE`: read back independently. `D0_WRITE_SET_READBACK_HOLD` / `D0_HEAD_READBACK_HOLD`: roll back on in-transaction mismatch, post-commit mismatch stays HOLD. `D0_READBACK_INCOMPLETE_OR_UNAVAILABLE`: no retry. `SCHEDULER_RUN_BINDING_HOLD`/`SCHEDULER_CAUSAL_ORDER_HOLD`: verify pinned plan and task history; no dispatch.
- For real PG use an explicitly provisioned new database with name `aicos_d0_0194_<suffix>`, local numeric loopback, non-superuser/no BYPASSRLS. Install psycopg in authorized isolated venv only. Set `AICOS_D0_PG_ACK=0194_DISPOSABLE_LOCAL_ONLY`, `AICOS_D0_PG_DSN` via private environment (never commit it), run `python -m unittest discover -s tests -p test_pg_transition_mapping_0194.py -v` from backend. No automatic environment provisioning; verify fresh database and credentials manually. Do not run against existing DB.
- Rollback: revert isolated 0194 source commit or restore pinned 0193. No actual PG schema applied; SQLite temporary DBs disposed. Do not reset main. Candidate DDL must not be applied to production. No API, frontend, product dependency or normative decisions changed.
- Provisional engineering choices: six-role ordinary mapping and table names; head→lease lock order; synthetic clock recheck and full lease digest; fail-closed strict current-head readback; local SQLite shim and gated PG tests. No official R03 decision, no lease write, worker claim, trusted time, actual PEP, admission/budget/terminal, actual model invocation or IV authority.

## Next (0195)
P0 run existing 0190 PG race and 0194 real PG suite in authorized isolated environment, resolve R03 physical ownership and trusted clock/witness. Develop admission/lease/budget transaction mapping and terminal authority separately, no standalone lease changes. P0 bind worker claim/fencing to canonical readiness and persistent admission; P1 event projection, Memory/Model/Skill/Tool contract integration using local synthetic adapters only. W8 Windows remains parallel, no merge. Full pinned backend/Next build/browser still NOT_RUN.
