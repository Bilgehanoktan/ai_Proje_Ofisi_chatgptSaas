# MI10-SSE-FRESH-RESPONSE-OWNER-CANDIDATE-20261120 — owned SSE freshness correction candidate

## Summary and authority
On 20 Nov 2026 the integration QA line prepared **source-pinned, tested, untransferred** fixes for the previously reproduced MI-10 SSE stale-body proof weakness. The MI-10 owner still controls `.github/mi10/run_sse_compatible_u3.py` and PR #4; neither was modified. This is not a change to the main app or an expansion of H01 narrow cloud CI authorization. Original existing approved CI [44617509366](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44617509366) remains 3/3 selected D0 PASS, including 1953/1953 exact tracked source files, 539/539 product files, 42/42 original selected SQLite tests, Next build and SSE-compatible browser diagnostic. That CI is **not** formal full W8 or security IV acceptance.

## Problem / why
The current owner helper stores one last-body Promise `window.__mi10LastStreamBody`, and its modified `read()` waits only for non-null. The 5/5 earlier negative reproduction demonstrated that pending B can read stale A, and pending C can read stale B. Fixed synthetic digest values may hide such a test false-positive.

## Candidate source catalog (what and where)
- `sse_capture_init.js`: CI-only `window.fetch` interception; exact path and origin validation, per-request monotonic sequence, Map keyed by request ID containing same-response cloned `text()` Promise. One-shot `take(seq)`; reject missing or mismatched data. No added HTTP calls, no changes to Next/FastAPI.
- `prepare_original_u3_fresh.py`: verifies unchanged original test Git blob `2a3f2b8e286c5d79847a6b00cdbd046d0429773`; checks all 3 original anchors exactly once; patches a **new copy** with init script and a per-click capture baseline, waits for the corresponding next request body and denies extra target requests; compiles result before writing `x` (no overwrite).
- `test_sse_capture.js`: 17 actual isolated JS assertions, includes old-body hazard, two concurrent out-of-order responses, malicious/incorrect response URL, network rejection, one-shot consumption, external and non-target pass-through. No real Chromium or service.
- `test_prepare_original_u3_fresh.py`: 10 actual Python unittests on **synthetic** original-shaped source verifying pin failure, marker counts, compilation, unchanged assertions, no original overwrite and output restrictions.

### File/API/DB/dependency register
Only four QA reference source files and test evidence/runbook files under this governance directory. No product symbol, app API, route, table, migration, registry, event, package requirement or security grant is changed. Inputs are original Playwright test source and same-fetch browser response. Generated output is a disposable modified test **copy**, never deployed.

## Executed tests and evidence
On the isolated container, Node **v22.16.0** `node test_sse_capture.js` succeeded **17/17**, Python **3.13.5** `python -m unittest -v test_prepare_original_u3_fresh.py` succeeded **10/10**, no skips or fails, total **27/27**. Direct GitHub Blob IDs for four source files match the independently executed local file bytes, listed in [EVIDENCE.json](./EVIDENCE.json). Full local archive SHA256 `0963009bb925496e42583e8f633950ae4dbd99b2bac8e693da145591509fce08` (ZIP, four sources, two logs, JSON). Logs [NODE_TEST.log](./NODE_TEST.log) / [PYTHON_TEST.log](./PYTHON_TEST.log).

The original U3 Git file was **not mounted** in the isolated local container. Its GitHub immutable blob and unique transformation anchors were remotely verified. Patcher on real original and real browser run **NOT_RUN**. Do not count this as 27 original product tests, 27 CI tests or full U3 PASS.

## Owner integration method / diagnostics
1. MI-10 owner compares this source candidate against current PR #4 helper and reviews `window.fetch` side effects; pre-approve no additional network reads. Existing CI scope only.
2. Run original test on exact checked-out pinned source and apply patch **outside source tree**, ensure original SHA1 and unchanged status 200/no-store, canonical SSE/digest, TTL, five screenshots, same-document and external deny assertions. Read count still exactly 3.
3. Add real browser case with **distinct** per-request bodies or identifiable sequence; verify B pending is not satisfied by A, including out-of-order delivery. If unable to make safe synthetic test, retain HOLD.
4. CI SHA, Node and Python dependency pins, unmodified product source and role `JOIN HOLD` remain locked. Do not merge PR #4 or enable unapproved workflow.
5. Failure: stop, capture stdout/stderr, error code, SHA, and revert only owner CI helper in its branch; do not change source acceptance or fake external effects.

## Progress and gate limits
D5-G7 42.50→42.50, D5-C-R8 50→50; Core 12/16 unchanged, MVP 0/11 unchanged. Overall development HESAPLANAMADI. GATE01 10 original Memory–T1, real GATE02 OperationsStore/Core/P02, GATE04 strict PostgreSQL COMMIT/witness and original U3/W8/IV remain NOT_RUN/HOLD. Owner source transfer **PENDING**.
