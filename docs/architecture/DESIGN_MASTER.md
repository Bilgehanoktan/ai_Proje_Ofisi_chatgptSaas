# Design Master — current index
[0158 parent](../0158/AI_Company_OS_DESIGN_MASTER_DOC_REV_0158_RECOVERY_ADAY.md) + [0159-A](../0159A/CHANGE_RECORD.md) + [0159-B](../0159B/ARCHITECTURE_ADDENDUM.md) + [0160](../0160/ARCHITECTURE_ADDENDUM.md). Bu indeks tam master yerine geçmez. Tam teslimatta 0159-B master byte-exact prefix ve 0160 ek bulunur.

[0161 ek](../0161/ARCHITECTURE_ADDENDUM.md). Tam master önceki 0160 byte-exact prefix + 0161 ek olarak teslim edilir.

[0162-A tasarım eki](../0162A/ARCHITECTURE_ADDENDUM.md) — öneri, R8 kaynakları değişmedi; normatif kabul değil.

[0162-B C çalışma kararı](../../decisions/CEO/CEO_WORK_MODE_20261114_C.md) · [uygulama hazırlığı](../0162B/IMPLEMENTATION_CONTRACT.md). R8 kaynak değişmedi; normatif kabul yok.


[0162-C local package reference](../0162C/LOCAL_PACKAGE_REFERENCE.json) · [0162-D static review](../0162D/ARCHITECTURE_ADDENDUM.md). R8 product remains; no normative change.

[0162-E pinned integration scope](../0162E/SCOPE_0162E.json) — H01 request recorded; R8 unchanged, HOLD.

[0162-F internal agent review ADR](../0162F/ADR_AGENT_REVIEW.md) — proposed, not ratified; no normative or source change.


[0163 agent review bootstrap and R9 UI source integration](../0163/ADR_AGENT_BOOTSTRAP.md) — scoped source-only, normative acceptance HOLD.

[0164 R10 review candidate](../0164/ARCHITECTURE_ADDENDUM.md) — quarantine only, R9 unchanged.

[0165 R10 source integration and registry/policy/evidence candidates](../0165/ARCHITECTURE_ADDENDUM.md) — no runtime acceptance.

[0166 R11 trust and staging readback](../0166/ARCHITECTURE_ADDENDUM_0166.md) — quarantine only, R10 unchanged.

[0167 R11 source promotion and local MVP setup](../0167/ARCHITECTURE_ADDENDUM.md) — source-only, runtime HOLD.

## 0168 local MVP execution path
[Parallel DAG, scope and evidence](../0168/LOCAL_MVP_PARALLEL.md). R11 normative source remains unchanged; no new runtime or acceptance authority.

## 0169
[Sequential acceptance program](../0169/PHASE01_PREFLIGHT.md). R11 product baseline unchanged; authority and independent gates retained.

## 0170
[Phase 01 dependency preflight and remote integrity evidence](../0170/PHASE01_DEPENDENCY_AUDIT.md). No architecture or product authority change.

## 0172 — EDS
[Executive Design System architecture and implementation plan](../0172/ARCHITECTURE_ADDENDUM.md). W1 parallel, R11 unchanged.

## 0173
[Parallel EDS source candidates](../0173/ARCHITECTURE_ADDENDUM.md) · [integration and acceptance](../0173/INTEGRATION_AND_TEST_PLAN.md). R11 unchanged.

## 0174 — standing development
[CEO decision](../../decisions/CEO/CEO_0174_STANDING_DEVELOPMENT.md). Mandatory integration and evidence per round; independent gates unchanged. R11 remains until permitted promotion.


## 0177 — W1 EDS candidate
[Addendum](../0177/ARCHITECTURE_AND_CATALOG.md). No normative authority or product acceptance change; prior architecture preserved.


## 0178 — W1 EDS fix and W8 preflight
[Addendum](../0178/ARCHITECTURE_AND_CATALOG.md). No normative change.


## 0179 — EDS integration PRE
[Exact scope and gate boundary](../0179/INTEGRATION_PRE.md). No product promotion or normative change.


## 0180 — CEO-0179=B controlled integration and EDS product source
[Addendum](../0180/ARCHITECTURE_AND_CATALOG.md). Source integration in isolated development only; runtime gates unchanged.


## 0181 — D0 MVP diagnostics (2026-11-15)
Source `a31040d8116a58521393040061abe0078c83800d` / `recovery/0181-mvp-diagnostics`. 19 product source changes + manifest; 162 manifest entries, 163 files. Selected local synthetic tests 38/38 (24 Python, 14 Node including loopback GET 200). Full pinned dependency locks, full frontend build/browser and full backend suite NOT_RUN; independent acceptance HOLD. See docs/0181/ARCHITECTURE_AND_CATALOG.md and releases/GITHUB_READBACK_0181.json. Prior history preserved.


## 0182 — persistent synthetic workbench
[Addendum](../0182/ARCHITECTURE_AND_CATALOG.md). Canonical mapping and authority unchanged.

## 0183 — D0 atomicity lab and lifecycle viewer
[Addendum](../0183/ARCHITECTURE_AND_CATALOG.md). Physical mapping, actual security and provider authority unchanged.

## 0184 — persistent D0 outbox review/read-only projection
[Addendum](../0184/ARCHITECTURE_AND_CATALOG.md) · [R03 gaps](../0184/R03_MAPPING_GAPS.md). No normative or physical mapping change.

## 0185 — typed provider review, admission bundle, shared Outbox contract
[Addendum](../0185/ARCHITECTURE_AND_CATALOG.md). No normative mapping, trust or execution authority change.

## 0186 — durable synthetic admission and settlement, CEO readback
[Addendum](../0186/ARCHITECTURE_AND_CATALOG.md). No canonical physical mapping or authority change.

## 0187 — Workbench history to Office role projection
[Addendum](../0187/ARCHITECTURE_AND_CATALOG.md). No canonical T1, trusted clock, geometry join or authority change.

## 0188 — Paired synthetic task/budget readback
[Addendum](../0188/ARCHITECTURE_AND_CATALOG.md). Optional fresh sample marker, double read, no causal/T1 or lease authority.

## 0189 — Actual paired D0 integration and PostgreSQL probe
[Addendum](../0189/ARCHITECTURE_AND_CATALOG.md). Existing product unchanged; real selected integration PASS, candidate PostgreSQL checks NOT_RUN. Canonical R03 mapping remains HOLD.

## 0190 — T1 contention and R03
63 selected controls PASS, 14 PG checks NOT_RUN, canonical mapping HOLD. Product files unchanged. [Architecture](../0190/ARCHITECTURE_AND_CATALOG.md) · [R03](../0190/R03_T1_DECISION_PACKET.md).

## 0191 — Logical T1
[Addendum](../0191/ARCHITECTURE_AND_CATALOG.md). Mapping HOLD.

## 0192 — Partial core integration
[Addendum](../0192/ARCHITECTURE_AND_CATALOG.md). No live runtime or physical mapping.

## 0193 — Runtime transition
[Addendum](../0193/ARCHITECTURE_AND_CATALOG.md) · [Product roadmap](../implementation_plan/PRODUCT_ROADMAP_8_PHASES.md). No normative change.

## 0194 — D0 ordinary-transition mapping and scheduler
[Addendum](../0194/ARCHITECTURE_AND_CATALOG.md). Candidate tables and synthetic lease/clock recheck; no canonical mapping or normative change.

## 0195 — D0 admission / first lease / sample budget
[Addendum](../0195/ARCHITECTURE_AND_CATALOG.md). Nine-role initial admission candidate; no normative mapping or real authority.

## 0196-L — admission-bound ordinary transitions / lease renewal / D0 failure settlement
[Addendum](../0196L/ARCHITECTURE_AND_CATALOG.md). No new normative mapping or real authority; separate memory/model workstream remains unmerged.
