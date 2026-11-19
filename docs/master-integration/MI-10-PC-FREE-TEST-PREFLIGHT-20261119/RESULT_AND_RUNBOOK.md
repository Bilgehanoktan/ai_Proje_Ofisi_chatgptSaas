# MI-10 — PC gerektirmeyen test geçişi / kaynak ve CI ön kontrolü
Tarih: 2026-11-19. Sınıf: REMOTE_STATIC_PREFLIGHT_ONLY; gerçek ürün testi, tam build, tarayıcı kabulü veya CI koşumu değildir.

## Değişmez referanslar
- Ortak geliştirme tabanı: `integration/product-dev` = `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`.
- Birleşik izole kaynak adayı: `integration/mi-common-source-review-01` = `61bb06efbba7544bfc68260ed8eb4d342cab9b8e`; ortak tabandan 7 commit ileride, 0 geride.
- Ürün manifesti Git blob: `03af243e8683f92c5d9c0b24e90b70d2bd6af29f`, 538 kayıt + manifest = 539 ürün dosyası.
- Kanıtlı önceki seçili ürün regresyonu: 97/97 PASS (ORG 31, projectionRead 12, Skill 41, registry 13); bu tur yeniden koşulmadı.
- W8 kaynak adaptörü: `tests/integration/w8_mi_common_02.py`, blob `acd361f17331f512ce35a1611e8108d32e61680f`.
- Özgün npm lock: `docs/ORG-07C-R8-INTEGRATION/original-lock/package-lock.json`, blob `4cd33f437df85d7e74c7946a0999f76adf2e31fe`; merkezde kayıtlı SHA-256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`. Bu tur yeni SHA-256 hesaplanmadı.

## Bu tur GitHub bağlı kaynaklar üzerinde yürütülen 8 salt-okunur statik denetim
1. `package.json` ile özgün lock kökünün 4 üretim bağımlılığı birebir eşleşti — PASS.
2. 4 geliştirme bağımlılığı birebir eşleşti — PASS.
3. `lockfileVersion=3` — PASS.
4. 61 transitif npm paketinin `integrity` alanı SHA-256/SHA-512 önekli ve `resolved` alanı beklenen HTTPS npm registry kaynağında — 61/61 PASS.
5. İki `overrides` paketi (postcss, sharp) lock ile sürüm uyumlu — 2/2 PASS.
6. Ortak manifest kaydı 538 — PASS (tam dosya SHA-256 taraması değildir).
7. Güncel W8 adaptörü kaynak ağacında, beklendiği gibi npm lock'u referanslıyor; doğru Git blob eşleşti — PASS.
8. Eski `tests/integration/w8_local.py` içinde `npm install --package-lock-only` mevcut — UYARI DOĞRULANDI. Bu komut kilit dosyasını yeniden üretebilir; eski hazırlayıcıyı doğrudan çalıştırma. Mevcut `w8_mi_common_02.py` adaptörünü koru.

Denetimler GitHub üzerinden alınan metin/JSON üzerinde yürütülmüştür. Bu sekiz statik bulgu 8 yeni ürün testi, tam checkout veya güvenlik kabulü olarak sayılamaz. Değiştirilen ürün dosyası = 0; yeni CI workflow = 0; test/build/npm install = NOT_RUN.

## Öncelik ve uygulama sırası
1. MI-01 / Unified sahibi, 61bb06e... sabit commit'ten **tam ve temiz** checkout + özgün manifest üzerinden path/byte/SHA-256 doğrulaması yapar. Eksik dosyada HOLD.
2. `w8_mi_common_02.py` adaptörü ve özgün npm lock için kaynak sahibi gözden geçirmesi; `npm install --package-lock-only` ile kilit üretme yok. Sabit lock ve Python wheelhouse için sürümlü/fresh fingerprint; eski onay tekrar kullanılmaz.
3. İzinli izole ortamda `audit → prepare → install → test → smoke` gerçek W8 zincirini sırayla çalıştır; her adımın exit code, komut, UTC timestamp, Python/Node sürümleri, manifest ve lock hashleri, stdout/stderr, test kimlikleri ve skip sayısını kaydet. İlk başarısız adımda kapat; sonraki kapıları PASS sayma.
4. Backend Python + frontend TypeScript/Next.js + regresyon; ardından yerel izole PostgreSQL/RLS ve Playwright; gerçek IAM/ORG/T1 korumalı COMMIT, IV, dış etkiler ve PROD bağımsız kapılardır.
5. Bilgisayarsız tekrarlanabilir CI otomasyonu ancak mevcut CI yasağı için ayrı yetki kaydı ve kaynak sahibi incelemesi sonrasında. Önerilecek workflow yalnız manuel tetiklemeli `workflow_dispatch`, en az `contents: read` yetkisi, secret/provider/spend yok, sabit commit checkout, sabit bağımlılıklar, süre sınırı ve kanıt/artifact üreten; otomatik merge/deploy kapalı. Bu tur workflow eklenmedi/etkinleştirilmedi.

## Durum / katalog / bakım ve geri dönüş
- MI-01: FULL_CHECKOUT_AND_BUILD_BLOCKED, OWNER_REVIEW_PENDING. MI-10: CI_PLAN_ONLY; LIVE_CI=HOLD.
- Dosya/sınıf/API/veritabanı değişikliği yok. İncelenen semboller: `w8_local.prepare`, `w8_mi_common_02.lock_bytes`, `w8_mi_common_02.extend`; harici bağımlılık eklenmedi.
- Yeni iş paketi yüzdesi hesaplanmadı: gerekli sabit, onaylı geliştirme paydaları bulunmuyor. Ürün kabul değişimi 0; geçmiş kabul oranları korunur.
- Arıza teşhisi: kaynak/manifest uyuşmazlığı → kaynak pini incele; lock uyuşmazlığı → özgün owner lock ile karşılaştır, yeniden üretme; import/npm sorunu → reviewed fingerprint ve izolasyonu kontrol et; build/PG/browser başarısızsa PASS işaretleme, ham kanıtı koru.
- Rollback: bu plan kaydını normal Git revert ile geri al. `integration/product-dev`, ortak izole aday, ana dal, CI ayarları ve önceki kabul delilleri değiştirilmedi.
