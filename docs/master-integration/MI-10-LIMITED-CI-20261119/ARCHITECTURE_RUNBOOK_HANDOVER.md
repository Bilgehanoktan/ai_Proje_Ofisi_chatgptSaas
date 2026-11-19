# MI-10 — Sınırlı GitHub Actions CI / 19.11.2026

## H01 kararı ve dar izin
H01 bu turda önceki CI tasarımını **sınırlı gerçekleştirme** amacıyla açıkça onayladı: yalnız sentetik D0 veri, GitHub-hosted ephemeral runner, salt-okunur repo, sabitlenmiş kaynak ve bağımlılıklar, izinli test altyapısı. Daha önceki global CI HOLD yalnız bu MI-10 PR tabanlı, düşük yetkili test iş akışı için daraltılır. CI üzerinden `main`, `integration/product-dev`, PROD, gerçek kullanıcı/tenant, provider, bütçe/harcama, IAM grant, external effect, production signing key, release, deployment, otomatik merge, güvenlik/IV kabulü veya branch koruma ayarı değiştirilemez. CI sonuçları ürün kabulü değildir.

## Kaynak tabanı ve dal izolasyonu
- Kaynak ana referansı: `integration/product-dev` = `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`.
- Kontrol edilen izole ortak aday: `61bb06efbba7544bfc68260ed8eb4d342cab9b8e` (`integration/mi-common-source-review-01`), 539 ürün dosyası, 538 manifest girdisi.
- Bu turdaki yalnız CI kodu: `integration/mi10-limited-ci-20261119`, ilk taban aynı product-dev commit. İlgili kaynak sahibi dalları değişmedi. PR yalnız CI dokümanı/yardımcı dosyası ve workflow getirir; **taslak ve merge HOLD**.
- İş akışı: `.github/workflows/mi10-limited-ci.yml`; yalnız aynı repo `integration/mi10-limited-ci-20261119` kaynaklı `pull_request` ve `integration/product-dev` hedef dalı, dosya yol filtresi. `workflow_dispatch` kullanılmadı: GitHub bunun için workflow dosyasının default dalda olmasını ister; `main` değişikliği yetki dışında.

## Bileşen ve test matrisi
| Kapı | Gerçek kaynak ve koşul | Sonuç ilk teslim |
|---|---|---|
| MI-01 kaynak | `w8_mi_common_02.py audit`, tam manifest SHA-256, ortak şema/fixture eşlemesi, SHA/commit pin | CI koşumu bekleniyor |
| MI-01 npm | Özgün ORG `package-lock.json` byte + SHA256, `npm ci --ignore-scripts`, hiçbir lock regeneration yok | CI koşumu bekleniyor |
| MI-01 frontend | Node `22.16.0`, Next `15.5.29`, React `19.1.10`, TypeScript `5.9.3`; `npm run build`, `npm run typecheck` | CI koşumu bekleniyor |
| MI-01 browser | Python `3.13.5`, Playwright `1.57.0`, paketler tam sürüm sabit, Chromium sadece izinli resmi Playwright indirmesi; özgün `browser_unified_u3.py` ile yalnız `127.0.0.1` ve harici tarayıcı isteklerini engelleme | CI koşumu bekleniyor |
| MI-03/04 | GATE-01 kaynaklarının 30/30 değişmez pin ile geçici klasöre kopyası; özgün `run_t1_direct.py` 7+35=42 gerçek sentetik SQLite testi | CI koşumu bekleniyor |
| MI-03/04 özgün 10 Memory/T1 fullchain | Kaynak ve özgün `run_t1_fullchain.py` mevcut; tam kaynak kapanışı, aynı SQLite sürümü ve sahibi onayı gerekiyor | NOT_RUN/HOLD |
| Korunan IAM/ORG/T1 üç DB PG transaction | GATE02 `durable_ops.py` sürüm çakışması, owner provenance, exact G9/PG/RLS kaynakları açık | NOT_RUN/HOLD |
| W8 tam `prepare-install-test-smoke` kabul zinciri | Fresh Python wheelhouse/fingerprint + source owner review açık; bu diagnostik CI bunu resmî W8 kabulü gibi göstermeyecek | NOT_RUN/HOLD |

## Güvenlik ve sistem politikası
- `permissions: contents: read`; hiçbir `id-token`, `packages: write`, environment, deployment, API key, secret, production DB veya ödeme sağlayıcısı yok.
- Kaynak commit'leri ve GitHub Actions çekirdek eylemleri SHA pinli; npm lock orijinal dosyadan doğrulanıp kopyalanır, yeniden üretilmez.
- CI logları yalnız sentetik; tarayıcı ekran görüntüleri 7 gün saklanır. Eylemlerin başarısı yalnız kendi test sınırını kanıtlar.
- `pull_request_target`, `push`, `schedule`, `workflow_run`, otomatik merge, release ve CD tetikleyicisi yok.
- GitHub-hosted runner paket registry/Playwright indirmesi mevcut olabilir; bunlar kayıtlı ve sabit test bağımlılığı kaynaklarıdır. Gerçek ürün provider/effect çağrısı izni verilmez.
- Çalışma zamanı `OPENAI_API_KEY` ve `DATABASE_URL` boş; sadece kullanıma açık test portu `127.0.0.1:17300`. Gerçek provider testleri yok.

## Çakışma, bakım, hata teşhis ve rollback
Bu çalışma MI-10 QA/CI otomasyonu hattına aittir; MI-01/03/04 ürün kodlarının sahibi değiştirilmedi. T1 testleri için ikinci güvenlik motoru yazılmadı; yalnız veri kopyalama/ SHA doğrulayan `.github/mi10/materialize_t1_selected.py` eklendi.

- FAIL kaynak: `source-integrity` ve Git blob/manifest pinini incele; yanlış ortak adayı düzeltmek için geçmişi yeniden yazma.
- FAIL npm: `package-lock.json` veya package root farkını owner ile uzlaştır; `npm install --package-lock-only` kesinlikle çalıştırma.
- FAIL Next/Chromium: platform, bağımlılık, gerçek test logları ve U3 ekran görüntülerini karşılaştır; var olmayan W8 kabul makbuzunu üretme.
- FAIL T1: 30 pin, G6A overlay ve unittest count/exit code kaydını değerlendir; sentetik test sonucu korunan COMMIT kabulü değildir.
- CI yoksa: GitHub Actions ayarları, PR etkinliği/runner izinleri, dosya yolu filtresi ve workflow görülme durumunu kontrol et; onay veya koşum olmadan PASS yazma.
- Geri dönüş: taslak PR'ı kapat; yalnız CI dalında eklenen commitleri normal revert et. Ortak ürün, kanonik product-dev, main ve güvenlik kaynaklarına dokunulmadı; force-push yok.

## Geliştirme ve kabul kaydı
Önceki seçili regresyon 97/97 tarihsel; yeni CI koşumu yoksa sıfır yeni PASS. Bu çalışma yeni ürün kodu ve resmî kabul kriteri kapatmaz; `acceptance_delta = 0`. Genel geliştirme yüzdesi grup ağırlıkları/sabit kriter paydaları onaylanmadan hesaplanamaz. Kanıt ayrı tutulacak: YAML teslim edilmiş ≠ workflow koşmuş ≠ PASS ≠ W8 tam ürün testi ≠ bağımsız kabul.

Sonraki görev: Taslak PR ve GitHub Actions durumunu doğrula; eksik koşum varsa Actions ayar ve olay koşullarını göster; koşum gerçekleşirse job sonuçlarını, logs/artifact ve SHA'yı kanıt olarak kaydet. Source-owner onayı ve full stack build, gerçek PG/RLS/üç DB COMMIT, W8 full browser kabulü ayrı yapılacak.

## İlk CI çalıştırması ve kök neden
GitHub run `44610698699` (commit `8d1de87fae562237826b1050e46626071b0eb285`): W8 audit 538/538 SHA-256 + 17 ortak çift + 33 yardımcı blob PASS; npm kilidi 61/61, Next build ve TypeScript PASS; orijinal T1 7/7 + 35/35 = 42/42 PASS (30/30 kaynak doğrulama). U3 browser FAIL: `browser_unified_u3.py:42` beklenen 200 alınamadı. Next `/api/demo/shared-snapshot` gerçek backend `/demo/v1/lifecycle/shared-snapshot` okumak zorunda; önceki CI yalnız Next sunucusu başlatmıştı. Yanıt HOLD/503 olduğundan test doğru biçimde başarısız oldu.

Düzeltme (ürün veya test beklentisi değişmedi): Önceki özgün `test_lifecycle_prefix_p03.export_prefix_fixture` ile gerçek geçici SQLite prefix üretilir, `app.main:app` FastAPI yalnız loopback port 17301'de çalışır ve Next bunu `AICOS_D0_BACKEND_PORT` üzerinden kullanır. Yalnız sentetik ve tam sürüm sabitlenmiş Python paketleri `.github/mi10/requirements-browser.txt` içindedir. Orijinal `browser_unified_u3.py` tekrar çalışır; DB dosyasının SHA-256 değeri değişmemeli. Bu W8'in henüz onaylanmamış wheelhouse/fingerprint kabul zinciri değildir. Tekrar koşum sonucu görülmeden PASS denmez.
