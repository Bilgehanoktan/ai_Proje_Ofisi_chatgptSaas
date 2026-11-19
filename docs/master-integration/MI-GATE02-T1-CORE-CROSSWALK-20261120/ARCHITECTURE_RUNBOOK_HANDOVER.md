# AI Company OS — GATE-02 / T1 / Core ortak güvenlik kapısı (2026-11-20)
Durum: **MİMARİ ÇAPRAZ BAĞLANTI DOĞRULANDI; GERÇEK GÜVENLİK KABULÜ HOLD.**
Referanslar: `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` kanonik product-dev, `bd57cc8235a13ba5bf10545a7879be98fd7b47f5` common yardımcı kaynaklar, `21de30d80528bff893ebbbf225354b44ae514917` PR #6, `5781c8992ebdaf97b8d5eec7622a105b58bcd1e8` governance başlangıcı.

## Ne / neden / nerede / nasıl
Bu turda yeni güvenlik motoru, yürütme yolu, migration veya CI workflow oluşturulmadı. Özgün D-03/D-04 güvenlik tasarımının sekiz olumsuz/restore senaryosu, GATE-02'nin eski SQLite + eski ZERO pin ile sentetik ACCEPTED_D0 tekrarını gösteren owner testleri ve özgün T1 0214 full restore son vakasıyla eşlendi. Kaynak dosyalarının tam Git blob SHA'ları ve PR sahipliği kontrol edildi. Bu **test yürütme değil**; gerçek owner 79/79 ve seçili MI10 42/42 kanıtı ayrı tutularak statik sözleşme doğrulamasıdır.

Mevcut D-03/D-04 tasarımındaki A (bağımsız consensus root/sink), B (harici append-only checkpoint + bağımsız serializer) ve C (D0 HOLD) seçenekleri henüz onaylı değildir. Başka sohbet tarafından seçim yapılmadı; yeni gerçek yetki açılmaz.

## Gerçek GATE-02 açık kusur
Eski DB ve bağımsız denilen fakat aynı restore kapsamına girebilen eski pinin bir arada geri yüklenmesi, sentetik ACCEPTED_D0'ı tekrar üretebiliyor. İmzalı hash chain, yerel SQLite immutable trigger veya aynı restore kapsamındaki anahtar tek başına bu durumun global güncelliğini kanıtlamaz. Mevcut `D0IntentAuthority` sadece ayrı geri yüklenmeyecek varsayımı altındaki işbirlikçi yazarları seri hale getirir, bağımsız yönetilen root/sink değildir. Bu nedenle GATE02/IV/T1 HOLD.

Şartlar: Ayrı yönetim ve kurtarma alanında monotonic root/claim ve yasal owner/role issuer kaynağı; geriye dönük claim tekrarını engelleme; bilinmeyen outcome için quarantine; etki alıcısında güvenli epoch/idempotency fencing; yeniden başlatma, backup/restore, revocation/rotation ve partition negatif kanıtı. D-03/D-04 tasarımı zaten bu şartları tarif eder; ayrı ikinci motor gerekmez.

## PR #6 Core–ORG
[Test adayı](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/6): 10 özgün yöntemin adları ve blob `23c2f019a27bc9e16d8de3f2af72c239eefac035` karşılaştırıldı. **0/10 gerçek fonksiyonel test**; son owner preflight `BLOCKED_NO_PRODUCT_MANIFEST`, exit 2. GitHub kaynak yolunun mevcudiyeti, çalıştırılmış `ResearchFixture` ve `OperationsStore` demek değildir. Hem ORG hem Core cursors ayrı SQLite, atomik global COMMIT/owner provenance değil. PR6 sahibinin tam sabit 553-manifest checkout + `python -B -m unittest discover -s tests -p test_core_operations_assignment_mi03.py -v` koşumuna ihtiyaç var. Mevcut MI10 H01 CI yetkisi PR6'yı kapsamaz.

## T1 ve ortak ürün kapanışı
- Önceki 42/42 T1: MI10 PR4 GitHub Actions PASS; tekrarlı sentetik D0 SQLite.
- Özgün 0214 Memory–T1: 10 yöntem statik kaynakta var, **0/10 NOT_RUN**; son testin beklenen sonucu restore zayıflığını yeniden üretmek, güvenlik kabulü değildir.
- G2 50, G9 7, protected PostgreSQL COMMIT ve IV: ayrı HOLD.
- Mevcut ortak 539 ürün dosyası; yeni MI-COMMON-05 yardımcı checkout testleri 12/12, **Model/Memory 344, historic Core 29, full W8 ve özgün byte-exact U3 kabulü NOT_RUN/HOLD**. MI10 SSE uyumluluk varyantı PASS olarak ayrı.

## Bakım, engeller, geri dönüş
Sahipleri değiştirme, PR6 veya G8/G9 kaynaklarını otomatik birleştirme. No real grant, customer, spend, provider, sink, CI genişleme veya main/product-dev merge. SOURCE_MANIFEST ve owner SHA uyuşmazsa HOLD. GATE02 belirlenmemiş root owner / receipt/domain ve bağımsız restore testi engel. Bu raporlama commit'ini normal revert ile geri al; hiçbir claim/nonce'u sıfırlama. Sürüm oranları ve kabul sayıları aynı: IAM/ORG 42.5%→42.5% (0 puan); Core 12/16, MVP 0/11, IV 0/7; genel ürün geliştirme **HESAPLANAMADI**.
