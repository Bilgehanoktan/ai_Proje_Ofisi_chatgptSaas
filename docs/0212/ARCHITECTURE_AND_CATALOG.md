# 0212 — Core source recovery and original T1/company integration

Parent e39c023f7fc8a8c7b3490e870f82a3109e76967b. 55/55 locked source blobs recovered locally. Existing production code unchanged. Two integration test sources added, exact readback; 348 manifest entries / 349 product files. Original 29 diagnostic tests and 13 new tests plus 10 prior authority checks in one run: 52/52 unittest results; 51 behavior checks and one expected restore residual. Dependency pins differ; not locked acceptance. No full checkout, PG, RLS, full build or live effect.

## Integration and maintenance
- `test_intent_authority_t1_0212.py`: `IntentAuthorityT1Tests.run_t1` wraps original ordinary mapping in `D0IntentAuthority.claim_and_fence`; verifies commit, readback, rollback, UNKNOWN, product-only restore, concurrent claim and publisher lock. Exact witness/journal wrapper remains open. Never restore authority to enable replay.
- `test_company_terminal_0212.py`: `CompanyTerminalTests.execute` composes CompanyCoordinatedMapping with original admission, ordinary, renewal and TerminalAnchorMapping; `chain`, `signed`, `company` verify five ordered events, pool rev 3, outstanding zero, terminal reference and signature. Trigger failures rollback all writes. UNKNOWN readback is evidence only; no replay. Single project, failure terminal; multi-project contention open.
- Initial test harness omitted OrdinaryPin before/lease; fixed fixture call to OrdinaryPin(i,b,target,l), no product source fix. Final 6/6, combined 52/52.
- DB schema/API/dependencies unchanged; existing DDL 0192–0204C only in disposable SQLite shim, no canonical migration.
- Diagnose: compare exact blob pins; inspect claim table, transaction receipt, budget revision and company_event_order; on UNKNOWN do read-only reconciliation. For rollback revert only test additions/docs, not authority/transaction data. No grants or normative decisions altered.

See [evidence](../../releases/GITHUB_READBACK_0212.json), [catalog](../../catalog/revisions/TECHNICAL_CATALOG_0212.json) and [next](../../handover/NEXT_STEP_0212.md).
