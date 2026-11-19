# MI10-D0-CI-GREEN-SSE-DIAGNOSTIC-20261119 — MI-10 / MI-01 / MI-03/04 handover

## Executive evidence
Actual [GitHub Actions run 44613960595](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44613960595) on the same-repo **draft, unmerged PR #4**, CI commit `403d180fb6bf2cd739dc0d8880e3b1d3b37006e0`, completed with **3/3 successful jobs** on GitHub-hosted ephemeral runner. This is a genuinely executed and externally observed D0 test matrix; no product build acceptance or IV attestation was issued.

- MI-01 GitHub SHA-256 source audit: **538/538** manifest files, **17/17** shared file pairs, **33/33** auxiliary Git blobs. Original npm lock direct package metadata **61/61**; no lock regeneration.
- MI-03/04 original selected Authority–T1 and SQL mapping tests: **7/7 + 35/35 = 42/42** actual disposable SQLite, **30/30** exact source pins; previous tests rerun, not 42 new methods.
- MI-01 diagnostic frontend `npm ci`, Next.js 15.5.29 `npm run build` and `npm run typecheck`: **PASS**. Python 3.13.5, Node 22.16.0, Playwright 1.57.0.
- Real loopback FastAPI `127.0.0.1:17301` with original on-disk SQLite lifecycle-prefix fixture and local Next `127.0.0.1:17300`: real HTTP 200, database SHA-256 invariant **PASS**.
- U3 **SSE-compatible diagnostic browser flow PASS**, 5 screenshots, 3 snapshot read events, same-document identity, `JOIN HOLD` retained. Artifact [14573164214](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44613960595/artifacts/14573164214), 1,440,083 bytes, ZIP SHA-256 `756a1d57e7af775f1df17ce981a36eb6ed70b9c38dce983aa905201a8caaed51`, eight entries: two server logs, five screenshots, original-format U3 JSON report.

## Architecture and catalog (what / why / where / how)
No product source, DB schema, event, API, policy, dependency, grants or main/integration/product-dev path was altered **by this integration governance review**. Current owner CI workspace:
`integration/mi10-limited-ci-20261119`: `.github/workflows/mi10-limited-ci.yml`, `.github/mi10/requirements-browser.txt`, and new `.github/mi10/run_sse_compatible_u3.py` (CI only). Source under test is immutable common `61bb06e`, original U3 test Git blob `2a3f2b8e286c5d79847a6b00cdb6d046d0429773`, G6A `6bab623`, selected 42-runner `878a0e4`. React/Next `app/api/demo/shared-snapshot/route.ts` reads FastAPI `/demo/v1/lifecycle/shared-snapshot`, which reads an existing SQLite prefix fixture; no stub API or grant.

The previous failures are distinguished:
1. 44610698699: backend not started, frontend returned intended 503 HOLD.
2. 44612266079: `pip check` detected missing FastAPI `opentelemetry-api`; owner pinned it, no validation disabled.
3. 44612869954: the real backend was HTTP 200 and Next passed status/no-store. Playwright `response.text()` failed at Chrome DevTools Protocol `Network.getResponseBody` for SSE. Backend/Next server log and screenshot artifact verify process start; this is not proof that the API was faulty.
4. 44613836033: owner CI helper failed on incorrect Git blob NUL separator encoding (`MI10_ORIGINAL_U3_BLOB_HOLD`), fixed in owner commit `403d180...`.
5. 44613960595: owner CI helper uses `response.clone().text()` on **the same browser fetch** via init-script; all CI jobs passed. The immutable original U3 test itself was not executed byte-exact in this last browser job. Label only `CI_SSE_COMPAT_DIAGNOSTIC_PASS`.

### QA caveat: do not promote compatible browser run to original U3
The shim captures the fetch body in a *single global* `window.__mi10LastStreamBody` promise. Its `read()` wait condition tests only non-null; after the first read, second and third reads can race with the replacement of that promise and reuse an older body. The fixed D0 digest masks this possibility. This is a **static coverage concern**, not a proven production bug. MI-10 owner was notified on [PR #4](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/4#issuecomment-7022113525). Review a monotonic per-request response identifier/queue and a fresh-read negative case **without introducing synthetic network responses or additional server reads**. Restore byte-exact original CDP test where supported, or retain separate transport-compatible classification. U3 original CDP limitation stays OPEN.

### Acceptance and next integration gates
The full reviewed W8 `prepare-install-test-smoke` wheelhouse/fingerprint chain, original byte-exact browser acceptance, all 10 original Memory–Witness–T1 tests on complete 265 backend sources (one full-restore test intentionally reproduces a known residual), real ORG/Core positive OperationsStore/P02 owner provenance, full G2/G9, strict protected multi-DB PostgreSQL COMMIT and independent witness/IV are **NOT_RUN/HOLD**. Do not infer any from these 3 CI jobs.

D5-G7 %42.50→%42.50, D5-C-R8 %50→%50, Core acceptance 12/16→12/16, MVP 0/11→0/11; no delta. MI-10 development percentage HESAPLANAMADI: the weighted 15/35/20/20/10 stage criteria are not frozen. No multi-line global project percentage computed.

## Operating/maintenance/rollback
Diagnosis: check exact CI run SHA, official step outcomes, raw SHA-256/source pairs, U3 report and backend/frontend logs; isolate install, backend reachability, Playwright CDP body, and browser assertions as separate failures. Never suppress `pip check`, status 200/no-store requirement, streaming canonical digest, role `JOIN HOLD`, unauthorized external requests, or independent custody. CI remains existing H01 narrow PR#4 `contents: read` permission, draft/unmerged, no deploy. Rollback governance documents via normal revert; owner may separately close/revert PR#4. Do not force push or alter product-dev/main, SQL migrations or grants.
