# 0169 — Sequential acceptance program / phase 01
H01: “sirasiyla bunları yap”. 10 stage order is retained; parallel subwork within a stage. Independent T01/T06 and DEV/TEST conditions remain HOLD, not self-issued. R11 unchanged (source f716591be84188d792f8a95ea3995a956208b51d; manifest 337d4fa90bd93b2119da4cd7f6eba193e93d18fe).
1. Local MVP: clean archive 141/141, applicable scope, locks, Python/Node installation, backend unit + 6 GET/404, frontend typecheck/build/browser, read-only snapshot/API.
2. Agent Runtime: T1/PEP, lease, heartbeat, cancellation, retry, UNKNOWN and deterministic runs.
3. Model Gateway: authorized loopback Ollama, allowlist, timeout, token count; other providers disabled until separate grant.
4. Orchestrator: canonical DAG, parallel waves, evidence and failure propagation.
5. Live office: event-derived snapshot/SSE/freshness/multi-floor.
6. Memory: tenant ACL/provenance/tombstone.
7. Skill/Tool: manifests, quarantine, PEP and grants.
8. Research, Excel W1, Obligation: independent IV and release gate.
9. Company management: departments, projects, KPI, approvals, budget/accounting.
10. SaaS/production: PostgreSQL T1/RLS, restore witness, independent security/production approval.
Legacy M08/M09 tracked separately in phases 02–04; phase 01 does not prove agent execution. Safety and T1 prerequisites remain applicable before any relevant execution, regardless of stage.
## Actual result
0168 delta 7/7 SHA256/CRC verified. New standalone scripts/verify_source_zip.py and tests/test_verify_source_zip.py, exact readback blob f4d9e978e8bdbdf53341f3d308bcfec8670f1947 and de22584066a4505bf1bffff1a7745ff71eb73c7d. 10/10 synthetic helper fixture tests, not product tests. No extraction/product import. Product archive absent, container DNS failed, bulk connector readback exceeded tool-call limit; 141/141 full SHA256 verification NOT_RUN. 134 product and 24 prior quarantine test candidates NOT_RUN. Package installs, build, actual agents NOT_RUN.
Preflight: download pinned R11 archive, then py -3 scripts/verify_source_zip.py <zip-path>. On MATCH, extract into a clean directory, run 0167 extracted-tree checker. A MATCH is source integrity only, not authorization. Limits 64 MiB/entry and 512 MiB total declared size are local engineering choices, not normative. No product API, DB, event or dependency change; remove helper to roll back.
Pinned archive: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/f716591be84188d792f8a95ea3995a956208b51d.zip
Next: full ZIP preflight and applicable independent DEV/TEST scope; then parallel dependency/test lanes and reviewed FE/BE readback integration. No production/main merge/CI/spend/model calls.
