# AI Company OS — 0181 architecture and technical catalog

## Scope and evidence
CEO-0179=B isolated source/build/synthetic permission; independent PRE/T01/T06, actual grants, external effects, spend, main and PROD stay HOLD. Source commit `a31040d8116a58521393040061abe0078c83800d` on `recovery/0181-mvp-diagnostics`, parent `c3292f873dd4cf85e1f94b07596dc18c08018f01`. 19 source paths (13 add / 6 replace), plus manifest; 163 product files including manifest; 162 manifest entries path/size match. 48 locally reconstructed backend source/test/fixture blobs and 6 frontend test/schema blobs exactly match remote. This is a selected synthetic product test slice, not full product acceptance.

## Architecture
Dashboard -> MvpDiagnosticsPanel -> same-origin GET /api/demo/mvp -> fixed 127.0.0.1:8000 GET /demo/v1/mvp/diagnostics -> inspect_mvp -> existing guarded core/engines -> strict JSON response. Existing six GET endpoints retained. No dispatch, provider, tool, financial effect, real run or persistent store. No automatic request; user triggers readback. Fail closed when any effect flag is unexpected, contract invalid or connection fails.

| Workstream | Integrated / exercised | Open |
|---|---|---|
| W1 | Dashboard panel, TS guard/proxy compiled; 14 Node tests | full Next build, browser, EDS/Office UI |
| W2 | 7 GET routes via TestClient; actual loopback GET 200; schema pair | pinned full integration |
| W3 | existing canonical DAG + plan binding/lifecycle inspection | lease, independent admission, actual run |
| W4 | SQLite :memory: insert/readback/rollback; 8 tests; replay | persistent PostgreSQL, T1, outbox |
| W5 | registry/fallback + disabled gateway, skill/capability inspection | approved provider/tool execution |
| W6 | IV artifact/trust-plane inspection | independent trust root and receipt |
| W7 | wrong-tenant negative tests, synthetic reservation/finance projection | onboarding, tenant DB, real billing |
| W8 | 24 Python + 14 Node; exact source pins, catalog | dependency locks, full suite/browser |

## Files, symbols, API and database
Detailed machine-readable catalog: catalog/revisions/TECHNICAL_CATALOG_0181.json. Main symbols: inspect_mvp (app/api/mvp_diagnostics.py), mvp_diagnostics (app/api/demo.py), inspect_sqlite_replay (app/core/event_store/sqlite_preview.py), parseMvpDiagnostics (features/mvp/mvpDiagnostics.ts), GET (app/api/demo/mvp/route.ts), MvpDiagnosticsPanel, Node test runner. Contract source/generated copies exact. Backend GET no-store; 409 HOLD on invalid projection. Proxy fixed loopback only, 2.5s timeout, no redirects, 16384-byte cap, strict envelope, 503 HOLD. SQLite sample_event(seq INTEGER PRIMARY KEY, event_id UNIQUE, body, digest) exists only in memory, always rolls back and closes. Three fixture events read back; diagnostic remaining 6900 minor units; actual costs, revenues and runs null. Not a persistent transaction proof.

## Actual test record and repeat
Python 24 selected tests: 11 diagnostics, 8 SQLite, 5 plan projection. Node 14 tests: 8 guard, 6 proxy including actual Uvicorn loopback. The first reconstructed subset lacked compatibility facade app/core/dag.py; exact source facade restored, final rerun passed. Uvicorn gracefully stopped. Existing product pins unchanged; test-only direct pins httpx 0.28.1 and jsonschema 4.26.0. Environment Python 3.13.5, FastAPI 0.128.2, Uvicorn 0.48.0, TS 5.8.3; differs from expected pins. Next/React/Phaser absent; network DNS unavailable; npm cache empty. Full pinned lock, full typecheck/build/browser and full backend suite NOT_RUN. No guessed lockfile.

On clean isolated checkout, install reviewed pinned Python and Node dependencies and generate reproducible transitive locks using network-enabled approved environment. Backend: from product/ai-company-os-backend run python -m unittest discover -s tests -p 'test_mvp_diagnostics.py' (likewise test_sqlite_preview.py and test_plan_projection.py); start local Uvicorn app.main:app --host 127.0.0.1 --port 8000; frontend npm run test:diagnostics then npm run typecheck and npm run build; browser test actual panel, fail-closed behavior and navigation. Stop local server. Review test log before status change.

## Failure and maintenance
409 inspect backend graph, fixture, schema and denied flags; 503 check local backend availability/port, response size/schema; UI failures inspect compiled module and browser console; SQLite failure check sequence, event IDs, scope/digest and rollback. Never bypass guard or substitute real data. Extend strict schema, TS guard, source/generated copies and negative tests together. On regression revert source commit on isolated branch, restore parent manifest and verify hashes, retain historical evidence. No main merge or production deployment.
