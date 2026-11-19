# MI-PROGRESS-02 — mimari kapsam, kriter tabanı ve devir

2026-11-19 — reporting-only. User-directed centralized progress work; no product/authority changes. Parent 382d769eccf30615957554668d84d7b9e8d96cd8; common candidate bf87d5c48c7fee97fe12d0a28df3be80249f7306; product-dev 8a3b05aadd32b214f3f8988fc9c793f853fbe3d0.

## Ne / neden / nerede / nasıl
- Exact v135 and DOC-REV-0155 names and order (63/63), 21 domain and 24 TRACK-0227 areas retained. Original workstream names retained. Proposed P01–P10 ownership is a reporting attribution, not actual task/permission reassignment. Cross-domain tracker references preserved.
- progress/MI_PROGRESS_02_SCOPE_AND_CRITERIA.json: unique module ID, original source anchor, single proposed scoring group, concrete target and failure condition, five proposed stage slots per module. These 315 slots are not yet exhaustive or frozen. 24 technical rows are coverage review, not independently scored duplicates. Crosscutting coverage must be reviewed, including EDS, API schema, build/CI, observability and recovery; preserve business module scope.
- docs/master-integration/MI-PROGRESS-02/CATALOG_AND_EVIDENCE.json: exact inputs, structural checks and evidence boundary. No product source/class/function/API/DB/event/dependency delta. Existing acceptance and owner percentages unchanged.
- Update existing central current/partial/weight files only; historical records and product branches remain intact.

## Proposed allocation
| Group | Weight | Modules | Proposed slots |
|---|---:|---:|---:|
| P01 Frontend ve UI | 12% | 1 | 5 |
| P02 Sanal ofis | 8% | 2 | 10 |
| P03 Backend ve API | 10% | 2 | 10 |
| P04 Orchestrator ve Task Engine | 12% | 3 | 15 |
| P05 Agent Runtime ve Organizasyon | 12% | 8 | 40 |
| P06 Model, Skill ve Memory | 12% | 8 | 40 |
| P07 Database ve Event Store | 8% | 5 | 25 |
| P08 Güvenlik ve Independent Verifier | 10% | 15 | 75 |
| P09 SaaS ve finans | 6% | 11 | 55 |
| P10 Test, DevOps ve entegrasyon | 10% | 8 | 40 |

## Measurement and proof
For frozen groups: 15/35/20/20/10, completed/total per stage. General weighted score only after all scopes, nonoverlapping criteria, denominators and group weights are frozen. Null = unknown/not reviewed, not zero. Existing 24 area ordinal rubric and canonical gates are separate. A source pin proves presence not execution. Replayed tests do not increase unique test counts. Product acceptance and authority remain separately guarded.

## Maintenance / fault diagnosis / rollback
Before edit, read current governance head, standard and owner records. Inspect every changed path and preserve prior owner deltas. On duplicate ID, missing group, invalid weights, unknown stage, ambiguous scope, stale/missing evidence, or a disputed criterion: block scoring, retain previous approved denominator, record issue and owner. For scope change, version the matrix and preserve both old and new denominators plus rationale. Revert this reporting commit only if needed after reviewing current head; never revert unrelated security or product changes. No CI/main/PROD/independent acceptance change.

## Next
MI-PROGRESS-02-R1: owner review 63 module and 24 crosscut scope; first freeze P04/P05/P07/P08 criteria against exact existing Core/D5 proof (without treating fixture as canonical acceptance), then P01/P02/P03/P06/P09/P10. Keep existing MI01–10 queue running and preserve Windows deferral. No new product tests in this round. 8 structural data checks only.
