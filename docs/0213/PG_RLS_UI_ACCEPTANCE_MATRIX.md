# 0213 PostgreSQL / tenant RLS / backend/frontend acceptance matrix — DESIGN ONLY

This matrix is a non-executed test design, not a SQL migration or a security acceptance.

## Disposable PostgreSQL prerequisites
- Exact reviewed PostgreSQL server version, driver and direct/transitive package pins.
- Isolated disposable DB, test-only database users: migration owner, application writer, reader, tenant-A and tenant-B nonowners; neither test principal may be superuser, BYPASSRLS or table owner.
- Apply only reviewed candidate schemas 0192–0204C in disposable namespace with FK/CAS/trigger compatibility checks.
- Explicit authenticated tenant context must be bound server-side to a trusted identity. A tenant-controllable custom GUC alone is *not* trusted: a client can forge it. Do not publish or depend on such a policy for security.
- Transaction isolation, lock timeout, recovery behavior and role grants captured as exact evidence.

## Required real database cases (NOT_RUN)
1. Run head CAS: one winner under concurrent UPDATE.
2. Same transaction writes head, mutation, fence, event, audit and outbox; injection before commit rolls back all.
3. Admission + shared budget reservation atomic CAS, no overcommit.
4. Renewal lease revision and heartbeat monotonicity.
5. Failure settlement releases reservation atomically; terminal anchor references original mutation and settlement.
6. Unique effect/idempotency collision fails closed.
7. Lost COMMIT response classified UNKNOWN and independently reconciled; never auto-retry.
8. Two projects concurrently reserve shared pool: authoritative current revision, one coherent event order.
9. Cross-tenant SELECT returns no foreign rows.
10. Cross-tenant INSERT and UPDATE violate WITH CHECK, preserving both tenants.
11. Cross-tenant DELETE cannot remove foreign rows; tenant-scoped unique constraints do not leak.
12. Owner/nonowner role boundary: FORCE RLS where appropriate; no BYPASSRLS; SECURITY DEFINER search_path and roles reviewed; no forged session tenant.
13. PostgreSQL lock order, timeout, deadlock and connection reuse/cleanup under concurrent claims.

## CEO Dashboard and Office browser contracts (NOT_RUN)
- Read-only historical projection requires fully reconciled Event Store/Terminal Anchor snapshot and explicit provenance (commit, timestamp, scope).
- UI must distinguish ACTIVE_VERIFIED, HISTORICAL_SAMPLE, UNKNOWN, HOLD; historical records do not become live agent positions or CEO revenue KPIs.
- Browser tests: Dashboard reload, stale snapshot, timeout/503, tenant switch, websocket disconnect, office floor/avatar no synthetic movement masquerading as actual runtime.
- Require full Next.js and backend installed source+locks before build and browser claims.

Status: no PostgreSQL server/psycopg in current isolated runtime; full 0213 checkout and frontend dependencies absent. Every case is NOT_RUN. No permissions or normative migration inferred.
