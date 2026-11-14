# 0165 / R10 — bounded integration and review foundation
User selected six explicit tasks. Exact six 0164 source blobs promoted into isolated product source tree; prior quarantine preserved. Dashboard adds static DevelopmentReviewPanel and wires it into İş ve Denetim; no live source. Four new backend modules and 18 test methods are quarantined. No real agents, DB execution, grant, provider, tests, deployment or main merge. 0163 exception was exhausted; this is new owner-directed one-turn source-only scope.
 
## Six work packages
1. Identity registry: frozen RegistrySnapshot, roster SoD and issuer/custody separation, scope/epoch/reference digest comparison. Labels are not authenticated principals.
2. Trusted policy: frozen PolicySnapshot, separate expected hash, registry/plan/scope binding, expiry and revocation check; no issuer or writer. Real protected storage, signature, clock, revocation authority and IAM remain open.
3. Evidence store: isolated SQLite staging candidate with explicit caller-owned connection, 7-row atomic batch, BEGIN IMMEDIATE, unique scope/sequence and evidence IDs, chained entry digests, UPDATE/DELETE rejection triggers, readback. No DB created or SQL executed. Not canonical Event Store/T1; file owner can bypass triggers, independent custody/restore/replay across scopes remain open. No raw output custody.
4. Coordinator: policy → exact patch bytes → evidence chain; all source_write_allowed/dispatch_allowed/release_allowed false. Staging separate, no write from coordinator. No actual scheduling or integration API.
5. Six original R10 files byte-identical (Git blobs pinned). Product manifest updates 132 entries, 133 product blobs. 0164 scope's test SHA-256 was truncated in GitHub record; new pin correct from original local verified package, unchanged blob. No rewriting previous record.
6. Dashboard static seven-stage review panel, NOT_RUN and HOLD. No actual agent activity or decisions. Existing UI intact.
 
## Evidence
Prior 0164 ZIP 21/21 manifest and CRC verified. 11 Python AST and two TypeScript 5.8.3 TSX parser checks, zero parse errors; no import/typecheck/build/runtime. 65 historical + 34 integrated R10 + 24 0162C + 18 new quarantined = 141 NOT_RUN. Owner 0/16; canonical 0/55; D01–D12, R03 physical 4/5/7, D4/D5 remain.
 
## Next
0166: explicit scope and independent trusted policy/custody boundary; reconcile SQLite staging schema ownership/DDL privileges, concurrency and cross-scope replay, protected issuer/trusted time, integration coordinator evidence pin. Only after new scope integrate five new files; separate T01/T02/DEV/TEST permissions before execution. W2 55/20 field owner gaps, W3/W4 terminal and reconciliation, W7 settlement, W1 UI tests remain parallel.
