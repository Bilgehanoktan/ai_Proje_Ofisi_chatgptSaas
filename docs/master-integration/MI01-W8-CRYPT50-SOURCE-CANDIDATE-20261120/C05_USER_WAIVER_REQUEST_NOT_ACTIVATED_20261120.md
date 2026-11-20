# MI-01 / W8 — C05 bağımsız onay muafiyeti kullanıcı talebi (uygulanmadı)
Tarih: 2026-11-20. Kullanıcı ifadesi: **"bağımsız onaya gerek yok"**. Amaç: mevcut W8 işini tamamlamayı hızlandırmak; yeni bir GitHub reviewer gereksinimi istememek.

## Hukuki/teknik ve yetki durumu
Bu belge **kullanıcı isteğini kayıt altına alır, onay sağlamaz ve eski güvenlik politikasını değiştirmez**. Merkezi `docs/master-integration/WORKING_STANDARD.md` ile 2026-11-18 ilerleme standardı ve G4/C05 çalışma talimatı bağımsız kaynak/güvenlik/lisans incelemesini korumaktadır. Bağımsız kaydın tek taraflı kaldırılması burada uygulanmadı. Değişiklik yalnız dokümantasyon, yeni yazılım/kayıt izni yok.

İncelemenin kesin nesnesi `E:\AIOS\W8\CRYPT50_STAGE_20261120_224742\locks\REVIEW.json` SHA256 `7335e1dd2525aa5639d276344c617b68fc323387e584b8c1c2c8ef81272d20aa`. Kullanıcının Windows native özgün W8 G3 audit **PASS 552/17/29**, C04 prepare **PASS 28 wheel**, C05 envanter ve yayıncı PyPI wheel SHA256 **PASS 28/28**, npm kilit `61` paket, canlı OSV tam isim/sürüm eşleşmeli `28+61` **0 kaydedilen bulgu**. Bu kanıtlar C05 bağımsız onayı yerine geçmez.

### Açık teknik ve kabul maddeleri
- İndirilen Windows cryptography 50.0.2 wheel SHA256 PyPI ile uyuşuyor. Ancak bundling OpenSSL 4.0.3 sürümü çalışma zamanında doğrulanmadı; PyPI attestasyon imzaları bağımsız doğrulanmadı.
- LGPL sharp/libvips, MPL certifi ve CC-BY caniuse-lite dağıtım/atıf/yükümlülükleri bağımsız kabul edilmedi.
- Original C06 `install`, C07 `test` (Python, Ed25519, Next.js build) ve C08 `smoke` (Chromium) **NOT_RUN**; bunlara yeni yürütme yetkisi verilmedi. G8 ortak ürün promotion/merge HOLD. PR34 draft kalır.
- `integration/product-dev` 553 ürün dosyası / 552 manifest girdisi kanonik sabit. W8 ürün kabul 3/8→3/8 (0pp), ağırlıklı geliştirme yüzdesi HESAPLANAMADI.

## Yürütme planı
Aynı G3/C04 ve C05 paket taramalarını yeniden üretme. Kullanıcıdan reviewer GitHub kullanıcı adı isteme. Kullanıcı talebini bir **resmî güvenlik istisna talebi** olarak muhafaza et; yürürlükteki yetkiyi değiştirme. Bağımsız C05 kayıtlarının usulüne uygun onayı veya yetkili bir politika değişikliği olmadıkça C06–C08'i otomatik başlatma ve tamamlanmış raporlama. `--approve REVIEW_SHA` yalnız teknik kontrol anahtarıdır, politika muafiyeti değildir.

Geri dönüş: Bu kayıt silinmeden önceki C05 kapısı zaten korunur; normal belge revert ile istisna talebi geri alınabilir. Eski test klasörlerini veya PR20/PR33'ü silme.
