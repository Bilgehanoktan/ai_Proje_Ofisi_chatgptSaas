# R03 — 0190 historical source reconciliation
DESIGN_REVIEW / PHYSICAL_MAPPING_HOLD. No migration or owner acceptance.
Direct source: AI_Company_OS_DESIGN_MASTER_V11_6_135_RC1.md from the user archive, SHA256 01e2258cb71a97f60a7a48aaef8a3282c905c32443cf3bd5d61a78ee5b93d0f9, 12,011,382 bytes, 119,818 lines. v112 DDL lines 29132–29214; dispatcher 29215–29226; v122 D07 13655–13664. v122 expects five consistent readbacks after abort, but does not name the fifth. Historical DDL is design only. 0155 recovery source corroborates this (SHA256 b812f48d155d03bf717a6cc5a6d9f3770db72da01404622890a4fa7ef0fc8fd2, lines 30751–30833 and 15276–15283).
Current references: database/READBACK_OWNER_MATRIX_0161.md; docs/0161A_REVIEW/T1_MAPPING.md; docs/0184/R03_MAPPING_GAPS.md; transaction/review.py, readback_review.py, admission_bundle.py, port.py. Four physical tables, five historical readbacks, seven historical logical entities and nine admission roles are distinct.
| Role | v112 physical evidence | Gap |
|---|---|---|
| HEAD | state_mutations unique tenant/aggregate/committed_version | history is not authoritative head lock; initial absence/CAS and full scope |
| MUTATION | state_mutations expected/new version, request digest, epochs | before/after state and full scope |
| FENCE | idempotency_fences tenant/effect uniqueness, request digest, status | full scope, retry versus conflict, generation and UNKNOWN |
| EVENT | transactional_outbox event_type and payload digest | digest is not canonical causal event; sequence and causation |
| OUTBOX | transactional_outbox composite tenant/run FK to mutation and fence | FK direction alone does not enforce complete writes |
| AUDIT | audit_ledger tenant/run/seq and entry hash uniqueness | bind exact mutation, fence, event, actor and chain |
| ADMISSION | absent | grant, scope, lease, budget; first-acquire |
| LEASE | outbox claimant_lease_expiry_utc | claim lease differs from run lease; holder/generation/clock |
| BUDGET | absent | limit revision, reservation, settlement, UNKNOWN |
| fifth readback | UNKNOWN | cannot infer head or budget from count |

v112 uses UUID tenant/run; 0183 candidate uses synthetic text scope. Company/environment columns absent in v112; Scope in current logical contract has eight fields. RoleObservation record_id is not physical row identity. HeadReadback currently pins expected precommit version, not committed head receipt. CommitIntent lacks budget reference and DisabledT1 remains. First lease acquisition differs from validation of a current lease.

## Design directions
A: explicit lockable head and separately bound admission/lease/budget records in the same PostgreSQL transaction; preserve four names and resolve physical event ownership. More objects, clearer constraints and contention. B: reuse an existing authoritative aggregate store and combine some roles only after same-transaction ownership is demonstrated; fewer objects but complex constraints, no evidence yet of such a store. C: keep operation-based review without schema approval, as current direction.
Engineering preference A for future review, not a ratified mapping. C stays the current review boundary. Do not identify any new table as the historical fifth. No owner appointment or acceptance.

## Required canonical verification
ADMISSION: head CAS, grant/epoch, admission, lease, budget reserve, mutation/fence/event/outbox/audit in one unit; late failure at each write and duplicate reservation contention.
STATE_MUTATION: base six roles plus lease/budget when changed; stale version, scope, missing event/outbox, digest conflict.
TERMINAL: base, lease close/fence, budget settle or preserve UNKNOWN; no reopen.
RENEWAL: authoritative existing lease, generation/heartbeat/epoch/clock; reject stale owner.
OUTBOX_CLAIM: persisted intent, claim CAS and fresh policy; external call outside T1 and currently unavailable.
RECONCILE: exact correlation and independent receipt, outcome and audit; missing proof retains UNKNOWN.
Canonical tests NOT_RUN. Need owner mapping, full scope, postcommit consistent readback, fault injection, multi-tenant role evidence and independent trust roots. 0183 candidate is not canonical. Next: actual 14-check PG probe, owner review, then implement in existing T1Port and transaction modules rather than another sample engine.
