# Teknik katalog v1.20 — 0161
122 kaynak kaydı; [yol eşlemesi](RELOCATION_MAP_0160.json), [dosya](FILE_CATALOG.json), [modül](MODULE_CATALOG.json), [sınıf](CLASS_CATALOG.json), [fonksiyon](FUNCTION_CATALOG.json), [bağımlılık](DEPENDENCY_CATALOG.json), [frontend](FRONTEND_CATALOG.json), [API](API_CATALOG.json), [DB](DATABASE_CATALOG.json), [olay](EVENT_CATALOG.json), [hata](ERROR_CATALOG.json), [güvenlik](SECURITY_CATALOG.json), [test](TEST_CATALOG.json), [izlenebilirlik](TRACEABILITY_MATRIX.json). Python katalogları taşınan sembolleri kanonik yola bağlar, facade importları ayrıca görünür. Test ve hata kayıtları statik aday. Geçmiş v1.18 parent ve 0158 kayıtları korunur.

0161 ekleri: [değişiklik](../docs/0161/CHANGE_RECORD.md), [kanıt](../docs/0161/TEST_EVIDENCE.md), [owner pin](../contracts/OWNER_REVIEW_0161.json). R11 budget ve finance projection, R03 admission readback, R07 IV receipt ve R04 freshness adayları; no IO/authority.

[0162-A inceleme deltası](revisions/TECHNICAL_REVIEW_0162A.json) — v1.21-A aday inceleme; v1.20 kaynak kataloğu ve 122 kaynak kaydı değişmedi.

0162-B: [önerilen dosya kapsamı](../docs/0162B/SOURCE_SCOPE_PROPOSAL.json) · [uygulama sözleşmesi](../docs/0162B/IMPLEMENTATION_CONTRACT.md). Source catalogue v1.20 and review v1.21-A unchanged; proposed paths not actual modules.


## 0162-D static review
[12 open findings](revisions/TECHNICAL_REVIEW_0162D.json) · [55 OfficeV0 crosswalk](../docs/0162D/OFFICE_FIELD_CROSSWALK_55.json) · [20 backend crosswalk](../docs/0162D/BACKEND_CROSSWALK_20.json). No product or API/DB/dependency changes.


## 0163 R9 source candidate
[File/symbol/dependency/test delta](revisions/TECHNICAL_CATALOG_0163.json). Four TSX, no API/DB/event/dependency version change. [Maintenance](../docs/0163/MAINTENANCE_ROLLBACK.md).

[0163 ayrıntılı MD katalog](revisions/TECHNICAL_CATALOG_0163.md)

[0164 source candidate catalog](revisions/TECHNICAL_CATALOG_0164.md) · [JSON](revisions/TECHNICAL_CATALOG_0164.json).

[0165 technical delta MD](revisions/TECHNICAL_CATALOG_0165.md) · [JSON](revisions/TECHNICAL_CATALOG_0165.json).

[0166 technical delta](revisions/TECHNICAL_CATALOG_0166.md) · [JSON](revisions/TECHNICAL_CATALOG_0166.json).

[0167 source and setup delta](revisions/TECHNICAL_CATALOG_0167.md) · [JSON](revisions/TECHNICAL_CATALOG_0167.json).

## 0168 review
[Source/readback review and local candidate inventory](../docs/0168/LOCAL_MVP_PARALLEL.md). No product source, canonical API, DB or dependency changes. Local candidate delta delivered separately.

## 0169
Standalone `scripts/verify_source_zip.py` (git_blob, safe_path, verify_zip, main; Python stdlib) and `tests/test_verify_source_zip.py` (10 helper fixture checks). No product API/DB/events/dependency changes. [Evidence and rollback](../docs/0169/PHASE01_PREFLIGHT.md).

## 0170
`audit_local_dependencies.py`: read_safe, unique, parse_requirements, parse_package, installed_python, installed_node, rows, optional_lock, audit, main; Python stdlib only. `test_audit_local_dependencies.py`: 14 synthetic checks. No product API/DB/events/dependency version change. [Evidence and rollback](../docs/0170/PHASE01_DEPENDENCY_AUDIT.md).

## 0183
[File/symbol/API/DB/dependency/test delta](revisions/TECHNICAL_CATALOG_0183.json) · [Maintenance](../docs/0183/ARCHITECTURE_AND_CATALOG.md). 173 manifest entries; separate SQLite lab, unexecuted SQL design, manual synthetic lifecycle view.

## 0184
[Source/API/DB/symbol/test catalog](revisions/TECHNICAL_CATALOG_0184.json) · [Maintenance](../docs/0184/ARCHITECTURE_AND_CATALOG.md). 182 product manifest entries. Synthetic local claim, UNKNOWN/READBACK_HOLD, fixed loopback GET; no external effect.

## 0185
[Source/class/function/API/DB/test catalog](revisions/TECHNICAL_CATALOG_0185.json) · [Maintenance](../docs/0185/ARCHITECTURE_AND_CATALOG.md). 191 product manifest entries. Typed provider DENY, admission bundle HOLD, shared Outbox schema/pins.

## 0186
[Source/class/function/API/DB/event/test catalog](revisions/TECHNICAL_CATALOG_0186.json) · [Maintenance](../docs/0186/ARCHITECTURE_AND_CATALOG.md). 201 manifest entries; isolated sample admission/budget/settlement, read-only projection.

## 0187
[Source/symbol/API/DB/event/test catalog](revisions/TECHNICAL_CATALOG_0187.json) · [Maintenance](../docs/0187/ARCHITECTURE_AND_CATALOG.md). 212 product manifest entries; actual synthetic Workbench history and Office role readback.

## 0188
[Source/symbol/API/DB/event/test catalog](revisions/TECHNICAL_CATALOG_0188.json) · [Maintenance](../docs/0188/ARCHITECTURE_AND_CATALOG.md). 223 manifest entries; paired D0 sample readback, actual writer NOT_RUN.

## 0189
[Infrastructure and test catalog](revisions/TECHNICAL_CATALOG_0189.json) · [Maintenance](../docs/0189/ARCHITECTURE_AND_CATALOG.md). Four new test infrastructure files; no product file changes.

## 0190 — T1 contention and R03
63 selected controls PASS, 14 PG checks NOT_RUN, canonical mapping HOLD. Product files unchanged. [Catalog](revisions/TECHNICAL_CATALOG_0190.json).

## 0193
[Source/symbol/DB/error/test delta](revisions/TECHNICAL_CATALOG_0193.json) · [Maintenance and rollback](../docs/0193/ARCHITECTURE_AND_CATALOG.md). 25 selected synthetic tests; no API/dependency change or actual migration.

## 0201-R — retained history
[Machine-readable delta](revisions/TECHNICAL_CATALOG_0201_R.json) · [Architecture, maintenance, rollback](../docs/0201R/ARCHITECTURE_AND_CATALOG.md). New reference module, two test files; 14 archive tests PASS, 5 integration tests NOT_RUN. No API/canonical DB/event schema change.

## 0202-S — signed history
[Machine-readable delta](revisions/TECHNICAL_CATALOG_0202_S.json) · [Architecture and rollback](../docs/0202S/ARCHITECTURE_AND_CATALOG.md). 25 new tests (6 underlying snapshot mock), 14 archive regression PASS. Optional cryptography pin; no base dependency or canonical schema change.

## 0203-T — terminal anchor
[Delta](revisions/TECHNICAL_CATALOG_0203_T.json) · [Maintenance](../docs/0203T/ARCHITECTURE_AND_CATALOG.md). Three modified product modules, three added product files, one root DDL. 54 selected tests PASS; 7+5 integration NOT_RUN.

## 0204-C — company coordination
[Delta](revisions/TECHNICAL_CATALOG_0204_C.json) · [Maintenance](../docs/0204C/ARCHITECTURE_AND_CATALOG.md). Two added product files, one root DDL; no old source changes.

## 0205-R — company recovery
[Delta](revisions/TECHNICAL_CATALOG_0205_R.json) · [Maintenance](../docs/0205R/ARCHITECTURE_AND_CATALOG.md). Two new product files, no prior source replacement or canonical migration.


## 0206
[Exact source delta, symbols, API/DB/event/dependencies and test boundaries](revisions/TECHNICAL_CATALOG_0206.json) · [Architecture/maintenance/rollback](../docs/0206/ARCHITECTURE_AND_CATALOG.md).

## 0207 — cross-boundary evidence
[Source/test delta](revisions/TECHNICAL_CATALOG_0207.json) · [Architecture and maintenance](../docs/0207/ARCHITECTURE_AND_CATALOG.md). 72 selected PASS, 29 core/lifecycle NOT_RUN, D-01 open.

## 0208 — Joint Runtime Context
[Source/symbol/test delta](revisions/TECHNICAL_CATALOG_0208.json) · [Architecture and rollback](../docs/0208/ARCHITECTURE_AND_CATALOG.md). 98 selected PASS; D-01 D0 joint inspection, D-02 restore gap open.

## 0209 — witnessed Runtime / original ordinary T1
[Source/symbol/test delta](revisions/TECHNICAL_CATALOG_0209.json) · [Architecture and rollback](../docs/0209/ARCHITECTURE_AND_CATALOG.md). 138 selected PASS; D-03 open.

## 0210 — local fenced T1 and intent journal
[Source/symbol/test delta](revisions/TECHNICAL_CATALOG_0210.json) · [Architecture and rollback](../docs/0210/ARCHITECTURE_AND_CATALOG.md). 154 selected PASS; D-03 external and D-04 open.

## UI-P10B
[UI catalog delta](revisions/TECHNICAL_CATALOG_UI_P10B.json) · [Maintenance](../docs/UI-P10B/ARCHITECTURE_AND_CATALOG.md).

## UI-P10C
[Catalog delta](revisions/TECHNICAL_CATALOG_UI_P10C.json) · [Maintenance](../docs/UI-P10C/ARCHITECTURE_AND_CATALOG.md).

## UI-P10D
[Architecture and limits](../docs/UI-P10D/ARCHITECTURE_AND_CATALOG.md) · 21/40 gates, isolated 5/7, full product 0/7. Core 0211 separate.

## UI-P10E — 0211 + UI D0 source union candidate
[Source/symbol/test delta](revisions/TECHNICAL_CATALOG_UI_P10E.json) · [Maintenance and rollback](../docs/UI-P10E/ARCHITECTURE_AND_CATALOG.md).


## UI-P10F
See [revision catalog](revisions/TECHNICAL_CATALOG_UI_P10F.json) and [architecture](../docs/UI-P10F/ARCHITECTURE_AND_CATALOG.md). Exact source 5b57199c397fa6ae183ec16c9efaa480dfc78175; no API/schema/dependency upgrades. D0 only.


## UI-P10G
[Catalog](revisions/TECHNICAL_CATALOG_UI_P10G.json); [architecture](../docs/UI-P10G/ARCHITECTURE_AND_CATALOG.md). D0 only.


## UI-P10H
[Catalog](revisions/TECHNICAL_CATALOG_UI_P10H.json); [architecture](../docs/UI-P10H/ARCHITECTURE_AND_CATALOG.md). D0 only.


## UI-P10I
[Catalog](revisions/TECHNICAL_CATALOG_UI_P10I.json); [architecture](../docs/UI-P10I/ARCHITECTURE_AND_CATALOG.md). D0 only.

## UI-P10J-03 / 04
[Product source delta](revisions/TECHNICAL_CATALOG_UI_P10J.json) · [Parallel and W8 delta](revisions/TECHNICAL_CATALOG_UI_P10J04.json) · [Architecture and maintenance](../docs/UI-P10J/P10J04_ARCHITECTURE.md). Standalone tests only; product manifest unchanged in P10J-04.

## UI-P10J-05
[Source/symbol delta](revisions/TECHNICAL_CATALOG_UI_P10J05.json) · [Architecture and rollback](../docs/UI-P10J/P10J05_ARCHITECTURE.md). D0 graph and historical presentation; no API/DB change.

## UI-P10J-07
[Verified symbols and overlap](revisions/TECHNICAL_CATALOG_UI_P10J07.json). No API/DB/source change.

## UI-P10J-08
[Windows portability delta](revisions/TECHNICAL_CATALOG_UI_P10J08.json).

## UI-P10J-08 — local Windows W8 PASS
Exact source 752b225deac4557a548faec7191a090fbfba19f7; see docs/UI-P10J/P10J08_W8_WINDOWS_ACCEPTANCE.md and tests/evidence/TEST_EVIDENCE_UI_P10J08_W8_PASS.json. Independent and 0222 union acceptance remain HOLD.

## UI-P10J-09 — verified delivery and real UI review
See docs/UI-P10J/P10J09_REAL_UI_REVIEW.md, tests/evidence/TEST_EVIDENCE_UI_P10J09.json, catalog/revisions/TECHNICAL_CATALOG_UI_P10J09.json and progress/UI_P10J09.json. No product changes; next mobile shell and controlled core reconciliation.


## UI-P10J-10
[Delta](revisions/TECHNICAL_CATALOG_UI_P10J10.json) · [Maintenance](../docs/UI-P10J/P10J10_ARCHITECTURE.md). Mobile disclosure candidate; no API/DB/dependency changes.
