# MI-01 W8 P0 — mimari, teknik kayıt ve devir (2026-11-20)

Bu belge, sekiz kapılı operasyonel takip görünümünün **ne/neden/nerede/nasıl** kayıt ve bakım sınırıdır; kanonik `progress/MASTER_INTEGRATION_CURRENT.json` tek merkezi gerçeklik kaynağıdır.

## Yapılan değişiklik
- Yeni kanıt deposu: `docs/master-integration/MI01-W8-P0-PROGRESS-20261120/GATE_REGISTER.json` — sekiz kimlikli sabit doğrulama kapısı; PASS, NOT_RUN ve HOLD_OWNER birbirinden ayrılır. **Tamamlanma 3/8 (%37,5) yalnız operasyondur**.
- `docs/master-integration/MI01-W8-P0-PROGRESS-20261120/DEPENDENCY_REVIEW.json` — gerçek kaynak `requirements.txt`, `requirements-test.txt`, sabit npm lock kaynak pinleri ve W8 Python transitive/wheel/fingerprint eksikleri; gerçek kaynak sahibi onayı **verilmedi**.
- `docs/master-integration/MI01-W8-P0-PROGRESS-20261120/DASHBOARD.md` — kanonik JSON'a referanslanan insan okunur görünüm; genel ağırlıklı yüzdeler paydalar dondurulmadan hesaplanmaz.
- Merkezi kuyrukta yalnız MI-01/W8 takip bağlantısı ve bir sonraki gerçek görev gösterilecek; diğer 9 sahibin kriter yuvaları değiştirilmez.

## Mimarî / katalog
- Ortak referans: `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`.
- İzole ürün adayı: `61bb06efbba7544bfc68260ed8eb4d342cab9b8e`; orijinal tam kaynak checkout `87272b6aebd1ce4b26d3a789b2ea75e4310cf60a`.
- W8 entrypoint: `tests/integration/w8_mi_common_02.py` → özgün W8 `audit/prepare/install/test/smoke`. Özellikle `prepare` mevcut `package-lock.json` dosyasını özgün ORG lock'undan kopyalar; legacy npm kilit yeniden oluşturma çağrısı yalnız adapter tarafından güvenli karşılanır.
- Yeni ürün sınıfı/fonksiyon/API/SQL/şema/dependency **yok**. Yalnız sürümlü takip ve bağımlılık inceleme kaydı.
- Kaynak ve uyumluluk doğrulaması: `44617509366` / 3/3 selected CI PASS, 1953 tracked file/539 product, W8 audit 538, npm lock 61. Bunlar tam W8 test ve IV kabulüne eşit değildir.

## Sonraki P0 ve görev çakışması
MI-01/Unified sahibi temiz W8 `prepare` için bağımlılık kaynaklarını ve registry erişimini inceleyip yeni fingerprint adayı üretecek. Wheelhouse metadata/hash/provenance/lisans/zafiyet incelemesini ayrı onaylayacak. Sonra aynı kaynak+fingerprint ile `install`, özgün `test`, özgün `smoke` ve bağımsız kabul sırası. MI-07/08 Model344, MI-02 Core29, MI-03/04 gerçek protected PostgreSQL ayrı hatlarda; hiçbir yöntem veya test mükerrer yürütülmez.

## Teşhis ve geri dönüş
- Satır değeri eksik kanıtla PASS ise yanlış sınıflandırma; kanıt bağlantısını ve runId/commit'i doğrula, aksi halde NOT_RUN/HOLD.
- Önceki genel geliştirme yüzdesi olmayan kapsamda yapay '0%→%' değişim üretme; 315 taslak kriteri ratified denominator sayma.
- Python wheel hash/REVIEW.json yoksa W8 kurulum izni yok; hash hesaplamak tek başına owner approval değildir.
- Tarayıcı SSE compat sonucu yerel QA ile sınırlandırılır; native CDP ve per-fetch freshness regresyonu ayrı doğrulanmalı, ürün davranışı zorlanmamalı.
- Geri dönüş: yalnız governance dalı belge/pointer normal revert; release, main, product-dev, PR#4 merge, gerçek güvenlik ayarı ve dış maliyet değiştirilmedi.

**Yeni ürün kabul kriteri kapatma: 0, kabul değişimi: 0 yüzde puan, genel geliştirme: HESAPLANAMADI.**

## Son QA düzeltmesi ve yeni kanıt
MI10 tarafından yalnız PR #4 CI dosyalarında taze SSE yanıtının isteğe özgü sıra kaydıyla bağlanması sağlandı. GitHub-hosted `44620987573` 3/3 PASS; ayrı Node 17/17 negatif regresyon ve gerçek Chromium per-fetch uyumluluk akışı PASS. Düzeltme ürün koduna veya orijinal U3 kaynağına dokunmadı. Yerel QA ile ortaya çıkan global Promise stale-body problemi artık testte fail-closed; özgün CDP Response.text ve formal W8 smoke hâlâ HOLD. Kanıt: [MI10 taze-yanıt düzeltmesi](../MI10-SSE-FRESH-REQUEST-FIX-20261120/EVIDENCE.json). **MI-01 P0 3/8 sabit; ilerleme kapısı olarak iki kez sayılmadı.**
