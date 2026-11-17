# 0227 — D3 scope review (design only)

Status: NOT_RUN. Based on `docs/0217/PG_RLS_ACCEPTANCE.md`, D2 raw evidence and exact 0227 original DDL inventory. D3 is not a rerun of PG13. Existing 0194 tests include actual row-lock NOWAIT and two-writer tests, but do not prove non-owner multi-tenant isolation.

## Pinned source findings

| DDL | Git blob | Tables | RLS |
|---|---|---:|---|
| database/0192/candidate_event_outbox_fence.sql | 6e4780bf9f267c0926b40d582d5afdbd6faa543c | 3 | Absent |
| database/0193/candidate_run_head.sql | 180924e97ee1f31fa27332941a41e37fdf73017e | 1 | Absent |
| database/0194/candidate_transition_roles.sql | 7b5d374bb7973b283e4fcfa0d796ed6128ef9d27 | 3 | Absent |
| database/0195/candidate_admission_budget.sql | d5dc6abc045da14ef42e88b4e85e50e9062a1b27 | 3 | Absent |
| database/0196L/candidate_lease_settlement.sql | e4c9a84ff705c39486579c393b1f3aaef9e34da9 | 2 | Absent |

Five DDLs define 12 tables; no ENABLE/FORCE RLS or CREATE POLICY. 0193 run_heads explicitly checks synthetic tenant/company/environment; not a canonical two-tenant model. Do not modify these original pins or weaken checks.

## Separate development scope

- First map tenant/company/environment keys and principal-to-tenant authority for all 12 tables, plus dependency/foreign-key and company stream/budget scope. Review current Design Master and open independent-authority findings; preserve historical D0 data model.
- Prepare new, isolated candidate fixture and exact source/test manifest. Separate non-superuser/non-BYPASSRLS owner and runtime logins for tenants A/B; no owner/other tenant role membership; trusted server-authenticated principal mapping; no caller-controlled GUC as sole authority. No use of production credentials or actual tenants.
- ENABLE and FORCE RLS, explicit USING/WITH CHECK for all command types, least privileges and safe connection reset. Test positive same-tenant reads/writes and negative cross-tenant reads, inserts, updates/deletes, forged/missing context, role escalation, owner/SECURITY DEFINER bypass, joins/FKs, rollback and reused connections.
- Real separate connections: lock contention, NOWAIT, shared cap, stale sequence CAS, lock order, rollback and snapshot visibility; verify company/project scope. Capture SQLSTATE, row counts, policy inventory, role flags, source hashes; no secrets.
- Review policy and fixture before execution; use new disposable cluster with independent admin lifecycle, never accepted retry2 (admin was ephemeral and not retained). No source migration, main merge, CI or production action. A fixture-only pass cannot imply canonical mapping or independent security acceptance; assess against D3 criterion explicitly.

## Parallel boundaries

D3 owns isolated database/security scope only. E2/E3/E4 may proceed separately on exact baseline or explicitly reviewed compatible branch; UI/Office branches are not merged here. B3 independent custody remains HOLD. All D3 implementation/execution NOT_RUN in this review.
