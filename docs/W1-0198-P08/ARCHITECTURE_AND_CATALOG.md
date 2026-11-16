# W1-0198-P08 — persisted Office HTTP diagnostic and reader hardening

Parent `3a744286bb1dd3702f4065f4d23eddf92465a480`. Scope: Actual D0 writer, original Office FastAPI router/Uvicorn and compiled Next GET/parser via Node HTTP wrapper; not full app.main, Next, React, PostgreSQL, live authority or independent acceptance.

- Source closure: 32 exact product files; one changed runtime source. Initial seeded 13/13, actual writer 18/18, then final 26/26 after hardening. Overlapping runs are not additive. Three P07 malformed DB profiles accepted: event view, unrelated trigger, WAL sidecar. P08 rejects them.
- Changed: `product/ai-company-os-backend/app/core/development_review/office_workbench.py`, new helpers `_workbench_snapshot`, `_authorizer`; `read_office_workbench` uses bounded read-only snapshot. Ordinary required tables, no views/triggers, DELETE journal, reject -wal/-shm/-journal, trusted_schema=OFF, allowlist authorizer, 8 MiB file cap and 1M VM-step budget. Optional sample_pair table accepted. No schema/API/UI/dependency change. Requires SQLite >=3.37 for table_list. No full DDL attestation or hostile filesystem race proof.
- Actual Workbench writes five sequential tasks; HTTP reads match backend and compiled frontend proxy; DB SHA256 unchanged on GET. Test wrapper POST rejection is not Next integration. Actual D0 fixed sample adapter only, zero real provider or spend. Pair-table compatibility is not atomic paired budget regression.
- Dependencies unavailable: DNS github.com/pypi.org/registry.npmjs.org; local runtime differs from pinned versions. No downgrade or dependency pin modification. Full checkout/build/React/PG and full seven-route parity NOT_RUN. Independent acceptance HOLD.
- Reproduce in isolated checkout: `python -B tests/integration/run_office_http_p08.py --writer --type-roots <installed @types dir> --report <new report.json>` (diagnostic only). For 503 inspect path, sidecar, journal, schema and DB size; preserve malformed DB as evidence; do not auto-repair. Rollback: select parent commit, no DB migration. Do not merge main or expand runtime authority.
- Evidence: [index](../../tests/evidence/TEST_EVIDENCE_W1_0198_P08.json); [catalog](../../catalog/revisions/TECHNICAL_CATALOG_W1_0198_P08.json).

## A–H
- A: PARTIAL_DIAGNOSTIC_26_PASS — Full pinned checkout/install and regression remain blocked by DNS; available versions differ.
- B: OFFICE_ROUTE_DIAGNOSTIC_1_OF_7 — Full seven-endpoint product HTTP parity remains 0/7 NOT_RUN.
- C: CANONICAL_CEO_BINDING_HOLD — No canonical run binding or live CEO change.
- D: D0_OFFICE_READER_HARDENED — Actual persisted D0 role counts 6/6; trusted time/placement still HOLD.
- E: D0_WORKBENCH_WRITER_PROVED — Five DAG tasks, dependency/lease/IV/idempotency verified; canonical lineage remains HOLD.
- F: D0_FIXED_MODEL_SAMPLE_ONLY — No live provider, reservation or Memory ACL proof.
- G: D0_SQLITE_GUARD_PASS — No canonical ledger/security acceptance; optional pair table compatibility only.
- H: NOT_RUN — Full build/browser/accessibility pending.
