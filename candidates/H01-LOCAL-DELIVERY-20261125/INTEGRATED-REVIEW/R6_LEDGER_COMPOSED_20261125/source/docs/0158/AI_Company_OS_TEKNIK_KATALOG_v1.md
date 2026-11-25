# AI Company OS — Teknik Geliştirme, Bakım ve Arıza Teşhis Kataloğu v1.0

**Tarih:** 14 Kasım 2026 · **Taban:** Design Master v141 / Product draft.3 · **Statü:** STATIC_DOCUMENTATION_ONLY.

Bu katalog geliştirici navigasyonu ve bakım için türev kayıttır; v135 hedefini, v141 yetki durumunu veya normatif sözleşmeleri değiştirmez. Kaynak adayları resmî uygulama değildir. Dosya, hash, Python AST ve TypeScript sözcüksel kaynak incelemesi yapıldı; uygulama/build/tarayıcı/schema validator/TEST çalıştırılmadı. Arıza senaryoları teşhis hipotezi ve planlanan oracle’dır, gözlenmiş arıza değildir.

## 1. Sürüm ve değişiklik geçmişi

Draft.1 arşivinin dış klasör öneki karşılaştırma için kaldırıldı; gerçek kaynak içeriği değiştirilmedi. Dosya farkları depo/paket göreli yolları üzerinden hesaplandı.

| Ürün | Master | Dosya | Eklenen | Değişen | Kaldırılan | Aynı |
|---|---|---:|---:|---:|---:|---:|
| draft.1 | v139 | 28 | 28 | 0 | 0 | 0 |
| draft.2 | v140 | 37 | 9 | 12 | 0 | 16 |
| draft.3 | v141 | 53 | 16 | 15 | 0 | 22 |

### draft.1 / v139

- ZIP: `AI_Company_OS_Product_v0.1.0_SOURCE_CANDIDATE.zip`
- SHA-256: `85dc5a8e74f5f5bdad89c88a148cf0b20dfb0c5918fc7648663a8de8d94b9a4b`
- Master SHA-256: `f581a7cf921cd458541eaf45627d9cace9391b6a7156cd269126abb1ca0d7b59`
- Arşiv SHA master başlığıyla eşleşti; ZIP CRC kontrolü başarılı.

**Eklenen:** `AI_Company_OS_Offline_Demo.html`, `README.md`, `SOURCE_MANIFEST.json`, `ai-company-os-backend/.gitignore`, `ai-company-os-backend/AGENTS.md`, `ai-company-os-backend/CONTRACT_PIN.md`, `ai-company-os-backend/README.md`, `ai-company-os-backend/SECURITY.md`, `ai-company-os-backend/app/__init__.py`, `ai-company-os-backend/app/main.py`, `ai-company-os-backend/contracts/source/office.snapshot.demo.schema.json`, `ai-company-os-backend/fixtures/office.snapshot.json`, `ai-company-os-backend/requirements.txt`, `ai-company-os-frontend/.gitignore`, `ai-company-os-frontend/AGENTS.md`, `ai-company-os-frontend/CONTRACT_PIN.md`, `ai-company-os-frontend/README.md`, `ai-company-os-frontend/SECURITY.md`, `ai-company-os-frontend/app/globals.css`, `ai-company-os-frontend/app/layout.tsx`, `ai-company-os-frontend/app/office/page.tsx`, `ai-company-os-frontend/app/page.tsx`, `ai-company-os-frontend/contracts/generated/office.snapshot.demo.schema.json`, `ai-company-os-frontend/features/Dashboard.tsx`, `ai-company-os-frontend/fixtures/office.snapshot.json`, `ai-company-os-frontend/office/OfficeScene.tsx`, `ai-company-os-frontend/package.json`, `ai-company-os-frontend/tsconfig.json`.

**Değişen:** Yok.

**Kaldırılan:** Yok.

### draft.2 / v140

- ZIP: `AI_Company_OS_Product_v0.1.0_draft2_SOURCE.zip`
- SHA-256: `aa233596525038526f79547908b2008e7adb96c26507e52b9d257c3ccd41c63c`
- Master SHA-256: `3667c1d8fcad10afbb317511197b92de6f4a338ccc61022606f976a21057e8ca`
- Arşiv SHA master başlığıyla eşleşti; ZIP CRC kontrolü başarılı.

**Eklenen:** `REVIEW_CHECKLIST.md`, `ai-company-os-backend/app/demo_policy.py`, `ai-company-os-backend/contracts/source/company.catalog.demo.schema.json`, `ai-company-os-backend/fixtures/company.catalog.json`, `ai-company-os-frontend/contracts/generated/company.catalog.demo.schema.json`, `ai-company-os-frontend/features/uiCatalog.json`, `ai-company-os-frontend/fixtures/company.catalog.json`, `ai-company-os-frontend/public/office-core.svg`, `ai-company-os-frontend/public/office-reserve.svg`.

**Değişen:** `AI_Company_OS_Offline_Demo.html`, `README.md`, `SOURCE_MANIFEST.json`, `ai-company-os-backend/CONTRACT_PIN.md`, `ai-company-os-backend/README.md`, `ai-company-os-backend/app/main.py`, `ai-company-os-frontend/CONTRACT_PIN.md`, `ai-company-os-frontend/README.md`, `ai-company-os-frontend/app/globals.css`, `ai-company-os-frontend/features/Dashboard.tsx`, `ai-company-os-frontend/office/OfficeScene.tsx`, `ai-company-os-frontend/package.json`.

**Kaldırılan:** Yok.

### draft.3 / v141

- ZIP: `AI_Company_OS_Product_v0.1.0_draft3_SOURCE.zip`
- SHA-256: `c097f5d1291e16066813b55f4259d85d6e51cd41de1785d43997f27a9a700a04`
- Master SHA-256: `cdb947321a1f4b20f7d4a33548ddb5830a9831930124cc19062dee4e4ffb9eb5`
- Arşiv SHA master başlığıyla eşleşti; ZIP CRC kontrolü başarılı.

**Eklenen:** `CORE_REVIEW.md`, `ai-company-os-backend/app/core/__init__.py`, `ai-company-os-backend/app/core/dag.py`, `ai-company-os-backend/app/core/event_store.py`, `ai-company-os-backend/app/core/office.py`, `ai-company-os-backend/app/core/orchestrator.py`, `ai-company-os-backend/app/core/security.py`, `ai-company-os-backend/app/core/t1_port.py`, `ai-company-os-backend/contracts/source/core.preview.demo.schema.json`, `ai-company-os-backend/contracts/source/core.preview.response.schema.json`, `ai-company-os-backend/fixtures/core.preview.json`, `ai-company-os-frontend/contracts/generated/core.preview.demo.schema.json`, `ai-company-os-frontend/contracts/generated/core.preview.response.schema.json`, `ai-company-os-frontend/features/CorePreview.tsx`, `ai-company-os-frontend/fixtures/core.preview.json`, `ai-company-os-frontend/office/geometry.ts`.

**Değişen:** `AI_Company_OS_Offline_Demo.html`, `README.md`, `REVIEW_CHECKLIST.md`, `SOURCE_MANIFEST.json`, `ai-company-os-backend/CONTRACT_PIN.md`, `ai-company-os-backend/README.md`, `ai-company-os-backend/app/main.py`, `ai-company-os-backend/fixtures/company.catalog.json`, `ai-company-os-frontend/CONTRACT_PIN.md`, `ai-company-os-frontend/README.md`, `ai-company-os-frontend/app/globals.css`, `ai-company-os-frontend/features/Dashboard.tsx`, `ai-company-os-frontend/fixtures/company.catalog.json`, `ai-company-os-frontend/office/OfficeScene.tsx`, `ai-company-os-frontend/package.json`.

**Kaldırılan:** Yok.

## 2. Uygulama akışı ve kararların gerekçesi

- v139/draft.1: Next/React/TS/Phaser ve FastAPI adayları; ilk sentetik arayüz ve iki GET. Kaynak-adayı sınırı, resmî yetki istisnası değil.
- v140/draft.2: 13 görünüm, yedi ajan detay sekmesi, koyu tema, SVG ofis; kapsamı görünür kılmak için katalog. Gerçek çalışma veya kanıt üretmez.
- v141/draft.3: Saf DAG, plan, bellek içi replay ve layout doğrulaması; dış etkiyi kapatmak için deny-only ve DisabledT1. Görsel BFS, yetki veya gerçek hareket değildir.
- CODE=C, REPO=C, DEV=B koşullu kullanıcı kararları; iki ayrı depo, backend kaynak sözleşmesi, frontend pinli tüketici. Depo adları ve algoritmalar teknik adaydır.
- Önceki v139–v141 metinlerinin birebir suffix koruması kontrol edildi.

## 3. Dosya kataloğu — draft.3

Her dosya için konum, amaç ve ilk görülme sürümü aşağıda. Tam hash/byte, sembol ve import listeleri eşlik eden JSON içindedir.

| Dosya | Amaç | İlk sürüm |
|---|---|---|
| `AI_Company_OS_Offline_Demo.html` | Bağımsız çevrimdışı HTML/CSS/JS prototipi; Next/Phaser build çıktısı değil. | draft.1 |
| `CORE_REVIEW.md` | 22 C3 inceleme oracle ve açık üretim sınırları; NOT_RUN. | draft.3 |
| `README.md` | Kaynak adayının kapsamı ve kullanım notları. | draft.1 |
| `REVIEW_CHECKLIST.md` | İnceleme ve kabul hazırlık listesi. | draft.2 |
| `SOURCE_MANIFEST.json` | Paket kaynak manifesti; doğrulama kabulü değil. | draft.1 |
| `ai-company-os-backend/.gitignore` | Git hariç tutma kuralları. | draft.1 |
| `ai-company-os-backend/AGENTS.md` | Geliştirme aracı için çalışma kapsamı ve sınırlar. | draft.1 |
| `ai-company-os-backend/CONTRACT_PIN.md` | Ortak schema/fixture SHA-256 pinleri. | draft.1 |
| `ai-company-os-backend/README.md` | Kaynak adayının kapsamı ve kullanım notları. | draft.1 |
| `ai-company-os-backend/SECURITY.md` | Güvenlik sınırları ve yasaklar. | draft.1 |
| `ai-company-os-backend/app/__init__.py` | Python paket işareti. | draft.1 |
| `ai-company-os-backend/app/core/__init__.py` | Python paket işareti. | draft.3 |
| `ai-company-os-backend/app/core/dag.py` | Görev kimliği/rol/bağımlılık doğrulaması; deterministik topolojik dalgalar, release sınırı. | draft.3 |
| `ai-company-os-backend/app/core/event_store.py` | Değişmez bellek içi sentetik ledger; kapsam, duplicate, sıra, payload, freshness kontrolü. | draft.3 |
| `ai-company-os-backend/app/core/office.py` | 6×6 sentetik layout, oda/istasyon/hücre sınırı doğrulaması. | draft.3 |
| `ai-company-os-backend/app/core/orchestrator.py` | RESEARCH planını doğrular, dalgaları çıkarır; tüm görevler HOLD, admission DENY. | draft.3 |
| `ai-company-os-backend/app/core/security.py` | Deny-only etki talebi; hiçbir grant/epoch/lease girdisi ALLOW açmaz. | draft.3 |
| `ai-company-os-backend/app/core/t1_port.py` | Gelecekteki T1 commit portu; DisabledT1 her zaman PermissionError. | draft.3 |
| `ai-company-os-backend/app/demo_policy.py` | Salt-okunur yetki projeksiyonu, gerçek enforcement değil. | draft.2 |
| `ai-company-os-backend/app/main.py` | Beş salt-okunur demo GET; fixture okuma ve çekirdek önizleme bağlantısı. | draft.1 |
| `ai-company-os-backend/contracts/source/company.catalog.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.2 |
| `ai-company-os-backend/contracts/source/core.preview.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.3 |
| `ai-company-os-backend/contracts/source/core.preview.response.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.3 |
| `ai-company-os-backend/contracts/source/office.snapshot.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.1 |
| `ai-company-os-backend/fixtures/company.catalog.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.2 |
| `ai-company-os-backend/fixtures/core.preview.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.3 |
| `ai-company-os-backend/fixtures/office.snapshot.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.1 |
| `ai-company-os-backend/requirements.txt` | Backend bağımlılık pinleri; kurulum kanıtı yok. | draft.1 |
| `ai-company-os-frontend/.gitignore` | Git hariç tutma kuralları. | draft.1 |
| `ai-company-os-frontend/AGENTS.md` | Geliştirme aracı için çalışma kapsamı ve sınırlar. | draft.1 |
| `ai-company-os-frontend/CONTRACT_PIN.md` | Ortak schema/fixture SHA-256 pinleri. | draft.1 |
| `ai-company-os-frontend/README.md` | Kaynak adayının kapsamı ve kullanım notları. | draft.1 |
| `ai-company-os-frontend/SECURITY.md` | Güvenlik sınırları ve yasaklar. | draft.1 |
| `ai-company-os-frontend/app/globals.css` | Dashboard görsel teması, yerleşim ve responsive stiller. | draft.1 |
| `ai-company-os-frontend/app/layout.tsx` | HTML dili ve global CSS. | draft.1 |
| `ai-company-os-frontend/app/office/page.tsx` | Ofis başlangıç görünümü. | draft.1 |
| `ai-company-os-frontend/app/page.tsx` | Genel bakış başlangıç görünümü. | draft.1 |
| `ai-company-os-frontend/contracts/generated/company.catalog.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.2 |
| `ai-company-os-frontend/contracts/generated/core.preview.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.3 |
| `ai-company-os-frontend/contracts/generated/core.preview.response.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.3 |
| `ai-company-os-frontend/contracts/generated/office.snapshot.demo.schema.json` | Sentetik JSON schema; backend kaynak, frontend üretilmiş kopya; normatif KS/NS değil. | draft.1 |
| `ai-company-os-frontend/features/CorePreview.tsx` | Yerel fixture üzerinden DAG dalgaları ve örnek olay replay UI; backend çağrısı değil. | draft.3 |
| `ai-company-os-frontend/features/Dashboard.tsx` | Ana navigasyon, KPI, ofis/ajan seçimi, panel ve katalog görünümleri. | draft.1 |
| `ai-company-os-frontend/features/uiCatalog.json` | Navigasyon, rol ve ekran metinleri. | draft.2 |
| `ai-company-os-frontend/fixtures/company.catalog.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.2 |
| `ai-company-os-frontend/fixtures/core.preview.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.3 |
| `ai-company-os-frontend/fixtures/office.snapshot.json` | Sentetik veri fixture; gerçek iş/ajan/kanıt değil. | draft.1 |
| `ai-company-os-frontend/office/OfficeScene.tsx` | Phaser dinamik import, kat çizimi, istasyon seçimi, rota/zoom ve cleanup. | draft.1 |
| `ai-company-os-frontend/office/geometry.ts` | İzometrik koordinat, yürünebilir hücre BFS, avatar durum projeksiyonu. | draft.3 |
| `ai-company-os-frontend/package.json` | Frontend bağımlılık pinleri ve aday dev/build komutları. | draft.1 |
| `ai-company-os-frontend/public/office-core.svg` | Çekirdek kat statik SVG görseli, Phaser çıktısı değil. | draft.2 |
| `ai-company-os-frontend/public/office-reserve.svg` | Rezerv kat statik SVG görseli. | draft.2 |
| `ai-company-os-frontend/tsconfig.json` | TypeScript derleyici ayar adayı. | draft.1 |

## 4. Çekirdek semboller ve bağımlılıklar

Satırlar draft.3 ZIP içindeki fiziksel dosya satırıdır. Python AST parse statik incelemedir; TS/TSX sembolleri sözcüksel adaydır.

### `ai-company-os-backend/app/core/dag.py`

`Task` L6–10, `GraphError` L14–15, `topological_waves` L17–39, `ancestors` L41–50, `validate_release_boundary` L52–67

Import: `dataclasses`, `typing`.

### `ai-company-os-backend/app/core/event_store.py`

`Event` L6–16, `Ledger` L19–21, `AppendResult` L24–26, `append_preview` L28–51, `reject` L29–30, `replay_preview` L53–69

Import: `dataclasses`, `typing`.

### `ai-company-os-backend/app/core/office.py`

`validate_layout` L2–29

Import: Yok.

### `ai-company-os-backend/app/core/orchestrator.py`

`preview_plan` L5–15

Import: `.dag`, `.security`.

### `ai-company-os-backend/app/core/security.py`

`EffectRequest` L5–13, `Denial` L16–21, `deny_effect` L24–35

Import: `dataclasses`.

### `ai-company-os-backend/app/core/t1_port.py`

`CommitIntent` L6–17, `T1Port` L19–22, `commit` L20–22, `DisabledT1` L24–26, `commit` L25–26

Import: `dataclasses`, `typing`.

### `ai-company-os-backend/app/demo_policy.py`

`authority_projection` L4–5

Import: `typing`.

### `ai-company-os-backend/app/main.py`

`demo_snapshot` L10–13, `status` L16–17, `catalog` L23–24, `authority` L27–28, `core_preview` L36–40

Import: `.core.event_store`, `.core.office`, `.core.orchestrator`, `.demo_policy`, `fastapi`, `json`, `pathlib`.

### Kritik frontend bağlantıları

- `app/page.tsx` ve `app/office/page.tsx` → `features/Dashboard.tsx` → `office/OfficeScene.tsx` / `features/CorePreview.tsx`.
- `OfficeScene.tsx` → `geometry.ts` + Phaser dinamik import; `CorePreview.tsx` → `geometry.ts` + `core.preview.json` (yerel örnek).
- `Dashboard.tsx` → üç fixture + `uiCatalog.json`; `app/layout.tsx` → `globals.css`.
- `app/main.py::core_preview` → `validate_layout` → `preview_plan` + `replay_preview`; `preview_plan` → DAG + `deny_effect`.
- FE doğrudan API kullanmıyor; statik fixture ve backend hesaplaması ayrı.

## 5. API ve sözleşme kataloğu

| Metot | Rota | Handler / satır |
|---|---|---|
| GET | `/demo/v1/office/worlds/{world_id}/snapshot` | `demo_snapshot` L10 |
| GET | `/demo/v1/status` | `status` L16 |
| GET | `/demo/v1/catalog` | `catalog` L23 |
| GET | `/demo/v1/authority` | `authority` L27 |
| GET | `/demo/v1/core/preview` | `core_preview` L36 |

Bütün rotalar sentetik, salt-okunur ve gerçek auth/tenant enforcement değil. Snapshot bilinmeyen world için 404; diğer rotalar sabit örnek veya türetilmiş örnek döner. API davranışı doğrulanmadı.

| Ortak sözleşme / fixture | FE–BE |
|---|---|
| `company.catalog.demo.schema.json` | SHA-256 birebir eşleşti |
| `core.preview.demo.schema.json` | SHA-256 birebir eşleşti |
| `core.preview.response.schema.json` | SHA-256 birebir eşleşti |
| `office.snapshot.demo.schema.json` | SHA-256 birebir eşleşti |
| `company.catalog.json` | SHA-256 birebir eşleşti |
| `core.preview.json` | SHA-256 birebir eşleşti |
| `office.snapshot.json` | SHA-256 birebir eşleşti |

## 6. Arıza teşhis rehberi (hipotez; gerçek arıza yok)

| Belirti | İlk inceleme sırası | Güvenli davranış / oracle |
|---|---|---|
| Ofis boş veya istasyon yanlış | `Dashboard.tsx` → `core.preview.json` → `OfficeScene.tsx` → `geometry.ts` | Kat/istasyon ID eşleşmesi; gerçek ajan uydurma; C3-01/02/21 |
| Rota görünmüyor | `geometry.ts::route`, `walkable`, başlangıç/hedef | Kapalı uçta null; yürünebilir komşuluk; C3-03/04 |
| Avatar yanlış VERIFIED | `geometry.ts::avatarProjection`, UI state | RESERVED/UNKNOWN/UNVERIFIED; sahte proof kabul etme; C3-05/06 |
| DAG ilerlemiyor / döngü | `dag.py::topological_waves`, fixture planı | Eksik bağımlılık veya DAG_CYCLE ret; C3-07–09 |
| QA/IV atlanıyor | `dag.py::validate_release_boundary` → `orchestrator.py` | QA_OR_PRODUCER_BYPASS / IV_BOUNDARY_MISSING / RELEASE_BYPASS; C3-10/11 |
| Olay tekrarı veya sıra boşluğu | `event_store.py::append_preview`, stream/layout/seq | Duplicate aynıysa ignore; çelişki/gap RESYNC_REQUIRED; C3-12–16 |
| Yetki beklenmedik açık | `security.py::deny_effect`, `demo_policy.py`, `t1_port.py::DisabledT1` | DENY; provider çağrısı yok; gerçek etkiyi durdur; C3-17/18 |
| API/arayüz farklı değer | `main.py`, `contracts/`, `fixtures/`, iki CONTRACT_PIN | Önce 7 pin karşılaştır; FE yerel fixture; C3-19/20 |
| Phaser yüklenmiyor | `OfficeScene.tsx`, paket pinleri, cleanup | Statik SVG ile Phaser ayrımını koru; C3-21 |
| HTML demo açılmıyor | Offline HTML, CSP, yerel tarayıcı koşulları | Dış fetch açmadan incele; C3-22 |

JSON `diagnostic_code_occurrences` kaynakta bulunan ret/durum literal adaylarının dosya ve satırlarını içerir; bütün hata kodları için semantik garanti değildir.

## 7. Genişletme ve değişiklik etki haritası

| Yeni özellik | Önce değiştirilecek kaynaklar | Birlikte incelenecek sınır |
|---|---|---|
| Kat/oda/istasyon | `core.preview.json`, `office.py`, `geometry.ts`, `OfficeScene.tsx` | İki fixture kopyası, layout revizyonu, scope, C3-01–06 |
| Yeni ajan rolü | `uiCatalog.json`, `company.catalog.json`, `dag.py::ROLES` (yalnız gerekirse) | Rol ≠ instance ≠ grant, QA/IV ayrımı; manifest/F0 |
| WorkType | `orchestrator.py`, plan fixture, DAG contract | RESEARCH dışı bugün ret; ayrı ürün, IV ve yayın kabulü |
| Event tipi | `event_store.py::Event`, append/replay, schema/fixture, CorePreview | idempotency, sequence, scope, resync; T1 ve outbox ayrı |
| Gerçek API adaptörü | `main.py`, FE tüketici, sözleşmeler | tenant auth, PEP, snapshot freshness, sürüm pinleri |
| Gerçek DB/T1 | `t1_port.py`, gelecekteki DB migration/adapter | W-A, CAS, atomic audit/outbox, restore, bağımsız kabul |

Bu tablo gelecekteki iş planıdır, kodlama izni veya hazır genişleme özelliği değil. Draft.3 içinde fiziksel DB şeması/migration, gerçek worker, model adapter, IV güven kökü, gerçek auth ve restore uygulaması yoktur.

## 8. Test ve kanıt defteri

- `CORE_REVIEW.md`: C3-01–22, hepsi NOT_RUN. `REVIEW_CHECKLIST.md` önceki kontrol kuyruğu.
- Gerçek NEG 0/30, UX 0/24, F0 0/35, C 0/24; etkin CODE/REPO/DEV 0/3; kritik iş 0/23.
- Bu katalog üretiminde ZIP CRC, hash, iki master suffix, Python AST ve 7 dosya eşitliği statik kontrolü yapıldı. Bunlar yazılım testi değildir.
- Resmî CODE/REPO/DEV, gerçek TEST, PROD, harcama, müşteri/dış işlem sınırları değişmedi.

## 9. Her yeni teslimatta zorunlu tutulması önerilen kayıt

Her değişiklik için tekil ID, kaynak master ve ürün sürümü, kullanıcı talebi/karar, görev kartı ve domain, eski/yeni dosya yolu ve hash, sembol/satır, ne-neden-nasıl, giriş/çıkış ve hata, bağımlılık, güvenlik etkisi, test oracle, gerçek yürütme sonucu veya NOT_RUN, bilinen sınırlama, genişletme notu, geri dönüş hedefi, reviewer/kanıt (yoksa NULL).

Örnek kimlik: `CHG-draft.3-DAG-001`. Kayıt değişirse eski kaydı silme; supersedes ilişkisi ekle. Bir sonraki katalogda önceki ZIP ile yeni ZIP arasındaki byte farkını otomatik çıkar; kaynak kodu değiştiğinde sembol/satır ve sözleşme hashlerini güncelle. Resmî depolar açıldığında Git commit SHA ve PR numarasını ekle; bugün NULL.

## 10. Geri dönüş ve kurtarma

- Kaynak referansı: draft.1 / draft.2 / draft.3 arşivleri ve yukarıdaki digestler. Önceki paketi ayrı dizinde açmak kaynak karşılaştırmasıdır; deploy veya DB restore değildir.
- Şema/fixture iki tarafta birlikte pinlenmeli. Uyumsuzlukta yeni tüketici etkinleştirilmemeli.
- Gerçek veritabanı/migration/restore yok; bu yüzden gerçek veri kurtarma prosedürü doğrulanmış değildir. W-A ve IV bağımsız kanıtı olmadan gerçek restore sonrası yetki açılmaz.

## 11. Sonraki katalog güncellemesi

Draft.4 ile yeni kaynaklar geldiğinde katalog farkları, semboller, hata indeksleri, API/schema, karar ve inceleme kayıtları yeniden çıkarılacak. Bu çalışma ilk teknik katalog tabanıdır; geçmişteki her tasarım revizyonunun tam sembol kataloğu çıkarılmış değildir. r67 bu kaynak çizgisinde birleştirilmedi.

