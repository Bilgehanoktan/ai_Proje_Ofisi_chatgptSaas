# MI-P0 — D0 Admission / Outbox / Task-Budget bounded-deadline correction

**Date:** 2026-11-20. **Scope:** new isolated product-review candidate; **not** a canonical source transfer, runtime authority, production release, security acceptance or new CI authorization.

## Source, ownership and change control
- Canonical immutable starting point: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 product files / 552 manifest entries, manifest blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`.
- Active PRs examined: #19 G2/G9, #20 W8, #22 Office Workbench (same symptom but **different owned route**), #24 G7 current ORG; **zero changed-path overlap** in these four PRs.
- This work owns only three other demo routes, one shared `features/mvp` helper and one focused test, in isolated `review/mi-p0-d0-multi-proxy-deadline-20261120`. Do not edit or merge PR #22's `office-workbench/route.ts` from this candidate.
- Old 3 exact route Git blobs: Admission `c0a867a669993738d8b06a08fa7089f836a911b3`, Outbox `7dc1c9eb20feaf70358ba6137f35a3cbbec8a4ce`, Task-Budget `91256098c2a61001e7305bf3658c8178219591ed`. Original parser, localBackend and original test blobs matched GitHub exactly before local work.

## Root cause, actual correction and technical catalog
All three routes previously passed an `AbortSignal.timeout(2500)` to `fetch()` but awaited fetch, `reader.read()`, and `reader.cancel()` without an independent bound. An abort-ignoring transport can indefinitely postpone a D0 `503 HOLD`; a late valid response could also yield `200`.

| File / symbol | What changed | Interface / risk |
|---|---|---|
| `product/ai-company-os-frontend/features/mvp/readBoundedD0Json.ts` — `beforeDeadline<T>()`, `readBoundedD0Json()` | New helper uses one abort signal to bound fetch and stream read, and does not await indefinite stream cancellation | New internal module; not an externally exposed API |
| `product/ai-company-os-frontend/app/api/demo/admission/route.ts` — `GET()` | Uses helper with original 4096-byte cap and original admission parser | Existing URL and HOLD envelope unchanged |
| `product/ai-company-os-frontend/app/api/demo/outbox/route.ts` — `GET()` | Uses helper with original 4096-byte cap and original outbox parser | Existing URL and HOLD envelope unchanged |
| `product/ai-company-os-frontend/app/api/demo/task-budget/route.ts` — `GET()` | Uses helper with original 8192-byte cap and original task-budget parser | Existing URL and HOLD envelope unchanged |
| `product/ai-company-os-frontend/tests/d0-proxy-deadline.test.cjs` | Adds 9 actual local Node checks per route, 27 total, including four adversarial deadline cases each | Synthetic fixture test, no real network |
| `product/SOURCE_MANIFEST.json` | Preserves 552 entries, updates three existing SHA256 records, adds two new paths | 554 manifest entries / 555 product files, **review candidate only** |

Parser modules (`admissionProjection.ts`, `outboxProjection.ts`, `taskBudgetProjection.ts`, `officeWorkbenchProjection.ts`) and `localBackend.ts` were **not** changed. No change to API shapes, backend, SQL, event store, authentication, IAM, grants, dependencies, Next config, CI, provider access, secrets, main or canonical product-dev.

## Actual execution and evidence classification
- Environment: Linux x86_64, Node.js 22.16.0, global TypeScript **5.8.3** (project-pinned 5.9.3 unavailable). Exact imported parser and localBackend Git blobs independently verified before selected strict TypeScript compilation: **PASS**.
- The **same 27 test methods** were run first against **three original unchanged routes** (matching their real Git blobs), producing **15/27 PASS and 12/27 FAIL**. The 12 failed tests cover post-abort valid response, abort-ignoring unresolved fetch, stalled body read, and unresolved stream cancellation across three routes. Baseline local TAP SHA256: `84cb4e7679efde640c3a8fece02343fd87d710e816c69fa21a2dbb799808ea10`.
- **After the code change** the same 27 test methods achieved **27/27 PASS**, no skip/failure. Local TAP SHA256: `f8fdb15a8ec166fc23c518155287d322788ba4ae911299ffcfb0f7f53eded214`.
- Three **original GitHub test files** were separately recovered with identical Git blobs: Admission `166572d2a0c6859dc4d39561264422ed2732c4fe`, Outbox `29c03bd93fbb6d20e480979ac0df0f23f1108a13`, Task-Budget `4a0ec2845d467bfe4caabddefffde1f0da896cd1`. Replayed **10/10 + 9/9 + 14/14 = 33/33 PASS**, no failed/skipped methods. TAP composite SHA256: `395f60cddb9d47f262253c8b21c6ace7d9420afed09a05fd6c86a2157dcb5630`.
- Combined selected local **60/60 PASS** (27 new + 33 original, zero duplicate methods). These are **synthetic mocked transport/HTTP response tests** with 150-ms test-only watchdog on intentionally aborted cases, **not** a 2500-ms wall-clock production SLA verification. No full install, Next.js build under pinned 5.9.3, browser or independent IV run; formal W8 C04–C08 remains **NOT_RUN / HOLD**.
- GitHub blob readback matched local actual tested files for all five changed/new files: `c46fa8f2`, `12895f7c`, `b8c6a4e6`, `a1ff4a16`, `52802763` (full values in manifest / evidence).

## Integration order, failure diagnosis, maintenance and rollback
1. **MI-05/owner** reviews this distinct three-route candidate and existing Office PR #22 independently; must not silently combine or override Office source. One consistent helper could later be considered by its owner but this PR makes no Office edits.
2. **MI-01/Unified** owner #20 completes already assigned W8 553 C04 prepare + C05 supply-chain/license ratification + C06-C08 install/build/native browser first. **This 555-file candidate changes the manifest blob** and therefore needs an **independent exact immutable manifest pin / full W8 requalification** before any transfer. Never blind-repin solely to make tests green.
3. **MI-04/G2-G9** owner #19 still has separate 562-file authority variant, 72/72 selected D0; PR19 and this PR are not to be auto-merged.
4. **MI-02/GATE-02** independent issuer/root/sink, strict PostgreSQL COMMIT/restore and IV remain HOLD.

To diagnose future failures, verify the exact Git blob for route/parser/helper and compare the test outcome by scenario: pending `fetch`, pending `reader.read`, pending `reader.cancel`, or late `200`; inspect source/manifest SHA256 before rerun. A browser or implementation-specific Streams failure requires a fresh owner runtime test, not acceptance by inference. Close the draft PR or normal revert of these 5 changed/new files + manifest and documentation; **no force push**, canonical branch and historical PRs remain unchanged.

## Progress 15/35/20/20/10 and devir
- Global weighted development previous/current/delta: **HESAPLANAMADI** (10 groups still have 0 owner-ratified criterion denominators; do not fabricate a percentage).
- Product acceptance: Core **12/16 -> 12/16**, UI **21/40 -> 21/40**, MVP **0/11 -> 0/11**, IV **0/7 -> 0/7**, acceptance delta **0**.
- Real local test evidence new: **27/27**, original selected repeat: **33/33**. This is not an acceptance or W8 gate promotion.
- Next task remains **owner MI-01 full W8 553**; this separate bugfix is review-ready and test-complete in its isolated source branch. **No new H01 decision** is needed merely to review the draft; production, security ratification or canonical merge remains subject to existing gates.

## 2026-11-20 R2 — native wall-clock 2500ms guard closes remaining synthetic-only timeout evidence gap
- No product runtime routes, parser, API, DB, event or security code was changed in R2. A **new original scoped regression** file `product/ai-company-os-frontend/tests/d0-proxy-wallclock.test.cjs` was added (Git blob `bc714ec16a144cba403c214bd1497525e5114821`, SHA-256 `46ce8369ff26a479dcf6e03df17fa593aa0af1c53f10ed2babb1c5d9e3013140`, 2510 bytes).
- Distinct from the original 150ms test-only watchdog, this script leaves `AbortSignal.timeout(2500)` **native and real**. Local Node 22.16.0 measured HTTP **503** on abort-ignoring unresolved `fetch()` in Admission (~2530ms), Outbox (~2502ms), Task-Budget (~2502ms), a stalled Admission `reader.read()` (~2505ms), and an unresolving `reader.cancel()` (~1ms). **5/5 PASS**, 0 skips. Raw unmodified TAP: `REAL_2500MS_WALLCLOCK_TAP.log` Git blob `aff733644dab4e03fa621ae7198f1525935bf635`, SHA-256 `ed2e399d704995ad9f571633c460b049eeeaa89ec55cf55aff0eae9c75b0b384`.
- Rerun unchanged existing original three suites Admission **10/10**, Outbox **9/9**, Task-Budget **14/14**, and the new 27-case suite **27/27**. With new native timeout proof, selected local unique cases are **65/65 PASS**. There is **no double counting** of previous replayed tests and no change to canonical product acceptance.
- Reviewed candidate manifest is now **555 entries / 556 product files**, manifest blob `de7890587730452c0c7b22315b7d475fc666f0d7`; the canonical `integration/product-dev` remains **552 entries / 553 files**. The 556 candidate must be independently pinned and fully W8-tested **after** the existing owner's 553 chain, never blindly re-pinned or merged.
- Failure diagnostic: a hang beyond the real 2500ms timer is an error even if a 150ms synthetic mocked-abort test passes; compare the raw TAP, Node version, actual original source Git blobs and environment. If runtime cancellation semantics change, rerun these cases plus full Next/browser. No new production SLA certification or owner acceptance follows from this narrow local Node result.
- Rollback for R2: normal revert of new wall-clock test, manifest entry and R2 docs only. Preserve prior 60 selected test results, exact owner PR #20/#22/#19/#24, canonical product-dev and all permissions. Overall weighted progress **HESAPLANAMADI** (owner criteria 0/10); Core 12/16, UI 21/40, MVP 0/11, IV 0/7 unchanged, product acceptance delta 0. W8 C04–C08 and independent PG/IV remain **HOLD / NOT_RUN**.
