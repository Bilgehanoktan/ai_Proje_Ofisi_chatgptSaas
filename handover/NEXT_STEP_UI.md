# UI-P10J-09 — exact delivery and real-screen review

Source archive reconstructed full Git tree e4e16879901fe045be686fceaa1db525d02c8996 from 1,544 blobs, exact tested source 752b225deac4557a548faec7191a090fbfba19f7. Original pinned archive auditor and W8 audit executed locally: 390/390, 16 pairs, 20 auxiliary blobs PASS. Raw REVIEW/lock hashes and all three acceptance markers match. Raw core29 report: 29 PASS, 55 exact historical 0207 files, no promotion to 0223. All 52 PNGs decoded, distinct SHA-256, four viewports/themes; contact-sheet review and selected full screen inspection. User Windows full run not independently replayed. PowerShell transcript omitted native command stdout; original console paste remains separate. No raw wheel or DB bytes; no pixel comparison baseline.

## Product findings and next work
- P0 mobile navigation: 12 non-office views show large open menu before heading (~75% first 844px viewport). Reuse design-system/Navigation.tsx and Navigation.module.css; implement accessible compact menu, keyboard focus, Escape, search, 13 destinations, preserve desktop and office route. Proposed mobile heading visible within first 240px when menu closed. Update browser harness explicitly, test all destinations and themes.
- P0 CEO and Work/Audit information architecture: 7182/13477 px CEO desktop/mobile, 7079/11624 px Work/Audit. Separate summary, operations and detailed evidence; preserve source/HOLD and all 7 existing reads. Proposed initial overview <=3 viewport heights before optional detail expansion; test actual measured height, no loss of evidence. Dashboard.tsx shared with core; do not overwrite without reconciliation.
- P1 Office: keep static D0 four rooms and empty reserve floor. Improve zoom, labels, room presentation and role detail; real motion/avatars only on verified runtime identity and location. No invented agent.
- P1 Project/Workflow/Agent: real graph selection, editor validation, undo/redo and role context browser tests; reconcile with 0223 Agent/Workflow source before feature overlap.
- P2 catalog-only WorkType, Goals, Decision Inbox, Preferences: existing read-only states, no new grants. Improve hierarchy and domain-specific views; preserve canonical data/unknowns. Finance, Security, Reports, Events and Skill need focused information organization.
- Version label still P10J-05 on P10J08, correct presentation version via source provenance in future candidate. CSS autoprefixer and Starlette warnings open.
- Visual acceptance: current 52 screenshots are baseline candidates, not reviewed pixel comparison. Check 390/1440 both themes, accessible menu, keyboard, graph actions, reserve floor, no horizontal overflow, no new network requests, no fake live data, unchanged sample DB hashes. Full W8 rerun for any code candidate.

Parallel 0223 source e499d8f063af872e2e83407935693b0ffed655c6 at observation; 320 same, 49 UI-only, 51 core-only, 5 divergent paths. No final 0223 handover found in this snapshot. Do not auto merge. UI 21/40 historic gate count retained pending explicit criterion mapping; W8 local 8/8. Independent 0/7. Core 7/16 last confirmed 0222; not regraded. No new product code, no main/CI/PROD changes. Rollback uses tested source 752b225deac4557a548faec7191a090fbfba19f7 and original evidence, no live DB restore.

---
# UI-P10J-08 — local Windows W8 PASS

Exact source 752b225deac4557a548faec7191a090fbfba19f7; manifest 2a555e7e511fe80078b233324f3442d79cd590c6; reviewed fingerprint 754ea4debaa8a902554b9dc1e99b17ecf815f612a957d8c9aabe6010dd6b7694. User Windows transcript SHA-256 27f848f89f80e0367a9f743bf6b02bd5744280a94a3bf6a029ee239c01d80e41. Only latest P10J08 run counted; old failed run retained in prior evidence. Source audit 390/390, 16 shared pairs, 20 auxiliary blobs; unchanged reviewed dependency inventory and install passed. Backend 821/839 passed, 18 skipped (13 PG, 5 platform), zero failures; Node 369 pass, 1 skip; 9 archive tests. Next build/typecheck passed. 7 loopback API parity, 4 browser scripts, 52 baseline captures (13 views x 2 widths x 2 themes); W8 before/after guard for 5 sample DBs passed. INSTALL_OK, BUILD_TEST_OK, SMOKE_OK markers match review. User transcript evidence, not independent replay. No raw PNGs or reviewed pixel baseline supplied; no new DAG interaction-specific browser acceptance inferred. CSS autoprefixer and Starlette warnings remain. No live agents, external effect, main/CI/PROD or independent acceptance.

0222 concurrent head 70d6c305c34a36361214343526d5c134cb6c9c9f: 326 same, 49 UI-only, 41 core-only, 5 divergent product paths; shared Dashboard, two lifecycle panels, intent_authority and manifest require explicit three-way reconciliation. No merge. Core 7/16 unchanged. Historical UI 21/40 ordinal retained pending explicit gate mapping; W8 8/8 local stages now passed.

Next P10J-09: collect exact source ZIP and raw review/log/markers/52 PNG evidence separately, inspect visual baseline, targeted React graph/editor/role/office interactions, prepare separate 0222 union candidate only after source/authority review. Re-run W8 with union-specific locks and PG tests in permitted disposable environment. Rollback to tested UI commit; no live database restore.

---
# UI-P10J-08 — Windows portability candidate verification
Exact source eb77018c9e0b4b0f403cb07d899d5329896e9427, manifest 2a555e7e511fe80078b233324f3442d79cd590c6. Fresh checkout and stage. Use tests/integration/w8_p10j08.py audit, prepare, compare lock inventory and review new fingerprint before install/test/smoke. Old stage preserved. Original full test 821 pass/18 skip, 369 Node pass/1 skip, Next.js FAIL. Candidate has not passed build. No independent acceptance or branch merge. Recheck current core heads before union.

# P10J-07 — environment HOLD, next actual W8

Use docs/UI-P10J/P10J07_W8_RUNBOOK.md on network-capable isolated DEV. Exact UI checkout 390 pins, prepare/review locks before install/test/smoke. Recheck 0220/0221 and UI heads. No new duplicate features or automatic merge. Combined candidate only after source compatibility and explicit scope; 21/40, core 7/16, independent 0/7 unchanged.

# UI-P10J-06 — exact checkout and product verification

Check parallel heads, materialize exact 390-pin checkout; verify W8 P10J-05 adapter chain, prepare/review locks before full build/test/smoke. Validate DAG selection and edit interactions, lifecycle filtering/reset, role contexts and office previews in actual React browser. No live runtime/authority/core merge, main, CI or PROD. Continue presentation work separately from acceptance. Previous pointer below.

# UI-P10J-05 — full checkout / W8 and parallel UI work

Re-read P10I/P10J/core HEADs, use parallel protocol and checkpoint. Run full 386-pin audit on exact checkout; load W8 P10J→P10I→P10H chain, prepare/review locks before install/test/smoke. Keep separate core 0213, D03/D04 HOLD. In parallel advance historical Runtime timeline, Project/Workflow graph and Office presentation only, with exact source and test evidence. No main, CI, PROD or real grants. Historical P10I handover snapshots preserved.

# UI-P10J-04 — exact source and W8 acceptance

Verify 386 SHA pins in clean full local checkout; audit/prepare/review/install/test/smoke with w8_p10j.py, inspect missing P10I historical auxiliary records. Validate React controls, graph and office visuals, maintain D03/D04 HOLD. No live authority, main, CI or PROD. Preserve evidence. Historical pointer below.

# UI-P10J-03 — exact checkout and W8

Recover remaining product pins in bounded batches; materialize complete checkout; run original archive auditor and W8 audit/prepare/review/install/test/smoke. New checkout audit is supplemental only. No CI, main merge, PROD or real grant. D03/D04 independent HOLD. Continue UI tracks without claiming full build. Historical pointer below.

# UI-P10I — full checkout and reviewed product verification

Priority: obtain exact full P10H GitHub archive (not selected evidence ZIP), verify 381 product SHA-256 entries and auxiliary pins. Recover original W8 harness auxiliary closure; run audit, prepare reviewed lock inventory, install only after explicit review, then full backend/Next build and product smoke 7 API/52 captures. Do not bypass lock or security gates. Original 0210/0211 wrapper diagnostic work is complete in selected environment; run locked regression when available. D03/D04 external authority design requires independent approval and verification; no real grant. Continue A-H, especially ProjectStudio graphical context and React accessibility/office product acceptance. Retain previous decisions and source versions; update catalog/progress/evidence/handover.
