# MI-05 / Office Workbench — request deadline fail-closed correction (2026-11-20)

## Basis and ownership
- Canonical development product: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 source files, 552 manifest records. Its contents were not changed.
- Existing W8/MI-01 PR #20, G2/G9 MI-04 PR #19, GATE-02 A1 security review and MI-06 owner modules were checked. None edits this one existing Office Workbench route. No other active MI-05 pull request was found at the checked GitHub snapshot.
- Work is review-only on `review/mi05-office-workbench-deadline-20261120`; original MI-05 `projectionRead.ts` 12/12 regression remains separately evidenced and not recounted.

## What, why, where, how
Original `app/api/demo/office-workbench/route.ts` constructs `AbortSignal.timeout(2500)` inline for its GET. A transport which does not honor the abort can still return a syntactically valid D0 body, after which the route replies HTTP 200. Two actual local controlled-mock tests reproduced this failure (HTTP 200 while the test requires HOLD/503). The backend and existing strict parser are not at fault.

Minimal change:
1. Capture the exact same timeout signal in a local `signal` variable, preserving the loopback-only URL, response size cap, type check, parser, no-store and no redirect behavior.
2. Check `signal.aborted` after full response parsing and before emitting a successful JSON response. The existing catch returns D0 HOLD/503.
3. Add `tests/office-workbench-deadline.test.cjs` with six focused Node `node:test` checks, including both adversarial ignored-abort paths.

This is a request-deadline and stale-response guard, **not** authenticated owner-issued provenance, Office–Runtime geometry binding, tenant authorization, shared-session browser acceptance or production release.

## Exact technical catalog delta
| Kind | Path / symbol | Delta |
|---|---|---|
| Existing TypeScript route | `product/ai-company-os-frontend/app/api/demo/office-workbench/route.ts` — `GET()` | Enforces post-parse timeout abort before returning HTTP 200 |
| New regression | `product/ai-company-os-frontend/tests/office-workbench-deadline.test.cjs` | Six actual local isolated Node tests; two newly exposed failure modes |
| Existing parser | `features/mvp/officeWorkbenchProjection.ts` — `parseOfficeWorkbench()` | Unmodified; strict D0 envelope and role counts |
| Existing port guard | `features/mvp/localBackend.ts` — `localBackendPort()` | Unmodified; local loopback only |
| API | `GET /api/demo/office-workbench` | Existing API unchanged; late aborted response now 503 HOLD |
| DB / security / dependency / workflow | None | Zero mutation |

- Old exact route Git blob: `749a289984049e0cec27ed93d656023ba4da1fff`.
- New route Git blob: `dc18ef2ecaf5556e09bc6152578f8cadf247ef29`.
- New test Git blob: `8ae7b251f8ac86e3f03897442d3819d76256cbe9`.

## Actual local test and reproduction
- Linux isolated environment: Node v22.16.0, global TypeScript 5.8.3 (project-pinned 5.9.3 **not installed**).
- Each of the three originally retrieved source files was verified using `git hash-object` against GitHub; selected strict TypeScript compilation succeeded.
- Before change: **4/6 PASS, 2/6 FAIL**. Both failures assert `200 !== 503` for an ignored abort.
- After change: **6/6 PASS, 0 skipped, 0 cancelled**; selected strict TypeScript compile PASS. This is actual isolated local execution, not CI/browser/full product.
- Baseline full TAP log SHA-256 `5cda68b6c8c88afe58d8dcc0f6215f13886adca5951fd7a2716170393328ea40`; fixed replay TAP SHA-256 `c2dd4f7b0bb2feec6bf707c0e609b68c15a248f84dbe293aba29dbeda8b2db38`.
- Exact structured evidence with source SHA and status: `EVIDENCE.json`. Original Office test suites and full W8 were not rerun.

For an isolated replay, preserve the frontend `app/` and `features/` relative paths, use `tsc --target ES2022 --lib ES2022,DOM --strict --module commonjs --moduleResolution node` to compile the route and its two imports, then execute:

```sh
node product/ai-company-os-frontend/tests/office-workbench-deadline.test.cjs /absolute/path/to/compiled/app/api/demo/office-workbench/route.js
```

Where @types/node is absent, only the local compile fixture needs `declare const process: {env: Record<string,string|undefined>};` in a transient .d.ts file; it is not a product runtime dependency or new grant.

## Owner and integration gates
- MI-05/Unified owner: review one-route change, rerun existing original Office Workbench and W8 tests under approved exact dependency fingerprint, verify browser against current same-session Office readback.
- MI-01 owner PR #20: continue independently; do not merge PR #19/20 unconditionally because manifest pins differ (553 vs 562). Do not repin for test success.
- Security and data: GATE-02 owner custody, strict PostgreSQL / restore and independent IV remain HOLD.
- No CI workflow, build approval, backend DB change, main, product-dev branch mutation, grants, secret, provider, spend or activation.

## Progress and handover
- UI acceptance **21/40 → 21/40, delta 0 pp**; standalone Core **12/16 → 12/16**, MVP **0/11 → 0/11**, IV **0/7 → 0/7**.
- General weighted development previous/current/delta: **HESAPLANAMADI**, because approved 10-group denominators remain 0/10. MI-05 local weighted percentage also uncalculated without owner-frozen stage criteria.
- New code patch/test is complete in an isolated review candidate, **not accepted in the canonical product**. Do not count this focused test as W8 C04–C08 or product acceptance.
- Rollback: close the draft review; if later transferred, revert this route and test normally. No reset/force push, no change to historical source or original tests.
