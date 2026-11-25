# DOC-REV-0225 — Actual integration validation

Base b201833f948f91293414e91000bc53377de9b6d1; product source 6e475e3ea31c22dc9f98f779aa28677546f2696e. Four new test files and manifest only; runtime sources unchanged. No main/CI/PROD, independent acceptance, real agent/provider/tool/spend authorization.

## Verified
- product/ai-company-os-backend/tests/test_research_t1_integration_0225.py: 12/PASS. Original T1 admission, ordinary transition, company event ordering, persisted readback, fault rollback at 15 role-write points; no historical pin admission wrapper.
- product/ai-company-os-backend/tests/test_pinned_research_t1_0225.py: 8/PASS. 0220 scheduled admission with retained pins, 0196L admission-bound transitions, same-cursor plan/company/budget readback, tamper and unknown quarantine.
- product/ai-company-os-backend/tests/test_lifecycle_db_http_0225.py: 5/PASS. Original historical writer, real DB and mounted FastAPI routes, four prefixes and failure terminal, negative inputs; not full ASGI app.
- product/ai-company-os-backend/tests/test_lifecycle_proxy_0225.py: 7/PASS. Real uvicorn loopback HTTP, exact compiled TS proxy and Studio parser; no mock upstream; mismatch HOLD; not React/browser.

81 Python + 53 Node = 134 distinct selected passes (32 new, 102 prior). Five Python tests repeated by Node runner excluded; 15 rollback injection points are subcases, not added to 134. Research root plan reaches VERIFYING v3 with three persisted events; draft/research/merge/qa remain QUEUED; IV/H01 have no run. 20 sample minor units reserved. Historical fixture is a different plan: v1–4 read back from actual writer, v5 FAILED releases 20 sample units with recognized cost 0. Actual HTTP proxy and Studio parser preserve PLAN_REVISION_MISMATCH, no assignment/placement, project/world null. Company read alone may match with a tampered ordinary audit; plan-history read rejects it, so combined read is necessary. No successful release.

## Environment and verification boundary
59 exact local product files and 7 DDL Git blobs; remote 392 manifest entries path/size checked, 393 product files incl manifest. Old mismatched local Provider copy excluded, not used by tests. SQLite dialect adapter strips schema and FOR UPDATE, translates placeholders, uses BEGIN IMMEDIATE; not PG semantics. Selected initial fixture records only seeded; subsequent writes are actual original writers. Python/Node/TS/FastAPI versions in evidence; nonlocked environment, uvicorn legacy websockets deprecation warning. DNS blocked full checkout; no PG binaries/driver. Original SQL6/SQL10/SQL8/DB4 suites were not rerun; new suites give scoped separate evidence, not replacement of those acceptances. 0224 full result archive/witness/authority read remains open. Full product and browser acceptance NOT_RUN. 7/16 gates unchanged. Existing findings 0207-D-01, 0208-D-02, 0209-D-03, 0210-D-04 retained.

## Reproduce
From backend: PYTHONPATH=.:tests PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_research_t1_integration_0225 test_lifecycle_db_http_0225 test_lifecycle_proxy_0225 test_pinned_research_t1_0225 test_research_roster_0224 test_research_company_snapshot_0224 test_plan_projection test_pinned_schedule_0220 test_shared_snapshot_0222
From frontend: AICOS_TSC=<absolute path to tsc JS> AICOS_NODE_DECLARATION=<diagnostic process.d.ts> AICOS_PYTHON=python node scripts/run-studio-0223.cjs
Use temporary isolated DB only; do not apply DDL to production. On mismatch inspect exact plan revision, membership, admission pin, command/audit chain, outbox/fence and budget. Rollback test changes by reverting four test files and manifest together; production migration not required. UNKNOWN must not auto-retry. See evidence and next handover.
