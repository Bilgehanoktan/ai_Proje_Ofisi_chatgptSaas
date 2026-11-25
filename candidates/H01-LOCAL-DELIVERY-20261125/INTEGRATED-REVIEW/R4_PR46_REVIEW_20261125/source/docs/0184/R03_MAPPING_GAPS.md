# 0184 R03 mapping gaps — analysis, not a ratification
Sources: database/READBACK_OWNER_MATRIX_0161.md; docs/0158/R03_T1_PHYSICAL_MAPPING_0157.md; app/core/transaction/review.py; app/engines/budget_engine/reservation_review.py; app/core/policy/witness_review.py; 0183 DDL; 0184 local sample. Canonical four tables = state_mutations, idempotency_fences, transactional_outbox, audit_ledger. Fifth consistent readback still UNKNOWN; seven logical entities not assumed physical tables. Logical REQUIRED admission = HEAD/MUTATION/FENCE/EVENT/OUTBOX/AUDIT/ADMISSION/LEASE/BUDGET; terminal adds LEASE/BUDGET to base. These role sets and historical 4/5/7 counts are different abstractions. Do not silently map one to another.
| Logical role | 0184 synthetic evidence | Physical candidate / unresolved |
|---|---|---|
| HEAD / MUTATION | single head CAS, prior 9 regression tests | 0183 head only; canonical state_mutations ownership and version/event mapping HOLD |
| FENCE / LEASE | local lease + review generation, old fence denied | 0183 lease; canonical idempotency_fences and live epoch/clock HOLD |
| EVENT / OUTBOX / AUDIT | event/audit/outbox atomic write + local_review | 0183 event/audit/outbox; canonical relation, claim/send/UNKNOWN readback and authority HOLD |
| ADMISSION | no actual admission | no accepted physical owner or mapping |
| BUDGET | existing reservation_review pure arithmetic only | no durable budget binding, settlement or fifth readback |
| W-A witness | existing witness_review pure reference only | external restore-resistant root and trusted clock not proven |
| Tenant scope | fixed synthetic metadata | real non-owner RLS proof, tenant memberships, privileges HOLD |
 
Next tests after approved mapping: atomic admission failure rollback across required set, repeated idempotency key conflicting digest, CAS contention and stale epoch, budget reservation/settlement unknown, crash around send marker (no real send in D0), non-owner tenant A/B cross-row denial, restore with old witness, authenticated independent readback. PostgreSQL server/driver absent, all these PostgreSQL tests NOT_RUN. No new mapping or SQL migration approved.
