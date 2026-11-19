# MI10-SSE-FRESHNESS-REPRO-20261120 — MI-10 SSE body freshness QA / architecture and handover

## Actual tested observation (not product/browser acceptance)
SSE-compatible CI succeeded in [run #44614849105](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44614849105), 3/3 jobs; prior selected 42/42 D0 SQLite, exact Next diagnostic build/typecheck, real FastAPI and five U3 screenshots are intact. Its original byte-exact U3 `Response.text` over CDP remains unresolved and full W8/PG/IV remain HOLD.

The checked CI owner helper is `.github/mi10/run_sse_compatible_u3.py` Git blob `84997c31334e4684b159b5dbd799e3abdd40d301`, original test pinned `2a3f2b8e286c5d79847a6b00cdbd046d0429773`. It stores the latest `response.clone().text()` in a single `window.__mi10LastStreamBody`. The adapted test awaits only `window.__mi10LastStreamBody !== null`; after the first request that condition is permanently true until a new value overwrites it. Accordingly, a later browser read can associate an earlier body with its newest response metadata. This is a potential **test evidence freshness false-positive**, not an observed security compromise or product API failure.

An isolated **actual Node.js v22.16.0 execution** of the reviewed interceptor logic with three asynchronously resolved controlled fetches reports **5/5 focused assertions** and reproduces **two distinct stale-body reading windows**. No network, real browser, full original Playwright, actual product module or database was exercised. Test script: [test_sse_global_promise.js](./test_sse_global_promise.js). Source-independent JSON evidence: [EVIDENCE.json](./EVIDENCE.json), local report SHA-256 `925a574437a173fe641ed4a9ab6c9afdc4a38b13e9e7800baecd1d31b60f0c89`. The report is downloadable in the originating conversation; the reproduced facts are restated here.

## Scoped catalog
**Reviewed elements:** JS `window.fetch` adapter and `window.__mi10LastStreamBody` global Promise; original Python `browser_unified_u3.main/read`; unchanged Next API `app/api/demo/shared-snapshot/route.ts` and FastAPI `shared_snapshot` HTTP 200 or fail-closed 503. **New QA-only source:** `test_sse_global_promise.js` (test harness for evidence, outside product tree), `EVIDENCE.json` and this runbook. No new/modified production API, class, function, DB/table, event, migration, runtime dependency, CI job, role, grant or branch merge.

## Owner fix/diagnostics
1. Under existing MI-10 owner boundaries, bind `read()` to a **fresh unique response ID or monotonically increasing sequence**, enqueue clone body against that request, and wait for matching new sequence and resolved text, not only prior non-null global.
2. Add negative repeat-read test with different snapshot payloads/sequences, and verify that each of three expected browser reads consumes the corresponding new body while **no extra network read** is introduced.
3. Keep 200/no-store/canonical SSE/digest, readonly fixture and SHA, UI screenshots, TTL, same-document and block-external checks. Avoid changing product API or test assertion semantics to force PASS.
4. Execute owner-scoped permitted CI; original U3 CDP and complete W8 still require independent owner acceptance, fresh reviewed fingerprint and protected PG/IV unchanged.
5. On mismatch, STOP/HOLD and revert only owner CI helper by normal commit; no CI permission widening, main or product-dev mutation.

## Delivery/integrity/percentages
Only central QA evidence and owner handoff. Previous/current D5-G7 %42.5, D5-C-R8 %50, Core 12/16, MVP 0/11 unchanged, delta 0. Whole project progress HESAPLANAMADI (no frozen group denominator). Do not count 5 focused harness checks as five product functional tests. Known full restore Memory–T1 replay residual and remaining ten original 0214 cases are still independent GATE-01 blockers.
