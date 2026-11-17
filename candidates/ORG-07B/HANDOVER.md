# ORG-07B — Original R3 SQLite / Studio API integration

Parent: a2f4461d558af0f69e51cf1570ccea64b7d9ac20 (ORG-07A). Initial inventory 189, second 190 branches. ORG-06R2 fd91b58e030e4dd74274a58878c48d0616456b34 still reports 11+1 NOT_RUN; separate owner, no duplicated run. ORG-05R5R2 PG evidence branch ba6c72a2508e3eab579c33f48e52008d1d601897 is separate and not accepted here. Core D4R6, U3A, W5, Office A6 and Premium UI remain unmodified. No merge, CI, live agents, external effect, new IAM or DB migration.

## Architecture and evidence
Existing ORG-07A router -> original R3 studio_read -> Store.studio_view -> disposable SQLite. Restored 11 exact R3 files and verified 3 ORG-07A Python blobs from pinned GitHub content before execution; partial dependency closure for these tests, not complete repo checkout. All inherited 6 ASGI/SQLite tests pass. Added 6 supplementary actual SQLite/ASGI checks (company/environment mismatch, non-demo principal, unknown credential, revision refresh, byte stability and identity omission). 25 transport tests rerun PASS with simulated reader. 37 selected local tests this round: 12 actual R3 SQLite/ASGI, 25 transport. No real IAM: test resolver and clock are synthetic. FastAPI/Starlette observed versions differ from historical product pins; no full product build. No product source changes, no authority promotion. No cross-store Core binding proof yet. EVIDENCE.json records exact pins, counts and environment. Logs are raw local output.

## Product composition gap / next ORG-07C
The existing app/api/demo.py is the router registration owner, but no authenticated server read context was established. identity_registry.py explicitly labels principals as unauthenticated. The current frontend projectionRead.ts allowlist has no organization key; useProjectionRead.ts differs on Unified U3A/Premium UI from this branch. Do not extend that older file or add a second session system. Coordinate existing backend IAM owner and UI/proxy owner, preserve same-origin/no-store/size cap/abort behavior, and obtain ORG-06R2 evidence before registering the route or binding Office. No client-selected tenant/path/head, no credential in browser storage or URL. Keep existing R3 schema and read-only HOLD response. ORG-08 remains separate.

## Reproduction / maintenance
From the exact source tree (or the supplied partial reconstruction with 14 pinned files), use reviewed isolated Python environment. Run from root:
- python -B candidates/ORG-07A/test_studio_original.py
- python -B candidates/ORG-07B/test_studio_boundaries.py
- python -B candidates/ORG-07A/test_studio_router.py
Original test verifies R3 pins; supplementary checks also verify router/test pins. If a pin fails, restore exact bytes; never weaken checks. All SQL writes are temporary fixture setup/negative tests. 403 generic: inspect trusted scope, resolver expiry/permission, retained head and notice integrity locally without logging credentials. Rollback: remove only ORG-07B delta; no persistent migration or route registration to undo. Full checkout and dependency lock, IAM, Core bridge and product integration remain HOLD. No global maturity score change.
