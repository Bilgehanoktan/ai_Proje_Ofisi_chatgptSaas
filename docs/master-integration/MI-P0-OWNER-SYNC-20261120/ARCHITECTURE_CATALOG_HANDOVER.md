# AI Company OS — MI-P0 owner evidence / integration handover (2026-11-20)

## Purpose and single-writer boundary
Read-only cross-owner reconciliation of the current highest-priority operational blockers. This is a **central orchestration record**, not a new product source, owner approval, new CI permission, normative decision, source promotion or product acceptance. The original MI-01, MI-04, MI-02 and QA/IV owners retain their scopes; do not open parallel implementations of their work.

## Immutable source snapshot
- Canonical development branch: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, source commit `a80932b6d5e99667889dfaa25b682feb267c6cba`; **553 product files / 552 manifest entries**. Unchanged by this reconciliation. Product tree `f4cdcf68115917ab69ba6441414539fe32a59369`; manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`.
- MI-01 active owner [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20), draft head `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`, targets canonical 553. `w8_unified_u3.py` continues to require the exact canonical manifest blob above.
- MI-04 active owner [PR #19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19), draft head `0a8907f177bb3e9b458aefb3ea3441b15537f542`, **562 product files / 561 manifest entries** in an isolated source candidate. Not merged.
- MI-02 security owner [PR #10](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/10), draft review only, 10 independent authority/custody decisions pending. No authority activation.
- Existing limited test-only CI [PR #4](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/4) remains limited to its original exact scope; no expanded CI authorization.

## Actual existing evidence readback (no new product tests)
1. [PR19 GitHub Actions run #44700495037](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44700495037), job `136167533591`: **SUCCESS**, all recorded steps successful. Source/manifest 561/561; owner G2 50, ORG 15, historical G9/G7 7 original D0 test executions = **72/72**. Historical G9 fixtures use old ORG source, not currently independently verified owner-issued identities; authority source variant not ratified; PostgreSQL, independent root/sink and restore protection HOLD.
2. [PR20 committed 19-test raw log](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542/docs/master-integration/MI01-W8-FROZEN-NPM-20261120/TEST_RESULT_ACTUAL_19.txt), Git blob `1df01ccd1a719c190d0ef550bacc9e6b86e181c6`: **19/19 reported local Python tests PASS**, comprising prior 15 plus 4 adapter-integration cases. Raw test text was read and verified against the reported method count and result; **not rerun** here. These are synthetic helper/adapter checks, **not** original full W8 prepare/install/build/browser.
3. Previously retained Core–OperationsStore original CI [#44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705) **10/10 synthetic SQLite PASS**. Do not rerun or double-count as real IAM/ORG protected PostgreSQL.
4. MI-01 separate metadata review: pinned npm lock **61/61 structural metadata checks**, **14 optional LGPL-containing platform packages** and **one CC-BY-4.0 package** require owner/license and actual-distribution-context assessment. Presence of license and integrity fields is not an audit of downloaded tarballs or vulnerability clearance.

## Key contract collision and enforceable dependency order
The PR20 U3 adapter requires canonical manifest `27b4eb...` (552 manifest records), while PR19 isolated candidate has manifest blob `566b7210b6edb95a21b999dc1d881a12284d9011` (561 records). Direct unconditional PR19+PR20 application must yield `U3_MANIFEST_HOLD`; this is a **safe refusal, not a bug to bypass**. Never blindly repin or force merge.

1. **MI-01 owner**: review PR20 immutable npm lock and exact 553 product/dependency graph; on a permitted connected host execute the **original** W8 C04 fresh `prepare` with reviewed wheelhouse, `python.lock`, full npm tarball/hash and licenses; obtain separate C05 owner dependency/legal/security approval; only then run C06 install, C07 complete build and C08 native browser smoke against exact 553. Current W8 operational status **3/8**, C04-C08 unclosed.
2. **MI-04 / G2–G9 owners**: ratify exactly one current authority reader, role/assignment issuer provenance, ORG scope, source and historical G9 fixture handling. PR19 remains draft until this owner ratification. If 562 is later approved, rebuild the W8 immutable manifest binding **for that reviewed 562 source** and rerun the full chain; the existing 553 approval cannot be inherited.
3. **MI-02 / security authorities**: assign independent root/claim administrator and restore custody, role/session issuer, quorum, sink-side fencing/idempotency and 8 independent negative cases. Existing 0214 restored-database replay vulnerability remains OPEN; real guarded PostgreSQL and independent IV must remain HOLD.
4. **MI-10 / IV**: inspect source-pinned full build, original browser, protected PostgreSQL and owner custody evidence only after the corresponding owner checkpoints. No automatic product acceptance.

## Progress / criteria — no unjustified uplift
- Global weighted 15/35/20/20/10 development: **HESAPLANAMADI** (10/10 group denominators not owner-ratified; 315 draft slots are not final).
- MI-01 operational subgates: **previous 3/8; current 3/8; delta 0**. Not global development percentage.
- Existing separate canonical acceptance: Core **12/16**, UI **21/40**, MVP **0/11**, independent IV **0/7**; **acceptance delta 0**. Note scoped original matrices are not interchangeable.
- No new test methods executed by this coordination turn, no software changes, no gate closed. Existing 19 and 72 test evidence merely cross-verified; no aggregation into unique test count.

## Technical catalog and change classification
- Product source files/classes/functions/API/DB tables/events/contracts/dependencies: **0 modified**.
- Source test files/CI/permissions: **0 modified**.
- Only additive central documentation and explicit reference in `progress/MASTER_INTEGRATION_CURRENT.json` are permitted.
- On missing source graph, network, owner/legal or security authority, fail **HOLD**; never downgrade check or treat an old synthetic passing result as release evidence.
- Container direct GitHub clone attempt produced DNS `Could not resolve host: github.com`; hence fresh original W8 tests were not claimed here.

## Maintenance, diagnostic, recovery and rollback
For a blocked W8 stage, preserve source SHA, lock SHA, full command, process exit, review fingerprint and original logs; never reconstruct an approval stamp. For PR19/20 collision compare exact manifest blob, owner SHA and inherited W8 source pin rather than rewriting either owner branch. Rollback this documentation-only addition by an ordinary revert and remove only its central JSON reference; preserve all owner PRs, source candidates and past evidence. No force push, CI scope expansion, main merge, live grants, PROD, secrets, payments, external effects or independent acceptance.
