# 0162-C teknik katalog deltası

Karantina kaynakları; R8 üzerine uygulanmadı.

| CHG | Dosya | Hat / domain | Ne / neden | Teşhis |
|---|---|---|---|---|
| CHG-0162C-01 | `reconciliation_review.py` | W4 / D15,D16,D21 | Outbox/fence/makbuz kimliği ve epoch ayrımı, UNKNOWN/CONFLICT karantina | Correlation, effect/idempotency, epoch ve receipt farkını incele; sağlayıcıya yeniden gönderme yok |
| CHG-0162C-02 | `terminal_review.py` | W3/W4 / D07,D15,D16 | Terminal CAS, sekiz rol, mutation digest, admission/lease bağlama; stop ayrı HOLD | CAS, lease, mutation ve rol kimliklerini sırasıyla incele; fiziksel T1 ve kontrol düzlemi açık |
| CHG-0162C-03 | `settlement_review.py` | W7 / D17,D15,D07 | Company-period head, reservation ve economic event ayrı, maliyet belirsizliğinde exposure | Period, currency, outcome, duplicate ve CAS kontrolü; hiçbir posting/FX yok |
| CHG-0162C-04 | `test_review_0162.py` | W8 / D11,D18 | Sentetik olumlu şekil ve negatif oracle kaynakları; hiçbir test çalışmadı | Yetkili test ortamı ve scope olmadan import/collect yok |
| CHG-0162C-05 | `AgentDetail.tsx` | W1 / D13,D05 | Rol/istasyon detayı; gerçek instance/grant/kanıt yok | Eksik rol durumunda boş görünüm; gerçek ajan oluşturma yok |
| CHG-0162C-06 | `OfficePanel.tsx` | W1 / D13 | Controlled kat/görünüm; statik SVG, bağımsız geometri, JOIN_HOLD | Layout revision uyuşmazlığında join yok; geometri preview yerel seçimi gerçek ajan değil |
| CHG-0162C-07 | `OperationPanel.tsx` | W1 / D13 | Controlled salt-okunur panel, gerçek aktivite/onay yok | Panel owner Dashboard; hiçbir gerçek onay işlemi yok |
| CHG-0162C-08 | `Dashboard.tsx` | W1 / D13 | Tek seçim ve panel sahibi; mevcut navigation, statik fixture, reset ve ayrıştırılmış paneller | Kat/view/layout reset; statik fallback; eski Dashboard blob ile geri dön |

## Sembol, satır ve bağımlılık

### product/ai-company-os-backend/app/core/event_store/reconciliation_review.py
SHA-256 `12c79ac6b742cf1d9c76f1352a114d84c42bd2502a186c90790b06e56e97d6f9`; 73 satır.

Bağımlılık: outbox_review.py, fence_review.py, lifecycle.py, transaction/review.py.

- `Outcome` — class, L9
- `ReconciliationPin` — class, L16
- `ReconciliationReview` — class, L37
- `valid_pin` — function, L48
- `inspect_reconciliation` — function, L56

### product/ai-company-os-backend/app/core/transaction/terminal_review.py
SHA-256 `f24f72264d6898b04b0ec48dd887a9fc2f99da749abcac9463943315199ad191`; 140 satır.

Bağımlılık: lifecycle.py, transaction/review.py, readback_review.py.

- `TerminalPin` — class, L9
- `MutationBinding` — class, L31
- `TerminalReview` — class, L44
- `inspect_pre_admission_stop` — function, L56
- `inspect_terminal` — function, L65

### product/ai-company-os-backend/app/engines/budget_engine/settlement_review.py
SHA-256 `17ea4c7251b11b813251bc20307127cc75d124e42a192701cbf73347153e2913`; 104 satır.

Bağımlılık: reconciliation_review.py, lifecycle.py, transaction/review.py.

- `CompanyBudgetHead` — class, L8
- `ReservationPin` — class, L24
- `SettlementPin` — class, L38
- `SettlementReview` — class, L49
- `currency_ok` — function, L59
- `valid_head` — function, L63
- `valid_reservation` — function, L69
- `inspect_settlement` — function, L74

### product/ai-company-os-backend/tests/test_review_0162.py
SHA-256 `1bcde627ed2c56c41c6173b8ecd2011a1a8682f88d80aee8c85902f8ff50a883`; 93 satır.

Bağımlılık: Python unittest, dataclasses; 3 aday modül, R8 temel tipleri.

- `terminal_args` — function, L16
- `rec_args` — function, L28
- `budget_args` — function, L34
- `TerminalCandidates` — class, L41
- `ReconciliationCandidates` — class, L63
- `SettlementCandidates` — class, L77
- `test_shape_never_commits` — function, L42
- `test_reopen_denied` — function, L44
- `test_receipt_missing` — function, L46
- `test_unknown_success` — function, L48
- `test_expired_worker` — function, L50
- `test_pre_admission_stop` — function, L52
- `test_outbox_mismatch` — function, L54
- `test_postcommit_version` — function, L56
- `test_mutation_digest_mismatch` — function, L58
- `test_control_plane_stop_separate` — function, L60
- `test_applied_claim` — function, L64
- `test_not_applied_claim` — function, L66
- `test_correlation_mismatch` — function, L68
- `test_conflicting_receipt` — function, L70
- `test_restore_epoch` — function, L72
- `test_unknown` — function, L74
- `test_shape_never_posts` — function, L78
- `test_duplicate` — function, L80
- `test_event_conflict` — function, L82
- `test_unknown` — function, L84
- `test_overage` — function, L86
- `test_currency` — function, L88
- `test_cas` — function, L90
- `test_outcome_scope_conflict` — function, L92

### product/ai-company-os-frontend/components/dashboard/AgentDetail.tsx
SHA-256 `9d870a49384e0618cd4f5a80384489321f87760bef5cc73c95bcef68ca392956`; 10 satır.

Bağımlılık: R8 uiCatalog.json.

- `RoleButton` — function, L4
- `AgentDetail` — function, L7

### product/ai-company-os-frontend/components/dashboard/OfficePanel.tsx
SHA-256 `97eab6148e944ebdf877c39c5ba0ac5b804a1adcd742a0aa6c3fa0fdd0bf4d36`; 19 satır.

Bağımlılık: R8 OfficeScene, geometry, snapshot fixture, Next Link.

- `OfficePanel` — function, L10

### product/ai-company-os-frontend/components/dashboard/OperationPanel.tsx
SHA-256 `10707538997f9022444d62e431d242440592e835c889b55cdbe5762ad0a9eb02`; 7 satır.

Bağımlılık: React type ReactNode.

- `OperationPanel` — function, L5

### product/ai-company-os-frontend/features/ceo-dashboard/Dashboard.tsx
SHA-256 `79b155362d51818e19a3139b190399f72473d8ca16633c26594b705e0108cb3d`; 56 satır.

Bağımlılık: R8 CorePreview, geometry, fixtures, SnapshotStrip, MetricsStrip; 3 aday panel.

- `Dashboard` — function, L23
- `DashboardView` — function, L26
- `resetContext` — function, L39
- `changeFloor` — function, L40
- `changeDisplay` — function, L41
- `navigate` — function, L42
- `openStation` — function, L43
- `openRole` — function, L44
- `changeDetail` — function, L45
- `stationList` — function, L46
