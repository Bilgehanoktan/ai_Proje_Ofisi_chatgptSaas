# Proje indeksi — 0161
- [Devir](handover/CURRENT.md) · [Sonraki adım](handover/NEXT_STEP.md) · [Açık işler](handover/OPEN_ITEMS.md)
- [Design Master](docs/architecture/DESIGN_MASTER.md) · [Klasör standardı](docs/architecture/REPOSITORY_LAYOUT.md) · [0160 yol eşlemesi](catalog/RELOCATION_MAP_0160.json)
- [Frontend](product/ai-company-os-frontend/) · [Backend](product/ai-company-os-backend/)
- [122 kaynak kaydı](releases/SOURCE_MANIFEST_0161.json) · [Katalog v1.20](catalog/TECHNICAL_CATALOG.md) · [Kararlar](decisions/OPEN_DECISIONS.md) · [24 alan](progress/DEVELOPMENT_TRACKER_24.md)
- [0161 değişiklik](docs/0161/CHANGE_RECORD.md) · [Kanıt](docs/0161/TEST_EVIDENCE.md) · [Rollback](docs/rollback/README.md) · [R06 owner pin](contracts/OWNER_REVIEW_0161.json)
- [0161-A tarihsel inceleme deltası (0160 bazlı)](docs/0161A_REVIEW/README.md) · [Sürekli GitHub aktarım kararı](decisions/CEO/CEO_REPO_TRANSFER_20261114.md)
- [0162-A design review](docs/0162A/ARCHITECTURE_ADDENDUM.md) · [devir](docs/0162A/HANDOVER.md) · [field gap](docs/0162A/FIELD_GAP_0162.json) · [oracle](docs/0162A/ORACLE_MATRIX.json)
- [0162-B C kararı](decisions/CEO/CEO_WORK_MODE_20261114_C.md) · [kapsam](docs/0162B/SOURCE_SCOPE_PROPOSAL.json) · [yetki hazırlığı](security/evidence/AUTH_PREP_0162B.json) · [devir](docs/0162B/HANDOVER.md)

## 0163 / R9 — current isolated source candidate
- [R9 source manifest](product/SOURCE_MANIFEST.json) · [Bootstrap ADR](docs/0163/ADR_AGENT_BOOTSTRAP.md) · [H01 decision](decisions/CEO/CEO_BOOTSTRAP_0163.md) · [Scope policy](security/policy/BOOTSTRAP_0163.json)
- [Technical catalog delta](catalog/revisions/TECHNICAL_CATALOG_0163.md) · [GitHub readback](releases/GITHUB_READBACK_0163.json) · [Test evidence](tests/evidence/TEST_EVIDENCE_0163.json)

## 0164 / R10 quarantine candidate
[Architecture](docs/0164/ARCHITECTURE_ADDENDUM.md) · [Scope](security/policy/SCOPE_0164.json) · [Technical catalog](catalog/revisions/TECHNICAL_CATALOG_0164.md) · [Candidate source](quarantine/0164/) · [Test evidence](tests/evidence/TEST_EVIDENCE_0164.json).

## 0165 / R10 source integration
[Architecture](docs/0165/ARCHITECTURE_ADDENDUM.md) · [scope](security/policy/SCOPE_0165.json) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0165.md) · [test evidence](tests/evidence/TEST_EVIDENCE_0165.json).

## 0166 / R11 quarantine
[Architecture](docs/0166/ARCHITECTURE_ADDENDUM_0166.md) · [Acceptance](docs/0166/TRUST_AND_STAGING_ACCEPTANCE_0166.md) · [Parallel bindings](docs/0166/PARALLEL_BINDINGS_0166.md) · [Scope proposal](security/policy/INTEGRATION_SCOPE_PROPOSAL_0166.json) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0166.md).

## 0167 — R11 local MVP source
[Setup](docs/0167/LOCAL_MVP_SETUP.md) · [Architecture](docs/0167/ARCHITECTURE_ADDENDUM.md) · [Scope](security/policy/SCOPE_0167.json) · [Preflight](scripts/verify_product.py) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0167.md).

## 0172 — EDS
[Architecture](docs/0172/ARCHITECTURE_ADDENDUM.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0172.md) · [Progress](docs/0172/PROGRESS.json) · [Candidate](quarantine/0172/eds-shell.css).

## 0173
[Architecture](docs/0173/ARCHITECTURE_ADDENDUM.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0173.md) · [Plan](docs/0173/INTEGRATION_AND_TEST_PLAN.md) · [Progress](docs/0173/PROGRESS.json).

## 0174
[Standing development decision](decisions/CEO/CEO_0174_STANDING_DEVELOPMENT.md).


- [0177 integrated EDS candidate](docs/0177/ARCHITECTURE_AND_CATALOG.md) — isolated source, not product promotion.


- [0178 EDS candidate and preflight](docs/0178/ARCHITECTURE_AND_CATALOG.md)


- [0179 exact EDS PRE scope](docs/0179/INTEGRATION_PRE.md) — no promotion.


- [0180 EDS actual isolated product integration](docs/0180/ARCHITECTURE_AND_CATALOG.md)


## 0181 — D0 MVP diagnostics (2026-11-15)
Source `a31040d8116a58521393040061abe0078c83800d` / `recovery/0181-mvp-diagnostics`. 19 product source changes + manifest; 162 manifest entries, 163 files. Selected local synthetic tests 38/38 (24 Python, 14 Node including loopback GET 200). Full pinned dependency locks, full frontend build/browser and full backend suite NOT_RUN; independent acceptance HOLD. See docs/0181/ARCHITECTURE_AND_CATALOG.md and releases/GITHUB_READBACK_0181.json. Prior history preserved.


- [0182 workbench and browser tests](docs/0182/ARCHITECTURE_AND_CATALOG.md)

## 0183 — atomicity lab and lifecycle viewer
[Architecture](docs/0183/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0183.json) · [test evidence](releases/GITHUB_READBACK_0183.json).

## 0184 — D0 outbox review/readback
[Architecture](docs/0184/ARCHITECTURE_AND_CATALOG.md) · [R03 gaps](docs/0184/R03_MAPPING_GAPS.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0184.json) · [evidence](releases/GITHUB_READBACK_0184.json).

## 0185 — provider/admission/contracts
[Architecture](docs/0185/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0185.json) · [evidence](releases/GITHUB_READBACK_0185.json).

## 0186 — durable sample admission/settlement
[Architecture](docs/0186/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0186.json) · [evidence](releases/GITHUB_READBACK_0186.json).

## 0187 — Office Workbench projection
[Architecture](docs/0187/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0187.json) · [evidence](releases/GITHUB_READBACK_0187.json).

## 0188 — paired task-budget readback
[Architecture](docs/0188/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0188.json) · [evidence](releases/GITHUB_READBACK_0188.json).

## 0189 — integration and PG probe
[Architecture](docs/0189/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0189.json) · [evidence](releases/GITHUB_READBACK_0189.json).

## 0190 — T1 contention and R03
63 selected controls PASS, 14 PG checks NOT_RUN, canonical mapping HOLD. Product files unchanged. [Architecture](docs/0190/ARCHITECTURE_AND_CATALOG.md) · [R03](docs/0190/R03_T1_DECISION_PACKET.md) · [Evidence](releases/GITHUB_READBACK_0190.json).

## 0191 — logical T1 product core
[Architecture](docs/0191/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0191.json).

## 0192
[Core integration](docs/0192/ARCHITECTURE_AND_CATALOG.md).

## 0193
[Architecture](docs/0193/ARCHITECTURE_AND_CATALOG.md) · [Product roadmap](docs/implementation_plan/PRODUCT_ROADMAP_8_PHASES.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0193.json) · [Evidence](tests/evidence/TEST_EVIDENCE_0193.json). 25 selected synthetic tests PASS; PG and full product NOT_RUN.

## 0194 — D0 six-role transition mapping
[Architecture](docs/0194/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0194.json) · [Evidence](releases/GITHUB_READBACK_0194.json). 35 new + 25 regression tests PASS; real PG NOT_RUN, R03/IV HOLD.

## 0195 — D0 first claim and admission budget
[Architecture](docs/0195/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0195.json) · [Evidence](releases/GITHUB_READBACK_0195.json). 19 new + 60 regression PASS; real PG/R03/IV HOLD.

## 0196-L — D0 lease renewal and terminal settlement (separate workstream)
[Architecture](docs/0196L/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0196_L.json) · [Evidence](releases/GITHUB_READBACK_0196_L.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0196_L.json). 105 selected tests PASS; real PG/IV HOLD; 0196-MA not merged.

## 0198-E — pinned run history (separate workstream)
[Architecture](docs/0198E/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0198_E.json) · [Evidence](releases/GITHUB_READBACK_0198_E.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0198_E.json). 127 selected tests PASS, PG/IV HOLD.

## 0199-C — plan-wide causal history (separate workstream)
[Architecture](docs/0199C/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0199_C.json) · [Evidence](releases/GITHUB_READBACK_0199_C.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0199_C.json). 153 selected tests PASS, PG/IV HOLD.

## 0200-S — PostgreSQL consistent snapshot adapter (separate workstream)
[Architecture](docs/0200S/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0200_S.json) · [Evidence](releases/GITHUB_READBACK_0200_S.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0200_S.json). 164 selected PASS; 13 actual PG skipped; IV/R03 HOLD.

## 0201-R — retained history references (separate workstream)
[Architecture](docs/0201R/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0201_R.json) · [Evidence](releases/GITHUB_READBACK_0201_R.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0201_R.json). 14 new archive tests PASS; 5 integration and 13 PG NOT_RUN; prior 164 PASS not rerun. No independent acceptance.

## 0202-S — signed retained history (separate workstream)
[Architecture](docs/0202S/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0202_S.json) · [Evidence](releases/GITHUB_READBACK_0202_S.json) · [Parallel checkpoint](handover/PARALLEL_CHECKPOINT_0202_S.json). 39 selected PASS (25 new, 14 rerun); five prior integration and 13 actual PG NOT_RUN; IV/R03 HOLD.
