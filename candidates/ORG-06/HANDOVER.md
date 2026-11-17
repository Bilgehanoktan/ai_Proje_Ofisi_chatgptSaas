# ORG-06 — Historical canonical organization / Runtime bridge

Parent: 1d0d587d8e42a2f0324712e614b7a85d6245cffa (ORG-05R5R3). This branch adds only `candidates/ORG-06/`. The PostgreSQL execution owner remains ORG-05R5R2-EXEC (51c8ed415cb4e6120d502c5d23b1979413979982 observed); do not launch, modify or duplicate its 26 checks. Core D4R3 f61ffe6ce9748c311b979772affa76977509d896, U3A 8a3b05aadd32b214f3f8988fc9c793f853fbe3d0 and A6 438985fea059f0ffafdfa16f0d090cb854b5fc36 reviewed read-only. No ORG-06 branch was present at start; head observations are not locks. No branch merge, product edit, DB migration, IAM creation, external effect or real agent.

## Architecture delta

R5 PostgreSQL fixture scopes remain separate. Original R3 `persistence.Scope.key()` already supports the same synthetic tenant/company/environment as Core (synthetic-tenant/synthetic-company/A0_SAMPLE_ONLY). Use that *existing* common SQLite scope, never alias PG fixture identities. `org_core_bridge.review_research_binding` directly calls Core `inspect_research_slice` on the caller-owned consistent read-only Core cursor, reusing actual plan, company membership and history reconciliation. It joins the exact task's RunHistoryPin and Member (including run_id, agent_instance_id, principal_id and initial version), uses the canonical TaskHistory role, then calls the R3 OperationsStore query-only read transaction to validate current org head, staffing, project team and retained history pin. The existing `inspect_runtime` validates seat and staffing references. The two stores are separate historical snapshots: no atomic cross-store read, live freshness, IAM provenance or grants proven. Output is a typed HOLD diagnostic; no principal/run/agent instance, authoritative placement, release or dispatch. This is an internal source candidate, not a registered API. Uses R3 private reader methods deliberately; pin them and review changes. Limit scope to existing 0224 Research prefix; not a generic scheduler or task writer.

## Evidence and limitations

26/26 local bridge protocol tests passed with simulated owner modules; actual SQLite connection BEGIN/close was exercised, but mock store does not exercise R3 persistence or Core SQL. Three Python files compiled. 11 full-checkout integration tests are written against the original ResearchFixture + OperationsStore and NOT_RUN; full local checkout/dependency closure unavailable. 12 selected Core files' Git blobs match the parent, current D4R3 and U3A; nine selected R3 blobs pinned. Not a complete source manifest, not a security acceptance. R5 PG tests and older tests were not rerun. No API/Office gate or global maturity promotion. No real IAM, no HTTP or Office Engine execution.

## Use / maintenance

From an exact fresh ORG-06 checkout with original LF bytes (`core.autocrlf=false`) and reviewed original dependencies, run from the repository root:

```
python -m unittest discover -s candidates/ORG-06 -p test_org_core_bridge.py -v
python candidates/ORG-06/test_org_core_checkout.py
```

Second command checks 21 selected Git blobs before importing existing modules. It creates only temporary SQLite files via existing fixtures. Do not run with production/canonical live data. If a source pin fails, compare against exact commit; never bypass by editing pins. For CORE_READBACK_HOLD inspect existing 0224 history, membership and budget evidence; do not fabricate success. For ORG_SCOPE_HOLD do not translate scopes. For ORG_HEAD_HOLD or ORG_TEAM_HISTORY_HOLD reconcile separately retained references; do not retry a write. For ORG_BINDING_HOLD review staffing seat and canonical role; never auto-reassign. For REFERENCE_UNAVAILABLE_HOLD inspect original owner logs locally without exposing paths/credentials. Return to exact parent for source rollback, no DB rollback needed. Design choices: historical Research only, exact member and seat join, no sensitive IDs in projection, use R3 private read methods rather than duplicate reader. Existing independent IV/H01 boundaries untouched.

## Next step

ORG-06R2: run the 11 original-source integration scenarios, fix real failures, then add server-owned authenticated read context to existing Organization Studio API (no new IAM), coordinate A6 Office projection owner for freshness/epoch/geometry and no identity leakage. The PostgreSQL acceptance owner independently supplies its report. Actual live product integration still HOLD.
