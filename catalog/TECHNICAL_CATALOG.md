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
