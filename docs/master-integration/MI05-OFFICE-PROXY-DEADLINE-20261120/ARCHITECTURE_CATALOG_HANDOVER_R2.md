# MI-05 — Absolute response deadline repair R2 | 2026-11-20

## Decision and active owner check
Canonical `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 product files / 552 manifest entries. W8 owner [PR20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20); G2/G9 owner [PR19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19); separate independent QA [PR23](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/23); manifest [PR21](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/21). Only MI05 owner review PR22 route and own focused tests were modified. PR23 independent source stays unchanged.

## Problem, root cause, repair
R1 checked `signal.aborted` **after parsing**. Three genuinely executed independent PR23 negative tests had **0/3 PASS** because a transport could ignore abort and indefinitely hold `fetch()`, `reader.read()`, or `reader.cancel()`; the post-parse check was unreachable.

R2 splits the existing route's `GET()` into the original D0 read/strict parse flow (`readOfficeWorkbench(signal)`) and a single absolute `boundToDeadline<T>(signal, work)` guard. `AbortSignal.timeout(2500)` is created **once** per GET, passed unchanged to fixed loopback fetch, and monitored by a one-shot abort listener plus `Promise.race`. Listener is removed on settlement. Aborted or failed requests return pre-existing `D0_OFFICE_WORKBENCH_HOLD` HTTP 503. A stalled transport promise need not cooperate in order for GET to terminate. The underlying uncooperative operation may itself remain pending; provider/resource cleanup is **not** claimed proven for a malicious transport.

The same strict payload parser, 4,096-byte response cap, fatal UTF-8 decoder, loopback-only port configuration, `no-store`, `redirect:'error'`, and JSON content-type rule remain intact.

## Exact technical catalog and interface delta
| Scope | Original | Current | Behavior |
|---|---|---|---|
| Product route `app/api/demo/office-workbench/route.ts` | R1 blob `dc18ef2ecaf5556e09bc6152578f8cadf247ef29` | R2 blob `ae42ecccdda987c00537696f2698f49c374ec927` | Existing `GET()`, new internal `boundToDeadline<T>()` and `readOfficeWorkbench()`; absolute 2.5s 503 guard |
| Product test `tests/office-workbench-deadline.test.cjs` | six methods `8ae7b251f8ac86e3f03897442d3819d76256cbe9` | nine methods `aa7afc3a93265305df6ceb8acbb03d25b901beb3` | Added pending fetch, stalled read and never-settling cancel negatives |
| Existing API | `GET /api/demo/office-workbench` | same path and HTTP 200/503 shape | no additional API or permissions |
| DB/schema/dependency/CI | none | none | no changed dependency or workflow |
| Strict D0 parser / port configuration | same owner Git blob | unchanged | no authority upgrade |

## Real test executions and limits
- Original frontend `office-workbench.test.cjs` exact Git blob `bbad34677abeb0f2fada6b68ad4805b09ee077c7`: **25/25 PASS**. Twenty JSON fixture values reconstructed semantically from original GitHub file blob `29aa823d16c2b7975c322b41b99f9db4ec2b2c4e`; **not byte-exact fixture bytes**.
- Owner PR22 focused nine-method suite: **9/9 PASS** (prior six retained, three new different-stage stalls).
- Independent PR23 QA source exact Git blob `ff6d1a9c923f427a9f982aaaffd59a45fd9d7578`: **3/3 PASS**, previously **0/3**. No QA changes and no false double counting as acceptance.
- Selected local Node tests **37 executions, 37 PASS, 0 FAIL/SKIP**. Node v22.16.0; selected TypeScript strict compile PASS with global v5.8.3 (project v5.9.3 NOT_RUN).
- Real native `AbortSignal.timeout(2500)` with indefinitely unresolved mock fetch: **503 in 2,536 ms PASS**. No live backend or network.
- Three raw local TAP SHA256 respectively original `80695950e11eb1708081dd1f1c82a71ba94651b950c60140ce1f1e749ab48350`, owner `0944bbd160699235d3e9a45abcdbec90b7c10f25b442c2572753c74386fc3154`, independent `07810a25982d7db749719088a55b1495632992897a428addbb7dad0715d58129`.

## Architecture, provenance, progress, handover
This remains an isolated synthetic demo security **fail-closed transport behavior**, not real IAM/issuer, PostgreSQL COMMIT, shared-session browser, independent verifier or operational MVP. Original architecture and user decisions unchanged. R1 evidence is preserved without rewriting history; new facts are in `EVIDENCE_R2.json`.

- Manifest proposal `SOURCE_MANIFEST_REBIND_R2.json`: canonical manifest is not changed, avoiding MI01/MI04/PR21 multi-writer conflict. Review branch contains a changed route plus added test requiring later manifest reconciliation by owner. No product-dev/main promotion.
- Progress previous -> current: Core 12/16 -> 12/16, UI 21/40 -> 21/40, MVP 0/11 -> 0/11, IV 0/7 -> 0/7, delta 0 pp. Global weighted 15/35/20/20/10 **HESAPLANAMADI**, no approved denominators.
- Remaining: MI-05/Unified owner code review PR22, reviewed MI-01 W8 exact C04-C08 full install/build/native Chromium, then valid manifest re-pin and source owner release gate. MI-02/04 security root/sink/PG remains HOLD. No new CI scope, provider grants, real execution, spends or PROD.
- Maintenance: a stuck `GET` should return 503 at abort; check signal, stage-specific pending promises and fixed loopback only. Repair by scoped PR22 revert (no force push), leave canonical `product-dev`/main and other independent PRs intact.
