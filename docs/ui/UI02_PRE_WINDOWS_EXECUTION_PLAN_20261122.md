# AI Company OS — UI-02 ve Windows öncesi uygulama/entegrasyon planı
**Görev zinciri:** MI05-UI02-PREWINDOWS-20261122 · MI05-UI02A-CEO-D0-EVIDENCE-PROVENANCE-20261122
**Tarih:** 2026-11-22
**Durum:** İzole kaynak adayı; mevcut kodda değişiklik, 19/19 seçili/sentetik PASS; kaynak sahibi incelemesi ve tam build HOLD.

## 1. Kaynak ve değişiklik sınırı
- Kanonik ve tek ebeveyn tabanı: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` — 552 manifest girdisi / 553 ürün dosyası; manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`.
- UI-01B birleşimi PR39 HEAD `8e614ec744b59bb1c3cb6c1166f59c3a6eb4941e` ve UI-01D kilit birlikte aday PR40 HEAD `1a75ea2cd287f8fbeab01f4ce5fd89c4197ba2c9` değişmeden kalır. PR40 lock ve 555 manifest bu UI-02 dalının ebeveyni DEĞİLDİR; entegrasyonda üç-yollu kaynak/manifest incelemesi gerekir.
- Açık PR yol taraması: PR2 ve PR3, `Dashboard.tsx` ile `MetricsStrip.tsx` dosyalarına dokunduğundan bu dosyalar HOLD; `OperationalReadback.tsx`, `OperationalReadback.module.css` için 29 açık PR'da doğrudan yazma çakışması görülmedi. Yeni yazma sahipliği MI-05 kaynak sahibi gözden geçirmesine bağlıdır; merkezî kuyruk bu kendiliğinden kapanmaz.
- Kod değişimi yalnız mevcut CEO bileşeni + CSS; yeni test bir dosya. Backend, API endpoint, DB, event, IAM/ORG/T1, auth, gateway, W8 runner, CI, ücretli servis, gerçek veri ya da yeni frontend uygulaması YOK.

## 2. Sıralı Windows öncesi çalışma paketleri

| ID | Öncelik / Sahip | Çalışma kapsamı ve kod/sözleşme | Kontrol ve kapı |
|---|---|---|---|
| UI-01D-OWNER | P0 / MI-05, MI-01 | PR39 + PR40 exact diff/lock ile manifest/bağımlılık sahibi incelemesi; hiçbiri oto-onay değildir | HEAD, lock SHA, source path; owner HOLD |
| UI-02A | P0 / MI-05 | Var olan CEO OperationalReadback'in gerçek kaynak okunabilirliğini ve tarihsel D0/HOLD ayrımını iyileştir; hardcoded event denominator kaldır | Özgün `ui-p10j17-ceo.test.cjs` + yeni negatif test; salt-okunur |
| UI-02B | P1 / MI-05 | Mevcut MetricCards / MetricsStrip'ın statik fixture metrik etiketlerini kaynak/kapsamla gözden geçir, gerçek canlı değerleri ancak onaylı projection varsa bağla | PR2/3 Dashboard/MetricsStrip çakışması HOLD; eski UI testleri |
| UI-02C | P1 / MI-05 + Core | Var olan ProjectStudio ve plan projection'tan H01 için salt-okunur proje/görev özeti; cross-read eşleştirme yok | task/run/project kimliği, tenant scope, HOLD |
| UI-02D | P1 / MI-05 + MI-06 | AgentDirectory gerçek IAM/ORG doğrulanmadıkça rol şablonunu aktif çalışan gösterme; ofis istasyonu ile role template'i ayrı tut | IAM grant/provenance kapısı, eski P10J18 regression |
| UI-02E | P1 / MI-05 + Güvenlik/IV | Karar kutusu, güvenlik, denetim kaynaklarını CEO panelinden mevcut rotalar ile göster; bağımsız kabul olmadan onay eylemi yok | güvenlik/IV sahipliği ve P02 fail-closed |
| UI-02F | P1 / MI-05 + MI-06 | Existing /office, SharedSnapshotProvider, WorkflowDraft ve PlanGraph navigation/projection salt-okunur bağları; örnek oturum eşlemelerini sahte canlı duruma yükseltme | Office/Project/Workflow, snapshot TTL, stale & auth negatif |
| MI05-CROSS-TEST | P0 / MI-05, QA | Gerekli değişen özgün testler + manifest/tree/blob/rollback ve tek birleşik aday üç-yollu gözden geçirme | sahibe bağımlı; sentetik/gerçek ayrı |
| WIN-BUILD | P0 / MI-01+MI-05 | Tam yetkili checkout, byte manifest, source-lock owner review, npm ci/typecheck/Next build/Chromium | gerçek Windows ortamında daha sonra |
| PROMOTE | P0 / merkezî kaynak sahibi | Değişiklikleri `integration/product-dev` ile sahip onaylı ve test kanıtlı aktarım | Product-dev gate; main/PROD hariç |

## 3. Bu tur gerçek kod değişikliği — UI-02A
- `features/ceo-dashboard/OperationalReadback.tsx`: `/api/demo/task-budget` tek pre-existing read endpoint'i. `sample_event_count` oranının paydası sabit '5' yerine mevcut doğrulanmış `office.roles[*].total` toplamından hesaplanır. Kaynak/yetki sınırı listesi: tarihsel D0/UNKNOWN-HOLD, gerçek görev/ajan yok, gerçek harcama ve dispatch DENY.
- `OperationalReadback.module.css`: yalnız EDS değişkenlerine bağlı, 680px'de tek sütun olan semantik veri kökeni listesi; yeni tema veya global stylesheet yok.
- `tests/ui02-ceo-provenance.test.cjs`: eski görsel semantiği bozmadan idle/loading/hold/historical/timeout, stale sızıntısı, 3/5 ve 2/3 olay oranı, zero/minor ayrımı, sadece okuyucu callback'i, CSS responsive kontrolleri.
- Eski `tests/ui-p10j17-ceo.test.cjs` kaynak dosyası Git blob `27167d887f7cd228f8ea6f83887b444f74b2b1e1` **byte-exact yeniden oluşturulup değiştirilmeden çalıştırıldı**; bu dosya adayda değişmedi.
- Önce provenance için `<dl><dd>` alanları eklemek özgün `dd` budget sayımını 2/9 testte bozdu; bu ara deneme FAIL olarak gözlemlendi. Sözleşmeyi bozmamak için yalnız yeni kaynak bölümü `<ul>` ile düzeltildi; özgün test KODU DEĞİŞMEDİ.
- Düzeltilmiş yerel tur: Node **v22.16.0**, global TypeScript **5.8.3**, `NODE_PATH=$(npm root -g) node --test tests/ui-p10j17-ceo.test.cjs tests/ui02-ceo-provenance.test.cjs` → **19/19 PASS**, TAP SHA-256 `6adb0568d3b0e6db63e7d11b5b138cf4c14d6224d0bf7a7f925133c73096aa3f`. VM/React JSX mock + TS transpilation; gerçek React/browser değildir. Pinned TS5.9.3 typecheck/Next build NOT_RUN.

## 4. Risk, teşhis, rollback
- R1 (yükleniyor/HOLD durumunda eski veri sızması): `data` yalnız `phase==='historical'`; negatif test PASS.
- R2 (tarihsel 3/5'i canlı KPI sanma): kaynak ve D0/HOLD metni korunur; gerçek harcama/dispatch DENY. `pair_id` atomiklik kanıtı değildir.
- R3 (DOM semantik regresyonu): özgün 9 test byte-exact PASS, yeni 10 test PASS.
- R4 (frontend typecheck/real React): kilitli TS 5.9.3, tam checkout ve Chromium bulunmadığı için **BLOCKED/NOT_RUN**, PASS çıkarılmaz.
- R5 (ortak manifest/owner): PR39/PR40 ile Product-dev ortak `product/SOURCE_MANIFEST.json` üç-yollu uzlaştırma gerektirir. Onaysız merge yok.
- Kod geri dönüşü: tek izole commit'i normal revert veya aday dalını bırakma. Veritabanı/API/event değişmediğinden veri migrasyonu/rollback gerekmiyor.

## 5. Metrikler ve son kapı
UI kabulü 21/40 → 21/40 delta0. W8 kabulü 3/8 → 3/8 delta0. Geliştirme ilerlemesi payda sabit kanıtlı kriteri yoksa **HESAPLANAMADI**. 24 alan olgunluk değerleri değiştirilmedi.
**Sonraki görev:** MI-05 kaynak incelemesi; ardından UI-02B yol/sahip çakışması ve mevcut metriklerin doğru kaynak sunumu; Windows tam build daha sonra. Yeni CEO mimari kararı gerekmiyor; owner/test/IV/prod kapıları yürürlükte.
