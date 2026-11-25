# Trust/custody and staging acceptance plan — 0166
All items NOT_RUN / non-normative. Proposed control allocation: H01 governs risk and scope; separate issuer owns protected policy; registry service resolves authenticated principals; QA and IV have distinct execution/custody; independent W-A outside restore; storage writer is separate from schema administrator. Orchestrator/Engineer have no policy/schema mutation or issuer credentials. PEP cannot be bypassed. No new actual role assignment.

|ID|Control / oracle|Expected|
|---|---|---|
|R11-01|Issuer/key registry pins and real signature over domain-separated canonical payload|Reject wrong algorithm/key/issuer/revision/signature; unknown root HOLD|
|R11-02|Clock and revocation from independent source, same policy/witness epochs|Expired, future, revoked, stale or unreachable HOLD; no fallback|
|R11-03|Restore external witness head, sequence and epoch|Old backup cannot reopen authority; new epoch + fresh admission required|
|R11-04|DDL catalog introspection, table/index/trigger set, ownership, migration identity|Existing mismatched schema or unexpected DDL HOLD; IF NOT EXISTS is not validation|
|R11-05|Unprivileged writer, admin credential isolation, no REPLACE/DDL|UPDATE/DELETE/REPLACE/DROP/trigger disable and schema bypass denied by service boundary; SQLite trigger alone insufficient|
|R11-06|Seven-row batch and actual commit/readback, failure injected after each row|0 or 7 committed; partial batch never accepted; no blind retry on unknown commit|
|R11-07|Two concurrent writers same scope/sequence and same global evidence ID across scopes|One successful commit at most; other conflict/HOLD; durable uniqueness + CAS under trusted owner|
|R11-08|Replay reservation/index and witness receipt bound to scope, plan, policy, evidence hashes|Cross-scope ID reuse, stale sequence, missing reservation or conflicting hash HOLD|
|R11-09|Backup/restore, checkpoint comparison, corrupt bytes|Read-only recovery until external witness and authoritative replay index reconciled|
|R11-10|Artifact byte custody and per-task output readback|Digest plus actual artifact bytes; asserted MATCH not evidence of test success|
|R11-11|Coordinator source review, batch receipt and external checkpoint|Cannot release on three shape matches alone; independent authenticated PRE/POST and real authority separately|
|R11-12|Dashboard projection unknown/missing/stale|HOLD and NOT_RUN; no live agent counts or approval fabricated|

SQLite is D0 staging only. Do not migrate canonical DB or count SQLite commit as T1. For actual implementation choose approved signature profile, canonical serialization, trusted key custody, trusted clock/revocation and protected external witness before enabling anything. No keys generated. No actual SQL, concurrency, restore, signature or browser tests run.
