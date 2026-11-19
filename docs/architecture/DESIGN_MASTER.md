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

## 0198-E — complete pinned D0 history readback
[Addendum](../0198E/ARCHITECTURE_AND_CATALOG.md). Internal historical Office projection only; no shared schema, normative mapping or real authority change.

## 0199-C — exact project-wide D0 causal history and optional exclusive budget replay
[Addendum](../0199C/ARCHITECTURE_AND_CATALOG.md). Internal historical input; no shared contract, normative mapping or real authority change.

## 0200-S — guarded read-only consistent snapshot for D0 plan history
[Addendum](../0200S/ARCHITECTURE_AND_CATALOG.md). Protocol tested, actual PG not run; no normative or shared contract change.

## 0201-R — retained history references and terminal reference match
[Addendum](../0201R/ARCHITECTURE_AND_CATALOG.md). D0 local archive tested; wrapper/PG/independent custody HOLD/NOT_RUN. No canonical migration or normative change.

## 0202-S — signed retained checkpoint and terminal receipt
[Addendum](../0202S/ARCHITECTURE_AND_CATALOG.md). Fixture Ed25519 and local archive tests PASS; external key custody, actual T1/PG/readback, W-A and independent acceptance HOLD. No normative authority or schema change.

## 0203-T — terminal anchor and strict historical readback
[Addendum](../0203T/ARCHITECTURE_AND_CATALOG.md). Candidate same-T1 terminal anchor; 54 selected PASS; full lifecycle/PG/R03/IV remain open.

## 0204-C — company coordination
[Addendum](../0204C/ARCHITECTURE_AND_CATALOG.md). Explicit project membership, company sequence and shared allocation replay; 51 new +54 rerun PASS. Candidate T1 decorator, PG/R03/IV remain open.

## 0205-R — company recovery
[Addendum](../0205R/ARCHITECTURE_AND_CATALOG.md). D0 checkpoint, local witness CAS and unknown transaction quarantine; 43 new +105 rerun PASS; independent custody, T1 integration and PG remain open.


## 0206 — controlled D0 unified product source
[Architecture](../0206/ARCHITECTURE_AND_CATALOG.md) · [Reconciled P05](../W1-0198-P05/ARCHITECTURE_AND_CATALOG.md) · [AI/Memory](../0196-MA/ARCHITECTURE_AND_CATALOG.md) · [P06 historical evidence](../W1-0198-P06/ARCHITECTURE_AND_CATALOG.md). 335 product files; 24 selected actual SQLite regressions PASS; combined runtime/independent acceptance open.

## 0207 — D0 cross-boundary evidence
[Addendum](../0207/ARCHITECTURE_AND_CATALOG.md). Selected 72 tests PASS; 55-file static lock, 29 cases NOT_RUN. Joint memory/model revocation binding remains P0 open. No production authority or normative change.

## 0208 — D0 joint Runtime context
[Addendum](../0208/ARCHITECTURE_AND_CATALOG.md). New joint digest and two memory span observations; 98 selected PASS. D-02 restore-external latest witness and mandatory effect boundary HOLD. No normative permission change.

## 0209 — signed memory witness and ordinary T1
[Addendum](../0209/ARCHITECTURE_AND_CATALOG.md). D0 external pin and original ordinary mapping SQLite pass; D-03 final check to commit race reproduced. Independent authority unchanged.

## 0210 — local revocation fence and durable intent quarantine
[Addendum](../0210/ARCHITECTURE_AND_CATALOG.md). Cooperating SQLite writer serialization through T1 commit and durable quarantine pass. D-03 external race and D-04 restore gap open. Independent authority unchanged.

## 0211 — D0 separate intent authority
[Addendum](../0211/ARCHITECTURE_AND_CATALOG.md). Two product additions; 9 component checks PASS and 1 authority-restore residual reproduced. Original T1, independent root, core29, Company/Terminal, PG/RLS and build NOT_RUN/HOLD. No normative change.

## 0212 — original core and composed D0 T1 verification
[Addendum](../0212/ARCHITECTURE_AND_CATALOG.md). 55/55 core files, 29/29 unpinned diagnostic tests, direct authority/T1 7/7, Company/Terminal 6/6. No existing product code or normative change; full wrapper, independent authority, PG/RLS/build remain open.

## 0213 — two-project D0 budget race and 0211 wrapper test preparation
[Addendum](../0213/ARCHITECTURE_AND_CATALOG.md). 55/55 pinned core and 56/56 diagnostic tests; four new multi-project SQLite cases. Six original wrapper integration tests only prepared, NOT_RUN. PostgreSQL/RLS/Next/browser and independent authority still HOLD. No normative decision or product runtime change.

## 0214 / 0215 — original wrapper, external claim observation, PG runner and historical UI
0214 source checkpoint is preserved at `a4a6aba3e986927b4e2b0157028e6623c669864e`; prior recorded 10 original wrapper tests, 1 restore residual. [0215 addendum](../0215/ARCHITECTURE_AND_CATALOG.md): 15 read-only signed local claim checks, 14 PG runner unit checks and 17 UI reference checks. Actual PG/RLS/build/browser and independent custody remain HOLD; no normative changes or effect authorization.

## 0216 — isolated synthetic effect fence reference
[Addendum](../0216/ARCHITECTURE_AND_CATALOG.md). 13 local tests, 1 expected restore residual; no canonical or normative change, independent and mandatory gateway acceptance HOLD.

## 0217 — signed consume observation and read-only studio context
[Addendum](../0217/ARCHITECTURE_AND_CATALOG.md). 37 selected checks including expected restore residual; no independent or normative change, actual PG/RLS/Next/browser open.


## 0218 — architecture realignment and user-approved integration sequence
[Addendum](../0218/ARCHITECTURE_AND_CATALOG.md) · [0218–0225 sequence](../implementation_plan/INTEGRATION_SEQUENCE_0218_0225.md). Product unchanged; remote source preflight, no new gate or normative decision. Original scope and grant boundaries preserved.


## 0219 — D0 company/admission/witness composition
[Addendum](../0219/ARCHITECTURE_AND_CATALOG.md). Reuse existing T1 mappings under explicit company profile; 12 excerpt diagnostics only, no actual combined wrapper/PG acceptance or normative change. Old profiles preserved.


## 0220 — pinned scheduler and explicit company admission
[Addendum](../0220/ARCHITECTURE_AND_CATALOG.md). Existing plan/DAG and T1 coordinator reused; exact initial roster and historical evidence before root admission, no bare success. 12 exact pure tests and 12 prior excerpt diagnostics; SQL and independent acceptance open. No normative changes.


## 0221 — fixed sample result context
[Addendum](../0221/ARCHITECTURE_AND_CATALOG.md). Existing model/skill/tool/memory inspectors and retained archive bound to opt-in company/witness intent fence. 18 new local checks, full SQL NOT_RUN; no real effects or normative change.


## 0222 — common CEO / Office historical snapshot
[Addendum](../0222/ARCHITECTURE_AND_CATALOG.md). Existing fixed historical prefix read reused once; bounded finite SSE with digest, shared frontend context; project/world/placement/live remain HOLD. 39 selected controls, full actual DB/browser/PG/build not run. No normative changes.


## 0223 — Agent / Workflow Studio
[Addendum](../0223/ARCHITECTURE_AND_CATALOG.md). Existing compiler/DAG and shared historical provider reused; fixed Research plan API, exact role context and unbound evidence timeline. Plan revision mismatch remains HOLD. 63 selected checks, actual DB/browser/PG/build open; no normative changes.


## 0224
Canonical Research root evidence candidate; exact plan and company snapshot, archive/local receipt readback candidate. No verified SUCCESS, QA/IV/H01 or real authority. See docs/0224/ARCHITECTURE_AND_CATALOG.md. 43 selected PASS; full SQL8 NOT_RUN; 7/16.


## 0225 — actual integration validation
Four scoped integration suites PASS (32 new +102 prior, 134 unique). Actual SQLite T1 and pinned admission/history, persisted historical DB and mounted routes, real loopback compiled TS proxy/Studio. No runtime source changes; original suites and full result path still open. 7/16 gates unchanged. See docs/0225/ARCHITECTURE_AND_CATALOG.md and handover/NEXT_STEP_0225.md.


## 0226 — recovered original regression
173 recovered original tests +134 prior selected reruns =307 unique selected tests (254 Python, 53 Node). Original SQL6 and DB4 PASS; original core29 current source PASS nonlocked, historical locked acceptance NOT_RUN. No product changes. 7/16 gates unchanged. See docs/0226/ARCHITECTURE_AND_CATALOG.md and docs/0226/LOCAL_ACCEPTANCE_RUNBOOK.md.


## 0227 — environment preflight (BLOCKED)
[Architecture](../0227/ARCHITECTURE_AND_CATALOG.md) · [Connected workstation](../0227/CONNECTED_WORKSTATION_0227.md). 392/392 remote paths/sizes, 55/55 historical blob/sizes; local checkout/resolver blocked. No runtime changes, test rerun or normative decision. 7/16 unchanged; B3 HOLD.

## 0227-A3 — historical evidence only
8/16; A3 transferred from exact historical A0F raw review. Product environment and independent acceptance open. [Evidence](../../tests/evidence/A3_EVIDENCE_TRANSFER_0227.json).


## 0227-E1 — reviewed-lock reuse execution packet
scripts/run_e1_0227.py reuses original W8 lock inventory, exact A0C hash/wheels and a fresh source-bound review. It copies only pinned product and DB source into a new stage, installs Python offline with hash verification and npm ci with scripts disabled, runs original 6/10/8 suites with exact collection and exit counts. 10/10 synthetic runner mechanics PASS; Windows prepare/execute NOT_RUN and zero product tests. 8/16 unchanged. No runtime/product changes, no CI, no merge. If A0 raw wheel/lock bytes unavailable or mismatch, stop; retain failed stage, use separately reviewed recovery. Evidence: tests/evidence/E1_RUNNER_MECHANICS_0227.json.


## 0227-E1 Windows execution transcript
User explicitly approved new fingerprint and ran the isolated Windows stage. Six install/inventory commands and original 0219/0221/0224 suites exited zero; runner reported 24/24 PASS after source/lock rechecks. Actual SQLite D0 execution reported, not independent replay. Raw reports/logs/locks pending; E1 gate remains open, 8/16. No additive test aggregate, no product/source changes. Evidence: tests/evidence/E1_WINDOWS_EXECUTION_TRANSCRIPT_0227.json.


## 0227-E1 final raw review — PASS
User-uploaded raw ZIP 14/14 CRC, 9/9 report log hashes, 28 Python wheel/installed versions and 61 npm lock entries, 30 installed versions, 24 original test names match source and all pass. Two extraneous npm packages are exact optional lock entries; E3 recheck. No raw wheel binaries or independent replay. E1 closed, 9/16 (56.25%); product and DB source unchanged; prior 307 count separate. D1/D2 next; D3/E2/E3/E4/B3 open. Evidence: tests/evidence/E1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D1 — Windows inventory checkpoint
No PostgreSQL commands, default Program Files directory, service or Psycopg packages found in user checks. Proposed PG17.12 and Psycopg3.3.9 Windows cp314, separate loopback-only D0 stage. Candidate download and hash/provenance review pending; no install, DB, test or gate promotion. E1 remains accepted and unchanged, 9/16. Evidence: tests/evidence/D1_WINDOWS_INVENTORY_0227.json.


## 0227-D1 — candidate downloads and connection runner
Server ZIP checksum matches EDB (user transcript); Psycopg/psycopg-binary/tzdata downloads successful. Public PyPI hashes verified for pure Psycopg and tzdata; local JSON API exact check required for binary. New pinned scripts/run_d1_0227.py uses reviewed E1 wheelhouse read-only, new 31-package lock, disposable loopback-only SCRAM cluster, two non-superuser/non-BYPASSRLS DBs, write/read/rollback and graceful stop. Linux syntax/fixture checks only; no Windows execution or new gate. 9/16 unchanged; PG13/RLS pending. Evidence: tests/evidence/D1_WINDOWS_WHEELS_READY_0227.json.


## 0227 D1 initdb HOLD
User transcript confirms all 3 PyPI checks and reaches postgres 17.12/initdb after 31-pin installation sequence. Password mismatch aborts initdb; rerun intentionally refused by fresh-stage guard. Preserve failed stage; copy only ZIP and wheels to new sibling stage and repeat isolated D1. No connection or PG13/RLS test; 9/16 unchanged. tests/evidence/D1_WINDOWS_INITDB_HOLD_0227.json


## 0227-D1 retry1 connection HOLD
User reports initdb and PostgreSQL start/stop successful, child OperationalError masked by runner; exact failing statement unknown. No D1 acceptance. Preserve retry1 and diagnose with interactive read-only psql connection and role/database existence checks, then stop own cluster. No password or private log transfer; no reinstallation or grants. 9/16. Evidence: tests/evidence/D1_WINDOWS_RETRY1_CONNECTION_HOLD_0227.json


## 0227-D1 authentication diagnosis and candidate fix
User psql diagnostic starts server, reaches loopback 55432, FATAL password authentication failed (exit 2), stops successfully. Exact mismatch cause unknown. New scripts/run_d1_0227_authfix.py generates ephemeral ASCII admin, restricts and verifies temporary pwfile ACL before writing, removes file in finally, sends same credentials to child via stdin; SCRAM preserved; test password user-held. Compile and four synthetic controls PASS; Windows not run. Retry2 fresh input-only copy; old stages preserved. 9/16 unchanged. tests/evidence/D1_WINDOWS_AUTH_HOLD_AUTHFIX_0227.json


## 0227-D1 retry2 connection PASS — raw review pending
User transcript: PG17.12, Psycopg3.3.9 binary, libpq180004, SCRAM loopback 55432, two separate DBs with non-superuser/non-BYPASSRLS test role; both write/read/rollback PASS; source before/after match, server stopped. Existing input-directory/copy errors preceded successful runner preflight; retain anomaly and do not rerun install. Raw evidence pending; 9/16 unchanged; PG13 and RLS NOT_RUN. tests/evidence/D1_WINDOWS_CONNECTION_TRANSCRIPT_0227.json


## 0227-D1 final raw review — PASS
Raw ZIP 8/8 CRC, 5/5 log/report hashes, 31/31 installed pins, original 28 E1 lock lines exact from reopened E1 archive, two PostgreSQL DB probes PASS; SCRAM loopback and stopped state evidenced. D1 accepted, 10/16 (62.5%). No independent replay, raw binaries absent, PG13/RLS/build open. Source unchanged. Next: docs/0227/D2_PG13_RUNBOOK.md. Evidence: tests/evidence/D1_RAW_EVIDENCE_REVIEW_0227.json.


## 0227-D2 — original PG13 execution PASS, raw report pending
Uploaded Windows transcript parsed: 0194 5/5, 0196L 5/5, 0200S 3/3, all failure/error/skip counters zero; exact runner source and 13 source test names reviewed; source/DDL verified; exit 0 and server stopped. Raw D2_PG13_RESULT.json pending. Expected report hash reconstructed, not measured on original. 10/16 unchanged pending review; D3/RLS/B3 open. tests/evidence/D2_WINDOWS_PG13_TRANSCRIPT_0227.json


## 0227-D2 final raw review — PASS
Original Windows JSON: 937 bytes, SHA256 79085656ad4d782a012642518d9d8724514976082af0c5734c5d04dcfb82cf05, exact CRLF serialization and prior transcript match. 13/13 PG cases, source/DDL verified; 11/16 (68.75%). D3 separate RLS/non-owner contention, E2/E3/E4 and B3 open; source unchanged. Evidence: tests/evidence/D2_RAW_EVIDENCE_REVIEW_0227.json; next: docs/0227/D3_RLS_SCOPE_REVIEW.md.


## 0227 D3 scoped acceptance — evidence transfer
D3-R4 review 426a2e69dd193a9ec8f61181cc809c28fc50733c verified 230/230 actual fixture controls, 7/7 ZIP entries, 6/6 file hashes, owner FORCE RLS and non-owner contention. D3 current binary criterion PASS; 12/16 (75%). Evidence-only transfer, no source merge, no product RLS deployment. Canonical policy, pool integration, full company stream PG and independent security HOLD/open. Remaining E2/E3/E4 and B3; coordinate Unified U3 owner. tests/evidence/D3_EVIDENCE_TRANSFER_0227.json


## MI-03-GATE01-AUTHORITY-API-REVIEW-01 — static owner API review
[Catalog/evidence](../master-integration/MI-03-GATE01-AUTHORITY-API-REVIEW-01/CATALOG_AND_EVIDENCE.json) · [Runbook](../master-integration/MI-03-GATE01-AUTHORITY-API-REVIEW-01/ARCHITECTURE_RUNBOOK_HANDOVER.md). G2/G7 exact IAM and authority pins; legacy wrapper lacks session_check; explicit protected entry remains HOLD. No product or acceptance change.


## MI-05-06-09-SOURCE-LOCK-REVIEW-01 — source and original lock readback
[Architecture, maintenance and handover](../master-integration/MI-05-06-09-SOURCE-LOCK-REVIEW-01/ARCHITECTURE_RUNBOOK_HANDOVER.md) · [Catalog/evidence](../master-integration/MI-05-06-09-SOURCE-LOCK-REVIEW-01/CATALOG_AND_EVIDENCE.json). Common U3 preserved; MI06 nine and MI09 five owner paths reviewed; exact original npm lock recovered from ORG, no regeneration. No source change, full build or acceptance. Existing owners and permissions unchanged.


## MI-05-06-PROJECTION-REPLAY-01
[Architecture / evidence](../master-integration/MI-05-06-PROJECTION-REPLAY-01/ARCHITECTURE_RUNBOOK_HANDOVER.md). Original closed ORG route subset 8/8 replay; existing source-lock and owner gates retained.


## MI-COMMON-ORG-SKILL-02 — exact closed ORG/Skill source convergence
Common 61bb06efbba7544bfc68260ed8eb4d342cab9b8e, parent bf87d5c48c7fee97fe12d0a28df3be80249f7306, 539 product files / 538 manifest; 14 exact owner paths, one registry test adaptation, 31/31 exact transferred product+aux paths. 7/7 fixture runner controls, no product test or full build. New W8 adapter preserves original lock, U3 and historical overlays. Owner review and all actual authorization gates HOLD. [Source transfer](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/61bb06efbba7544bfc68260ed8eb4d342cab9b8e/docs/master-integration/MI-COMMON-ORG-SKILL-02/SOURCE_TRANSFER.json) · [Runbook](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/61bb06efbba7544bfc68260ed8eb4d342cab9b8e/docs/master-integration/MI-COMMON-ORG-SKILL-02/ARCHITECTURE_RUNBOOK_HANDOVER.md).


## MI-03-GATE02-PROVENANCE-BOUNDARY
[Catalog and evidence](../master-integration/MI-03-GATE02-PROVENANCE-BOUNDARY/CATALOG_AND_EVIDENCE.json) · [Runbook](../master-integration/MI-03-GATE02-PROVENANCE-BOUNDARY/ARCHITECTURE_RUNBOOK_HANDOVER.md). Three actual local diagnostic tests on exact R3 DDL and D4 review; owner issuance, actual P02, protected COMMIT remain HOLD. No product change.


## MI03-GATE02-ASSIGNMENT-LIFECYCLE-D0
Isolated G8 descendant [6efc6714757e](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/commit/6efc6714757ebd698d27efd7022afc2c92af70d0), three candidate source paths, one new disposable SQLite table, 20/20 actual local unit tests on 3/3 exact original sources, 13/13 GitHub readback. Existing ORG proposal remains HOLD; append-only accepted/revoked D0 review record, CAS, expiry, no grant or dispatch. Original OperationsStore and Core adapter full replay NOT_RUN; actual owner provenance/P02/G9/COMMIT HOLD. [Catalog and evidence](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/6efc6714757ebd698d27efd7022afc2c92af70d0/candidates/MI03-ASSIGNMENT-D0/CATALOG_AND_EVIDENCE.json) · [Runbook](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/6efc6714757ebd698d27efd7022afc2c92af70d0/candidates/MI03-ASSIGNMENT-D0/ARCHITECTURE_RUNBOOK_HANDOVER.md). Product-dev/main unchanged; rollback isolated candidate only. Next: ORG/Core owner review exact source, original Store+Core historical replay, IAM/D4 owner-issued evidence. Weighted D5-G 42.5 unchanged.


## MI-COMMON-03-SELECTED-REGRESSION — selected common regression
Exact source 61bb06efbba7544bfc68260ed8eb4d342cab9b8e, manifest 03af243e8683f92c5d9c0b24e90b70d2bd6af29f. Actual 97/97 selected tests (ORG31, projection reader12, Skill41, registry13) and 26/26 local bytes/pins; remote model/memory 114/114, historical Core 55/55 and shared pairs 17/17. No source change or full build; no protected authority or acceptance. [Evidence](../master-integration/MI-COMMON-03-SELECTED-REGRESSION/EVIDENCE.json). Raw logs/source pins in separately delivered ZIP with SHA-256 75094e1c4b69045fd01b513bb592675ff2bd7dd4974fe59b591bad7a181e9767.


## MI03-G6A-D4-ORG-CROSS-REPLAY-01
59/59 actual selected original tests (G1 14, G2 19, G4 14, G5 12) on 28/28 exact local pins, verified pre/post. G6A plus common D4/Core and original ORG R3 auxiliary closure. 26 existing G4/G5 cases replayed on G6A, 33 repeat; do not count 47 preceding subset separately. No product transfer, actual owner issuance, strict COMMIT, full G2/G9, PG/W8 or acceptance. Preserve competing assignment candidate and original durable_ops independently. D5-G 42.5% unchanged. Evidence: docs/master-integration/MI03-G6A-D4-ORG-CROSS-REPLAY-01/EVIDENCE.json. Raw log SHA-256 bfafe7ccfeec14afe978a340dc14f32a44877891de08ee79ae43fa034583ca9b. ZIP 35 files SHA-256 d3477476aec41ef928cfb5f4c6f05ae7d061bd1dccaa2f438a5120211f0cd272.


## MI03-GATE02-03-PACKAGED-REGRESSION-01 — izole G8/GATE03 ürün kaynak uyumluluğu
59 özgün IAM/ORG regresyonu + 8 yeni yerel Store kontrolü + 4 mevcut GATE03 paketleme testi = **71/71 PASS**, 32/32 kaynak/test blob kimliği (koşum öncesi/sonrası). Gerçek SQLite geçici depo, Python 3.13.5. G8'in ek 41 satırlı owner `durable_ops.py` kullanıldı; gerçek Core Research okuyucusu bu seçili sette yok, pozitif Store kabulü ve P02 NOT_RUN; doğrudan fixture ACCEPTED_D0 yetki değildir. GATE03 izole 552/551 aday, 539/538 ortak kod tabanına aktarılmadı. Özgün 0214 Memory–T1 10, G2 50, G9 7, PG/strict COMMIT ve tam W8/build NOT_RUN. [% dökümü](../master-integration/MI03-GATE02-03-PACKAGED-REGRESSION-01/EVIDENCE.json) · [Teknik katalog](../master-integration/MI03-GATE02-03-PACKAGED-REGRESSION-01/CATALOG.json) · [Runbook](../master-integration/MI03-GATE02-03-PACKAGED-REGRESSION-01/ARCHITECTURE_RUNBOOK_HANDOVER.md). İzinler, eski dallar ve ürün kabulü değişmedi; D5-G 42.5% → 42.5%. Yerel 40-dosyalık ZIP SHA-256: 955e76171b52997b0c3053de80e5cbb98bbb3eb17326abc55654022a91678646.


## MI-COMMON-04 — source-locked recovery for Model/Memory and historical Core
[GitHub helper](../master-integration/MI-COMMON-04-PINNED-RECOVERY/pinned_source_recovery.py) · [technical catalog](../master-integration/MI-COMMON-04-PINNED-RECOVERY/CATALOG.json) · [runbook](../master-integration/MI-COMMON-04-PINNED-RECOVERY/RUNBOOK.md). Separate immutable restored source roots for 114 Model/Memory and 55 historical Core paths; 26 overlapping paths, 2 distinct historical versions. Tested 14 synthetic recovery controls locally; original 344/29 and W8 full build/browser NOT_RUN. 24/24 original W8 adapter blobs and 23/23 parent pins match, npm lock 61 registry metadata entries. Product source/manifest and CEO security boundaries unchanged.


## MI03-GATE02-ASSIGNMENT-RECOVERY-79
79/79 actual selected regression (71 historical/replayed + 8 new D0 SQLite diagnostics), original 32/32 exact Git source pins, 44/44 ZIP SHA files; joint old DB + old retained head reaccept residual deliberately reproduced — **not safety acceptance**. Core positive readback and 0214 10/10 original Memory–T1 remain NOT_RUN. [Evidence](../master-integration/MI03-GATE02-ASSIGNMENT-RECOVERY-79/EVIDENCE.json) · [Runbook](../master-integration/MI03-GATE02-ASSIGNMENT-RECOVERY-79/ARCHITECTURE_RUNBOOK_HANDOVER.md). Isolated 45-file package SHA-256 6a486e66223c424108b85bfe43e912899935e9d34483f4c7d1d31a55917ea4e4. G8 owner, GATE03 owner and common/product refs unchanged; weighted D5-G 42.5→42.5, Core12/16, MVP0/11. No live schema/API/event/grant/CI changes.


## MI03-GATE02-STORE-CORE-ISOLATED-REPLAY-01
[Evidence](../master-integration/MI03-GATE02-STORE-CORE-ISOLATED-REPLAY-01/CATALOG_AND_EVIDENCE.json) · [Runbook](../master-integration/MI03-GATE02-STORE-CORE-ISOLATED-REPLAY-01/ARCHITECTURE_RUNBOOK_HANDOVER.md). 16/16 new real local synthetic SQLite tests on source-exact assignment/Store extension; original 20/20 unit methods repeated. ORG Store dependencies and Core reader mocked, so original full Store/Core integration NOT_RUN and P02/G9/COMMIT remain HOLD. No new product paths, grants, acceptance or progress change; D5-G 42.50% retained.


## MI-COMMON-05 — user-PC exact full-tree archive transfer
[Runbook](../master-integration/MI-COMMON-05-LOCAL-CHECKOUT/ARCHITECTURE_RUNBOOK_HANDOVER.md). Full Git tree source 1953/1953, pinned 114 Model and 55 Core sources staged separately with unchanged original helper. 12/12 local synthetic archive safety tests PASS. User execution/report and original 344/29 full W8/browser NOT_RUN; no product, permission or acceptance change.


## MI10-D0-CI-GREEN-SSE-DIAGNOSTIC-20261119 — D0 CI / U3 SSE transport annex
An authorized GitHub-hosted, read-only draft PR #4 CI run [44613960595](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44613960595) completed 3/3 jobs: 538 source SHA256, 17 shared pairs, 33 helper blobs, original npm 61/61, 42/42 original selected SQLite D0, Next build/typecheck and **SSE-compatible diagnostic U3 browser** with five screenshot artifacts. The unchanged original U3 CDP response-body mechanism remains unresolved; per-request body freshness in CI shim requires owner review. Formal full W8/fingerprint, 265-source original T1 10, strict PostgreSQL and independent IV are NOT_RUN/HOLD. This is a non-normative evidence addendum, not an architecture or permission change. [Evidence](../master-integration/MI10-D0-CI-GREEN-SSE-DIAGNOSTIC-20261119/EVIDENCE_AND_CATALOG.json) · [Catalog and handover](../master-integration/MI10-D0-CI-GREEN-SSE-DIAGNOSTIC-20261119/ARCHITECTURE_RUNBOOK_HANDOVER.md).


## MI10-SSE-FRESHNESS-REPRO-20261120 — non-normative MI-10 browser evidence guard
The authorized draft MI-10 D0 CI #44614849105 remains **3/3 selected jobs PASS**, but the CI-only SSE adapter `window.__mi10LastStreamBody` uses a single last-body Promise. An **actual offline Node.js v22.16.0 negative reproducer** verified 5/5 controls and **two** old-body reuse windows when later fetches are pending. This is not an actual Chrome/product failure, does not invalidate previous source or D0 test pass, and does not change any architecture/authority semantics. Fresh per-request body binding must be reviewed by MI-10 owner before treating compatibility diagnostics as independent browser evidence; unmodified U3 CDP, full W8 and security IV remain HOLD. [Evidence](../master-integration/MI10-SSE-FRESHNESS-REPRO-20261120/EVIDENCE.json) · [Technical catalog and handover](../master-integration/MI10-SSE-FRESHNESS-REPRO-20261120/ARCHITECTURE_CATALOG_HANDOVER.md).
