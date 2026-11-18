# R8 Build R1 — current handover (2026-11-18)

Source commit: be42ba7bf8f20c8e1032804b04bbdc07c90f8160
Manifest Git blob: fcfab43ff8661dde24f5d5b1f797ed61a1fb9887
Previous failed-stage source: 9675d4e1c3238776d1e744e0d82d6df70cfcbcd9

Windows original attempt: npm ci exit 0, 30 installed, full build exit 1, typecheck NOT_RUN. Original logs remain on workstation; reported hashes in BUILD_R1_REPAIR.json. No final acceptance.

Exact source readback: 509/509 manifest paths match remote tree, 505 unchanged at same path, one byte-identical component relocation, three modified source/test files, one manifest change. Five original preimage SHA256 values matched; zero case-folded TS/JS module stem collisions. No full build after repair.

Catalog delta: WorkflowDraftInspector.tsx retains DraftInspector component symbol, same content blob b57e27761e60351e62224b569ad107cd54fd8daf; WorkflowDraft import and 16-case inspector test loader refer to new filename. ProjectionReadbackCenter.ReadbackCheck parameter ReadbackKey instead of ProjectionKey; original seven-card inventory preserved. No new API, database, dependency, permission, or runtime publication. Existing CSS warnings not modified.

R1 local delivery helper R8_build_R1.py, SHA256 00f9f31fd24292a82ef87166c52e9615f9ad99a6ed63f73c4ef747e3e68b9e76, 8545 bytes, Python AST syntax PASS, actual Windows execution NOT_RUN. Delivered separately in chat, not a GitHub source artifact. Checks old stage log hashes and original review/lock; fetches exact source and extracts product to a fresh stage; verifies 509 source files and old component references; records fresh R1 review and asks explicit ONAY before install; copies content-addressed cache if available; npm ci ignore scripts, existing 16 inspector test cases, full Next build, standalone tsc, source/lock verification. No backend starts. Failed stage remains intact. If build mutates tracked source, stop HOLD, preserve logs and review exact diff.

Ownership: shared base defect also exists at pinned U3A and Premium heads. Only R8 isolated integration branch changed. Unified/Premium owners must review/apply exact fix in their own source, rebind original manifests/harnesses; do not auto-merge. Other 235 branches checked. No independent acceptance. I2/I3 remain open. R8 weighted 11.67 -> 11.67 (0 pp); canonical product acceptance unchanged. Reporting standard blob 77ffdb44fc4b6ff8419c80a47b5aa7a8be0d2a16.

Next: actual R1 Windows test logs, then real loopback browser only when build passes. Rollback by keeping previous immutable source and failed stage; no deletion or repinning.
