# 0161 — R8 kaynak adayı
8 Python dosyası: admission/budget/readback, IV receipt, projection freshness, finance projection ve test. [Detay](docs/0161/CHANGE_RECORD.md).

# Değişiklik geçmişi
## 0160
16 Python core modülü, API ve 5 frontend modülü yeni kanonik dizinlere; 2 Dashboard bileşeni ayrıldı. Uyumluluk facade, manifest 114 kayıt, katalog v1.19. Statik kanıt; gerçek TEST NOT_RUN.
## 0159-B
Model, skill, memory kaynak adayları; katalog v1.18. Bkz. docs/0159B/CHANGE_RECORD.md.
## 0159-A / 0158
Eklemeli repo düzeni ve R5 kaynakları; tarihsel kayıtlar docs/0159A ve docs/0158.

## 0222
Shared CEO/Office historical snapshot, finite SSE replay, bounded loopback proxy, common provider and source/mirror schema. 39 selected behaviors. Actual DB/browser/PG/build not run. [Details](docs/0222/ARCHITECTURE_AND_CATALOG.md).

## 0223
Agent and Workflow Studio fixed compiler read, shared separate historical context, role/task lineage HOLD, 63 selected checks, actual DB/browser/PG/build open. [Details](docs/0223/ARCHITECTURE_AND_CATALOG.md).


## 0224
Canonical Research root roster/company and result readback candidate; four new product files, two replacements including manifest. 43 selected passes, eight full integration cases NOT_RUN. No new authority or schema.


## 0225 — actual integration validation
Four scoped integration suites PASS (32 new +102 prior, 134 unique). Actual SQLite T1 and pinned admission/history, persisted historical DB and mounted routes, real loopback compiled TS proxy/Studio. No runtime source changes; original suites and full result path still open. 7/16 gates unchanged. See docs/0225/ARCHITECTURE_AND_CATALOG.md and handover/NEXT_STEP_0225.md.


## 0226 — recovered original regression
173 recovered original tests +134 prior selected reruns =307 unique selected tests (254 Python, 53 Node). Original SQL6 and DB4 PASS; original core29 current source PASS nonlocked, historical locked acceptance NOT_RUN. No product changes. 7/16 gates unchanged. See docs/0226/ARCHITECTURE_AND_CATALOG.md and docs/0226/LOCAL_ACCEPTANCE_RUNBOOK.md.
