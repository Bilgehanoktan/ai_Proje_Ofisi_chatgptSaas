# MI-P0 — Four D0 proxy cross-owner source integration | 2026-11-20

## Scope and ownership
A **review-only integration candidate**, not a new prototype, transfers byte-exact existing owner source from [PR #26](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/26) and [PR #22](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/22) onto one isolated tree. Its parent is PR #26 immutable head `8af623d5a...`; two PR #22 files are transferred by identical Git blob. No owner branch or `integration/product-dev` modification. MI01 [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20) W8 and MI04 [PR #19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19) security work remain separate.

## What changed, why, how
The canonical 553-file, 552-manifest product has four D0 GET proxies. PR26 already proposes three proxies with a shared absolute deadline helper (555 files / 554 entries). PR22 separately proposes the Office Workbench absolute deadline and focused tests. Their changed source paths are disjoint; the actual integration task is to reconcile **one combined manifest** and verify the four route contracts under one isolated build/test run, rather than develop new route implementations.

This review candidate contains **556 product files, 555 manifest entries**, with an updated Office route entry and one added Office test entry relative to PR26's manifest. Source-owner pins for the four routes, shared helper and two focused regression test files were **7/7 exact Git blob**. The complete GitHub product source tree and manifest check: **555/555 path/byte matches; no unlisted/missing files**. The Git blob audit covers **10/10 exact TypeScript source files** locally. A selected strict compilation of these ten exact files passed using TypeScript **5.8.3**; the project-pinned 5.9.3 and full Next build were not executed.

## New combined regression
The GitHub-committed `test_four_proxy_cross_owner.cjs` was executed against those **same exact ten source files** in one local compiled tree. **7/7 PASS**, raw TAP is `raw_four_proxy_cross_owner_7.tap` (SHA-256 `7ec905b926a7445040c6804354ad04035a8cd71a3e93db79697e0030cded9666`). Tests cover four proper local-only valid responses, foreign-tenant isolation, one stalled outbox fetch not blocking three other concurrent 200s, pre-aborted signals, invalid port with zero fetch, disjoint parser contracts, and native 2.5s abort of hanging Office GET. All backend traffic is mocked; none contacts a live backend. The first attempted `node --test <file> <path>` call failed due only to argument parsing; plain `node <file> <path>` was run successfully. Owner prior PR22 37 and PR26 60 selected tests are historical owner evidence, **not 97 tests re-executed** in this combined checkout.

## Technical catalog delta
| Type | Change | Preservation |
|---|---|---|
| Source routes / GET() | Four existing API routes on one review source tree: `admission`, `outbox`, `task-budget`, `office-workbench` | Exact owner blobs; existing HTTP 200 or 503 D0 HOLD contract |
| Helper functions | `readBoundedD0Json`, `beforeDeadline` from PR26 and Office `boundToDeadline`, `readOfficeWorkbench` from PR22 | No new shared executor, real authorization or external calls |
| Parser, settings, API | Exact existing strict D0 parsers and `localBackendPort` | No changed schema, API path, host or port policy |
| Manifest | Review-only 555 entries; PR26 554 entries + exact PR22 Office route replacement and focused test | No update to `integration/product-dev` or other owners' manifests |
| Test | One new cross-owner synthetic regression source + raw TAP in docs | 7/7 selected actual; does not imply Next browser/full W8 |
| DB/events/dependencies/CI/grants | None | Zero new permissions, prod effects, dependency locks or DB migrations |

## Progress, blockers, recovery, handover
Canonical before → after **unchanged**: Core **12/16 → 12/16**, UI **21/40 → 21/40**, MVP **0/11 → 0/11**, IV **0/7 → 0/7**. Global weighted 15/35/20/20/10 **HESAPLANAMADI** because owner-ratified denominators remain 0/10. This review is source and selected functional integration evidence, not full product acceptance.

**Next and ownership:** MI01/Unified PR20 must establish exact reviewed lock/wheelhouse C04, supply-chain approval C05, then original W8 C06–C08 full fresh install/build/native browser. Source owners review the exact manifest and four-proxy source candidate after those gates; G2/G9 PR19, real independent root/issuer/sink and protected PostgreSQL remain HOLD. No automatic merge/main/CI/PROD elevation.

Rollback: close draft or normally revert the isolated combined source/manifest commits; PR22, PR26 and canonical product-dev remain intact. See `EVIDENCE.json` for full source and test provenance.
