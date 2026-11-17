# ORG-10 — Verification and controlled execution boundary

This package is a candidate, not a deployment. Actual PostgreSQL tests are NOT_RUN. No executable server launcher is included; this avoids acting before owner review of the proposed profile. Do not execute bootstrap or acceptance on a running cluster.

## Safe local source-only verification
Use the exact parent archive at `0839ecc5cedc338e791022d287d0a251cf93506f` (or the additive ORG-10 child when published), byte-preserving extraction, and this candidate directory at `candidates/ORG-10-COMMON-SCOPE`. With a reviewed Python installation, from the repository root:

```
python -B candidates/ORG-10-COMMON-SCOPE/derive_common.py --source-root . --verify candidates/ORG-10-COMMON-SCOPE
```

Expected: `EXACT_GENERATED_PASS 6`. This reads files only, does not create a DB, and rejects original or generated drift. Review SHA256SUMS against delivery separately. To regenerate into a *new* directory, use `--output` instead of `--verify`; never overwrite original or generated evidence. To run local fake-DB and static checks, from the candidate directory set `ORG10_SOURCE_ROOT` to the exact repo root, then `python -B -m unittest -v test_pg_protocol test_common_profile`. Expected 55 tests; no PostgreSQL. For a standalone delta archive, `ORG10_SOURCE_ROOT` must refer to the exact full parent containing the six originals.

## Required owner review before real PostgreSQL execution
- Agree on new DB/schema/cluster and proposed port 55436, check current machine and active development ownership. Do not reserve or run this port merely from this document. No old R4/A/B aliasing; no shared credentials, role memberships, FDW, dblink or assumed cross-database transaction.
- Fresh independently reviewed PostgreSQL 17.12 binaries/driver hashes and separate psycopg[binary] 3.3.9 environment, non-admin OS account, no inherited PG variables, no production data. Separate new ASCII data directory, explicit C/UTF8 initdb and SCRAM, loopback only; verify cluster identity (data directory, process, port, database, server version, current/session user) locally before bootstrap and schema. Do not disclose secrets or personal paths. Existing 55433/55434/55435 and any application DBs stay untouched.
- Review exact bootstrap and DDL before execution. Bootstrap requires named `org10_admin` and a fresh PG17 cluster with only built-in databases and system roles. The guard is not independent server custody. Install only in approved new cluster, separate passwords for each role, no saved passwords. Schema guard validates name, port, loopback, PG17, admin and role flags/membership. No production migration.
- After owner review, approved isolated launch, source/hash/driver review, and actual role/schema creation, the runner accepts only `--execute-disposable --port 55436 --report <new report path>` in the exact source tree. No automatic installation, server start/stop, or retry. It asks for four fixture-role passwords; never pass credentials in CLI or logs. It preserves partial results and uses an exclusive report path. Existing DB and reports are never deleted. Do not use the old R5 reviewer for this new 31-check matrix.
- Evidence acceptance must verify original report bytes, source and binary hashes, sanitized bootstrap/start/stop, 31 exact ordered test IDs, outcomes, SQLSTATEs, ACL details and actual cluster identity; independent custody/authority remains separate. On failure preserve stage and inspect, stop only positively identified new stage with matching pg_ctl, no automatic retry/cleanup. On UNKNOWN do not reopen same intent or repeat writes.

## Remaining work
After fixture execution, build the distinct common-scope join with the existing Core readback and ORG reader using retained pins from both owners; no automatic cross-store atomicity. The fixture runner's demo project/plan are not the canonical Research plan, and it does not authenticate IAM. No product route or Office geometry is activated.
