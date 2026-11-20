# AI Company OS — MI-01 / W8 553 kaynak pinleri bağımsız geri okuma

**Tarih:** 20.11.2026 · **kanıt türü:** gerçek GitHub kaynak ağacı / statik Git blob geri okuma. Bu bir W8 çalıştırma, fonksiyonel test, fresh build veya ürün kabulü **değildir**.

## Ne, neden, nerede, nasıl
- **Ne:** Kanonik `integration/product-dev@9a3571d6a06537ba718bafc45398c309bf3dc9b1` üzerine aktarılan W8 özgün U3 adaptörünün doğrudan ve tarihsel sabit kaynak pinlerini doğruladık.
- **Neden:** 505→553 ürün kaynak aktarımının ardından `tests/integration/w8_unified_u3.py` manifesti `27b4eb58...` olarak güncellendi. Birbirinden ayrı G2/G9/MI04 CI kanıtlarını W8 kabulü saymamak gerekir.
- **Nerede:** W8 adaptörü `tests/integration/w8_unified_u3.py` (Git blob `e1330a7c33f6c5d5c353a19b0be1ae1281fd0700`); P10J24 ve P10J23 yükleyicileri, U2 ve özgün U3 browser, SQL bağlantı yardımcıları, tarihsel 0207 dosyaları.
- **Nasıl:** GitHub recursive Git tree (SHA `9a3571d6a06537ba718bafc45398c309bf3dc9b1`), adaptörün literal pin sabitleri ve P10J24 tarihsel pinleri eşleştirilip tüm 16 yolun gözlemlenen Git blob SHA'sı birebir karşılaştırıldı; gerçek kaynak içeriklerine işleme yapılmadı.

## Doğrulanan kaynak ve bağımlılık kataloğu

| Kaynak | Beklenen Git blob | Git tree | Sonuç |
| --- | --- | --- | --- |
| `product/SOURCE_MANIFEST.json` | `27b4eb581626…` | `27b4eb581626…` | PASS |
| `tests/integration/w8_p10j24.py` | `0728ba08494b…` | `0728ba08494b…` | PASS |
| `tests/integration/w8_p10j23.py` | `7a386554e51c…` | `7a386554e51c…` | PASS |
| `tests/integration/run_unified_u2_session.py` | `c27eb541d4ad…` | `c27eb541d4ad…` | PASS |
| `tests/integration/browser_unified_u3.py` | `2a3f2b8e286c…` | `2a3f2b8e286c…` | PASS |
| `database/0192/candidate_event_outbox_fence.sql` | `6e4780bf9f26…` | `6e4780bf9f26…` | PASS |
| `database/0193/candidate_run_head.sql` | `180924e97ee1…` | `180924e97ee1…` | PASS |
| `database/0194/candidate_transition_roles.sql` | `7b5d374bb797…` | `7b5d374bb797…` | PASS |
| `database/0195/candidate_admission_budget.sql` | `d5dc6abc045d…` | `d5dc6abc045d…` | PASS |
| `database/0196L/candidate_lease_settlement.sql` | `e4c9a84ff705…` | `e4c9a84ff705…` | PASS |
| `database/0203T/terminal_command_anchors.sql` | `0b5f9725f402…` | `0b5f9725f402…` | PASS |
| `database/0204C/company_event_order.sql` | `edb2ef263204…` | `edb2ef263204…` | PASS |
| `database/migrations/0183_D0_PHYSICAL_CANDIDATE.sql` | `8e6b4a4e8864…` | `8e6b4a4e8864…` | PASS |
| `tests/integration/historical_0207/app/api/lifecycle_prefix_projection.py` | `b465e37d2959…` | `b465e37d2959…` | PASS |
| `tests/integration/historical_0207/app/core/agent_runtime/scheduler_review.py` | `719ce306304b…` | `719ce306304b…` | PASS |
| `tests/integration/historical_0207/app/core/transaction/postgres_admission_mapping.py` | `0a3ce6066225…` | `0a3ce6066225…` | PASS |

**Sonuç:** 16/16 **statik pin eşleşmesi** (13 doğrudan adaptör + 3 tarihsel kaynak). Ürün dosyaları 553, `SOURCE_MANIFEST.json` blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`. Kaynak uyuşmazlığı saptanmadı. Bu kontrol tamamlanmış eski W8 seçili kaynak audit'i veya CI koşumu için ikinci başarı kredisi oluşturmaz.

## Açık gerçek W8 engeli

`MI01-W8-C04` özgün `prepare` çalıştırması hâlâ **NOT_RUN**. `tests/integration/w8_unified.py` W8 hazırlığı sırasında `npm install --package-lock-only` ve `pip --isolated download` kullanır; eksiksiz `python.lock`, `locks/REVIEW.json`, wheel SHA/provenance ve temiz stage gerekiyor. `product-dev` ürün ağacında hazır `package-lock.json` yok; özgün lock ayrı ortak kaynak dokümantasyon ağacında `docs/ORG-07C-R8-INTEGRATION/original-lock/package-lock.json` olarak saklı. Doğrudan paket çözümlemesi veya yeni otomatik CI yetkisi varsayılmamalı. Geçerli 553 bağımlılık sahip incelemesi sonrası kontrollü `prepare → review → install → test → smoke` gerekir.

`C05` bağımlılık sahibi onayı **HOLD**. `C06/C07/C08` **NOT_RUN**; native U3 CDP ve gerçek browser doğrulanmış değil. Eski 539 CI testleri 553 için tam kabul değil. GATE-02 issuer/root/custody, PostgreSQL restore ve bağımsız IV tamamen ayrı açık.

## Mimari / güvenlik / ilerleme / devir

Ürün, API, veritabanı, sınıf, fonksiyon, semantik sözleşme, manifest, bağımlılık ve CI/workflow kodu **değiştirilmedi**. D-03/D-04 A mimari tercihi ve mevcut yürütme izni aynen. Operasyonel W8 eski kayıt **3/8** (bu turda yeni fonksiyonel kapı kapanmadı). Global geliştirme 15/35/20/20/10 ölçümü için ratifiye paydalar yok: **HESAPLANAMADI → HESAPLANAMADI**, delta hesaplanamaz. MVP **0/11**, bağımsız A-IV **0/8**, kabul artışı **0 yüzde puan**. Kanıt: yalnız statik GitHub Git blob karşılaştırması, 16/16 pin; gerçek W8 test **0**.

**Sonraki adım ve görev sınırı:** MI-01 Unified kaynak/bağımlılık sahibinin mevcut 553 tabanı için C04 fresh wheelhouse+fingerprint teslim etmesi; sahibin onayından önce C06–C08 yürütme yok. Bu sohbet MI-01 ürün kaynağına veya PR #4 workflow'üne yazıcı olarak girmedi. Geri dönüş: yalnız bu doküman commit'inin normal revert'i. `product-dev`, `main` ve eski test kanıtı korunur.

Makine-okunur özet (bu dosya içindeki metadata): `{"source":"9a3571d6a06537ba718bafc45398c309bf3dc9b1","adapter":"e1330a7c33f6c5d5c353a19b0be1ae1281fd0700","manifest":"27b4eb5816265d4e6e6d2458acb6220db7dd0c76","pin_count":16,"pins_pass":16,"real_w8":"NOT_RUN","acceptance_delta_pp":0}`.
