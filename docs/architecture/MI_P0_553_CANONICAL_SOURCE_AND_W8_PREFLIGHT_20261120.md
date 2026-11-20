# MI-P0 — 553 kaynaklı kanonik geliştirme durumu / W8 önkontrol eki
**Tarih:** 20.11.2026 | **Tür:** Mevcut Design Master'a bağlı kanıt eki | **Kabul:** Kaynak aktarımı PASS; W8 / güvenlik / MVP HOLD

Bu belge ana `DESIGN_MASTER.md` mimarisini, 8 fazlı uygulama planını veya seçilmiş D-03/D-04 A kararını değiştirmez. GitHub'da mevcut `integration/product-dev` başının gözlemini ve W8'in source/dependency sınırlarını günceller.

## Kanonik kaynak, kontrol edilen alt sistemler
- **Kaynak:** `integration/product-dev@9a3571d6a06537ba718bafc45398c309bf3dc9b1` (`PR #15`, development-source transfer).
- **Özgün ürün ağacı:** `f4cdcf68115917ab69ba6441414539fe32a59369` = ayrı ortak adayın son 553 ürün kaynağı; `product/SOURCE_MANIFEST.json` Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`, toplam **552 manifest kaydı + manifest dosyası**.
- **Yeni bağımsız Git readback:** recursive Git tree'de **552/552** manifest yolu var; eksik, fazla veya belirtilen byte uzunluğuyla uyumsuz dosya **0**. Bu SHA-256 üzerinden 552 dosyayı *yeniden* okuduğumuz anlamına gelmez; özgün 552/552 tam hash CI kanıtı önceki sahibi `44628704044` numaralı koşumda bulunur.
- **W8 zinciri:** `w8_unified_u3.py` → `w8_p10j24.py` ve `w8_p10j23.py` → ... → `w8_unified.py` referansları, sabit Git blob SHA'larıyla **23/23 statik uyumlu**. Ayrıca U2, U3 native browser ve 8 SQL yardımcı yolunu kapsayan `EXTRA` referansları **10/10** eşleşti. Güncel W8 adapter MANIFEST literal kimliği, 552 manifestin gerçek blob kimliğiyle birebir.
- **Lock/kurulum:** `product/ai-company-os-frontend` içinde `package.json` vardır; **`package-lock.json` kaynak ağacında yok**. W8 çalıştırıcısının `stage/frontend/package-lock.json` ve `locks/REVIEW.json`, Python wheelhouse ve fingerprint sahip onayı ihtiyacını *otomatik olarak* ortadan kaldırma. Burada lock üretimi veya paket kurulumu yapma; review zinciri onaylanmalı.

## Geliştirme hattı, API/DB/bağımlılık/sınıf etki sınırı
- **MI-01/Unified:** W8 adapter, tarihsel test zinciri ve lock review sahibi. Bu tur mevcut uygulama fonksiyonu, frontend bileşeni, event, API, SQL veya paket bağımlılığı değiştirilmedi; *yeni ürün test çalıştırılmadı*.
- **MI-02/03/04/G2/G9/ORG:** 553 kaynak üzerinde `durable_ops.py`, `assignment_lifecycle.py`, `intent_authority.py`, `operations.sql`, `assignment_review.sql` kaynakları mevcut; işleyen bağımsız root/issuer, gerçek PG RLS/fencing/restore kabulü henüz yok. 0214 özgün 10/10 CI PASS eski restore tekrar yürütme güvenlik bulgusunu **reproduce** ediyor; güvenlik PASS değildir.
- **MI-07/08/09 Model–Memory–Skill:** önceki 160/160 supplement ve 183/184+1 SKIP raporları orijinal strict 344/344 temiz kabulün yerini alamaz; eksik fullchain tekrar test edilmeli.
- **MI-10 QA/IV:** Mevcut PR #4 sadece izinli sınırlı D0 CI kanıtı taşır. Yeni broad CI/PROD izni yoktur.
- **Bağımlılıklar:** Next/React/Phaser ve Python `cryptography` kaynakta sürümlü tutulur; install/lock/wheelhouse bu tur çalıştırılmadı, yeni sürüm seçilmedi.

## Test, durum, bakım/rollback
| Kapı | Gerçek durum |
|---|---|
| Tam ürün kaynak yolu + byte uzunluğu | 552/552 PASS — GitHub statik doğrulama |
| W8 runner geçmişi/yardımcı pinleri | 23/23 ve 10/10 PASS — GitHub statik doğrulama |
| W8 exact `prepare/install/test/smoke` + native U3 | **NOT_RUN** — kilit ve yürütme ortamı gerekir |
| MI-04 özgün 0214 10 test | **10/10 PASS D0** ([CI](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44695937454)), old restore replay residual **OPEN** |
| Özgün G2 50 + G9 7 (sabit owner kaynak) | **50/50 + 7/7 PASS D0** ([CI](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44697437051)); kanonik 553 owner varyant entegrasyonu HOLD |
| Gerçek PG/RLS/restore, bağımsız A-AT 8 | **HOLD/NOT_RUN**, gerçek grants/COMMIT yok |

Değişiklik kapsamı bu doküman ve `handover` / `catalog` göstergeleridir; **ürün kaynak dosyaları değişmez**. Arıza: W8 başarısızsa ilk önce frozen source SHA + manifest, W8 ancestor blob + AUX ve `locks/REVIEW.json` SHA/fingerprint karşılaştır; yanlış onay, silent pass veya eski run'a yeni kredi verme. Güvenlikte replay residual çözülmeden gerçek işlem açılmaz.

**Rollback:** Doküman değişikliğini normal revert; 553 ürün kaynak commit'i `9a3571d6a...` kalır. Daha geriye dönüş için önceki kaynak commit `8a3b05a...` ve PR #15 normal revert süreci ayrıca korunur. Force push, grant/claim reset ve main mutasyonu yoktur.

**Kanonik teknik kanıt:** [MI_P0_553_W8_STATIC_PREFLIGHT_20261120.json](../../catalog/revisions/MI_P0_553_W8_STATIC_PREFLIGHT_20261120.json). **Sonraki görev:** Mevcut MI-01 sahibinin exact 553 dependency lock review + W8 fresh fullchain koşumu; ardından G2/G9 owner ve PostgreSQL/IV kapıları. Genel ağırlıklı geliştirme yüzde paydası owner-ratified değil, **HESAPLANAMADI**; Core 12/16, UI 21/40, MVP 0/11, IV 0/7 olduğu gibi korunur.
