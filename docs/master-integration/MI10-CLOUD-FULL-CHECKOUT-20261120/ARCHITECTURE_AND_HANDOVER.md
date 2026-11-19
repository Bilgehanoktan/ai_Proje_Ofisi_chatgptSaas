# MI-10 → MI-01 | Bulutta tam kaynak doğrulaması, sahiplik ve devir

Tarih: 20.11.2026 • Sınıf: ACTUAL_CLOUD_CHECKOUT_AUDIT • Ürün kaynak/PR birleştirme/gerçek güvenlik kabulü değildir.

## Ne, neden, nerede, nasıl
Amaç: MI-01'in bilgisayara özgü tam checkout bağımlılığını, daha önce kapsamı daraltılmış GitHub Actions içerisinde aynı repo kaynaklarını salt-okunur indirerek ortadan kaldırmak. Yeni downloader, güvenlik motoru ya da ikinci kaynak transfer mekanizması oluşturulmadı. MI-COMMON-05 sahibi zaten `mi05_verified_local_checkout.py` hazırlamıştı; bu dosyaya dokunulmadı.

Yalnız `integration/mi10-limited-ci-20261119` üzerindeki `.github/workflows/mi10-limited-ci.yml` dosyasının mevcut **source-integrity** işine iki adım eklendi:
1. GitHub-hosted Linux ortamında `87272b6aebd1ce4b26d3a789b2ea75e4310cf60a` commit'i, 61bb ortak ürün adayı ile **ayrı** bir klasöre ve `persist-credentials:false` ile checkout edildi.
2. 1.953 izlenen dosyanın her birinin çalışma ağacı baytları, kendi Git blob hash'ine karşı yeniden SHA-1 hesaplanarak doğrulandı. 1.953 mode 100644, 22.342.956 bayt, sıfır symlink/submodule ve 539 ürün dosyası doğrulandı. Tüm ağacın SHA'sı `187f652f1b1ff8604981833f634c4531a33f8a47`. İki commit arasındaki ürün ağacı Git SHA'sı **aynı**: `617e1ca5f5b657d9fe8ad09017a60ecd47ce6bad`.
3. Özgün `w8_mi_common_02.py audit --repo archive` 538/538 ürün SHA-256, 17/17 sözleşme/fixture çifti, 33/33 yardımcı Git blob ile yeniden PASS.

Önceki `61bb` → `872` compare: 2 commit ileride, 0 geride; yalnız 7 dokümantasyon/yardımcı dosya değişti, `product/` altında **0** farklı dosya. Arşiv ürün kodunun bir terfi edilmiş sürümü değildir.

## Kanıt ve kapsam
- Workflow commit: `4dda0455340c7e6b6dbfef71a0018b2f00c90706`.
- Gerçek GitHub Actions run: [44617509366](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44617509366). Kaynak-doğrulama job: **135890048240, PASS**.
- Test kanıtı ve sayaçları: [EVIDENCE.json](EVIDENCE.json). Teknik katalog: [TECHNICAL_CATALOG.json](TECHNICAL_CATALOG.json).
- MI-COMMON-05 Windows kaynak aktarımının ayrıca çalıştırıldığı iddia edilmez. Bu, **Github-hosted tam checkout PASS** kanıtıdır; orijinal Model/Memory 344, Core tarihsel 29 ve W8 `prepare/install/test/smoke` henüz koşulmadı.
- Yeni özgün ürün test sayısı: 0. Mevcut 42/42 D0 T1 testi tekrar koşulursa yalnız eski seçili regresyon olur. Bağımsız IV veya gerçek PostgreSQL/IAM–ORG–T1 COMMIT bu işin kapsamı dışındadır.

## Mimari ve güvenlik
Kaynak DAG: `integration/product-dev` geçici ortak taban (korunur) → `61bb` aday ürün, tamamlayıcı kayıtlar → `872` iki doküman/yardımcı commit sonrası **aynı ürün ağacı**. CI dalı yalnız GitHub-hosted CI tanılama; otomatik merge, `main`, gerçek grants, kullanıcı verisi, PROD, provider, harcama, OIDC ve write token kapalı. İzin `contents:read`, sadece önceden tanımlı draft PR #4. W8'in `REVIEW.json` sahip incelemesi ve özgün aşama kapıları değiştirilmedi.

## Sonraki gerçek iş / engeller
1. **MI-01 / Unified kaynak sahibi:** artık doğrulanmış tam kaynak checkout'u kullanarak özgün W8'in `prepare` aşamasında, yalnız izinli ve gözden geçirilmiş Python wheelhouse/npm kilidi adayını çıkarıp provenance, transitif sürüm ve SHA fingerprint'i *ayrıca* incelemeli. `install/test/smoke` ancak o aşamanın açık inceleme onayından sonra. Sonuçları kabul PASS saymadan önce W8'in kendisiyle koş.
2. **MI-01 browser:** eski native Chromium CDP `text/event-stream` gövde okuma problemi kalır. Mevcut same-response SSE-compat Playwright PASS, byte-exact native test PASS ile eşit değildir. UI kaynakları başka sohbette değişirken bu dalda tekrar yazılmayacak.
3. **MI-03/04 / Core/IAM/ORG sahipleri:** GATE02 atama/rol provenance, gerçek PostgreSQL RLS ve korumalı üç-database COMMIT, Memory–T1 son 10 senaryo, bağımsız IV ayrı devam etmeli. Yeni T1 motoru çıkarılmamalı.
4. **MI-10:** kaynak-audit kanıtını ve merkezi kuyruğu güncelle, no-merge sınırını koru; başka PR ile mükerrer checkout tool yazma.

## Teşhis, bakım, geri dönüş
- `CHECKOUT_SHA_HOLD`: repo/commit eşleşmesini kontrol et; branch head'e göre sessiz repin yapma.
- `GIT_TREE_PIN_HOLD` veya `SOURCE_BYTES_HOLD`: ZIP/archive veya çalışma ağacı line ending, symlink veya veri bozulması; `main` üzerinde düzeltme yapma, sorunlu aşamayı FAIL bırak.
- `PRODUCT_TREE_MISMATCH`: ortak adayın ürünü değişmiş; W8'de veya başka ürün dosyasında bu CI sohbetinden değişiklik yapılmaz, sahip incelemesi HOLD.
- `W8_AUDIT_FAIL`: SHA256 manifest, frontend-backend parity veya yardımcı runner pinleri; net path ve Git blob referansı olmadan kabul verilmez.
- `W8_REVIEW_HOLD`: bağımlılık fingerprint'i yeniden hesaplama onay demek değildir; takip eden aşamaları başlatma.
- Rollback: yalnız `integration/mi10-limited-ci-20261119` üzerindeki CI commit'in normal `git revert` incelemesi veya taslak PR #4'ün kapatılması; geçmişi yeniden yazma, ürün dalını birleştirme ya da canlı güvenlik ayarı değiştirme yok.

**İlerleme raporu:** Doğrulanmış yeni kaynak bütünlük kriteri var; MI-01'in genel kriter paydası mevcut onaylı raporda sabit olmadığı için 15/35/20/20/10 üzerinden yeni yüzde **HESAPLANAMADI**. Ürün kabul artışı **0 yüzde puan**; önceki/simdiki kanonik oranlar korunur.
