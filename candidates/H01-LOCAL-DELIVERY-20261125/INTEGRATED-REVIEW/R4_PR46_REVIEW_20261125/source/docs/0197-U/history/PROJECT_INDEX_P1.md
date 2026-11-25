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

## 0187-W1-I — 0187 + W1 joint source
32 UI paths (30 exact, two reconciled), 239 product files, 238 manifest path/size matches, 69 historical UI blobs retained. 9 shared schemas and 4 fixtures match. 66 selected Node/mock tests and 2 merged TSX syntax checks PASS; no full checkout/build/browser/backend or independent acceptance. [Scope](docs/0187-W1-I/SCOPE.json) · [Acceptance runbook](docs/0187-W1-I/ACCEPTANCE_RUNBOOK.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0187_W1_I.json) · [Readback](releases/GITHUB_READBACK_0187_W1_I.json).

## 0188 — paired task-budget readback
[Architecture](docs/0188/ARCHITECTURE_AND_CATALOG.md) · [catalog](catalog/revisions/TECHNICAL_CATALOG_0188.json) · [evidence](releases/GITHUB_READBACK_0188.json).

## 0188-W8 — combined source and local execution tooling
[Architecture](docs/0188-W8/ARCHITECTURE_AND_CATALOG.md) · [Build runbook](docs/0188-W8/LOCAL_BUILD_RUNBOOK.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0188_W8.json) · [Readback](releases/GITHUB_READBACK_0188_W8.json) · [Tests](tests/evidence/TEST_EVIDENCE_0188_W8.json). 17 exact 0188 paths, 250 product files, 249 manifest path/size matches; 13 Node +8 runner checks PASS. Full install/build/runtime NOT_RUN, independent HOLD.
 
## 0188-W8-S1
[Security candidate architecture](docs/0188-W8-S1/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0188_W8_S1.json) · [Readback](releases/GITHUB_READBACK_0188_W8_S1.json). Prior Windows lock rejected; new pins and 9 runner tests, full build open.

## 0188-W8-S2
[Architecture](docs/0188-W8-S2/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0188_W8_S2.json) · [Readback](releases/GITHUB_READBACK_0188_W8_S2.json)

## 0188-W8-S3
[Architecture](docs/0188-W8-S3/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0188_W8_S3.json) · [Readback](releases/GITHUB_READBACK_0188_W8_S3.json)

## 0188-W8-P1
[Architecture](docs/0188-W8-P1/ARCHITECTURE_AND_CATALOG.md) · [Catalog](catalog/revisions/TECHNICAL_CATALOG_0188_W8_P1.json) · [Readback](releases/GITHUB_READBACK_0188_W8_P1.json)
