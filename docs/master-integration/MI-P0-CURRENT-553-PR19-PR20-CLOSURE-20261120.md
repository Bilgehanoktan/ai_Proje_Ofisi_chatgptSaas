# AI Company OS — MI-P0 merkezi ilerleme / sahiplik uzlaştırması
20 Kasım 2026 · Kanıt sınıfı: GitHub canlı PR/head, CI sonucu ve sürümlü görev kaydı; **yeni ürün testi değildir**.

## 1. Gerçek kaynak ve paralel görev durumu
- Kanonik **geliştirme** dalı: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`. Ürün **553 dosya / 552 manifest kaydı**; product tree `f4cdcf68115917ab69ba6441414539fe32a59369`, manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`. `main` ve PROD kabulü değişmedi.
- [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20), W8/MI-01 sahibi, **açık taslak / merge edilmemiş**, head `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`. Mevcut frozen npm düzeltmesinin **19/19 yerel sentetik testi** daha önce gerçekten yürütülmüş; bu turda koşulmadı. Orijinal W8 C04 `NOT_RUN`, C05 `HOLD`, C06–C08 `NOT_RUN`.
- [PR #19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19), G2/G9–MI04 sahibi, **açık taslak / merge edilmemiş**, head `0a8907f177bb3e9b458aefb3ea3441b15537f542`. Ayrı aday **562 ürün / 561 manifest**, manifest blob `566b7210b6edb95a21b999dc1d881a12284d9011`. Özgün G2 50 + ORG 15 + tarihsel G9 G7 7 = 72/72 **sentetik D0** testi için [GitHub CI #44700495037](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44700495037) **completed/success**, head birebir eşleşti. Bu eski testler yeni ürün kabulü/benzersiz metot sayısı değildir.
- Önceden [MI-P0 W8 ↔ G2 sıra kapısında](MI-P0-W8-G2-MANIFEST-ORDER-GATE-20261120.md) kanıtlanan çakışma **halen açık**: PR #20 `MANIFEST=27b4eb...` 553 tabanına kilitli, PR #19 yeni manifest `566b72...` içeriyor. İki PR'ı kontrolsüz birleştirmek `U3_MANIFEST_HOLD` üretir; bu fail-closed güvenliktir, kabul değildir.
- [PR #10](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/10) A1 bağımsız root/issuer/sink custody incelemesi de başka sahipte; yeni otorite üretmek/aynı güvenlik hattını tekrar yazmak yasak.

## 2. Bu turda bağımsız olarak kapatılan iş
**Merkezi kaynak/aktif sahiplik/öncelik ve görünür ilerleme anlık kaydı**, eski 505 tabanı ve tarihsel PR yorumlarının kanonik *güncel* durum sanılmasını engelleyecek şekilde `progress/MASTER_INTEGRATION_CURRENT.json` içine yalnız **ek alanlarla** işlendi. Önceki sürümler ve geriye dönük denetim tutuldu. PR #19/#20 sahiplerinin kaynaklarına müdahale **0**, yeni GitHub Actions / test/permission **0**; `integration/product-dev`, `main`, API, DB, olaylar ve yürütme kodu **değişmedi**.

**Hata teşhis/kontrol:** W8 `U3_MANIFEST_HOLD` çıkarsa çalışan kaynak manifestinin Git blobunu, adapter `MANIFEST` değerini ve owner ratifikasyonunu ayrı doğrula. Başarılı izole 72/72 D0 testini gerçek yetki zinciri veya PostgreSQL kabulü sanma. Farklı SHA'yı sırf test geçsin diye pin'e yazma.

## 3. Önceki → güncel ilerleme, yüzde puan değişimi
| Kanıtlı kapsam | Önceki | Güncel | Delta | Anlam |
|---|---:|---:|---:|---|
| Core kanonik kabul | 12/16 (%75) | 12/16 (%75) | 0 | Core özel kabul |
| Premium UI kabul | 21/40 (%52,5) | 21/40 (%52,5) | 0 | UI özel kabul |
| Bütünleşik MVP | 0/11 (%0) | 0/11 (%0) | 0 | Uçtan uca kriterler açık |
| Bağımsız güvenlik IV | 0/7 (%0) | 0/7 (%0) | 0 | Otorite ve kabul HOLD |
| MI-01 W8 operasyonel alt-kapı | 3/8 (%37,5) | 3/8 (%37,5) | 0 | **Ürün tamamlama yüzdesi değil** |
| MI-03 D5-G çalışma paketi geliştirme | %42,5 | %42,5 | 0 | Tarihsel paket kriterleri |
| Genel ağırlıklı geliştirme | HESAPLANAMADI | HESAPLANAMADI | HESAPLANAMADI | 10 grubun **0'ında** sahibi onaylı payda |
| Genel ürün kabulü | HESAPLANAMADI | HESAPLANAMADI | HESAPLANAMADI | Ayrı kriterler toplanıp tek yüzdeye çevrilmez |

Ağırlıklar: tasarım **%15**, kaynak **%35**, fonksiyonel test **%20**, entegrasyon **%20**, nihai kabul **%10**. Geçerli kriter paydası yoksa yüzde uydurulmaz. 72/72 ve 19/19 farklı sentetik kapsamlar; eski başarıları iki kere toplama.

## 4. Sıralı uygulama, gerçek kalan engeller
1. **MI-01/W8 sahibi PR #20:** 553 exact checkout ve önceki özgün npm lock üzerinden izinli, bağımlılık sahibi incelemesiyle **C04 fresh Python wheelhouse/prepare** çalıştırması. `REVIEW.json`/fingerprint, çözülmüş binary ve platform lisansları, gerçek arşiv SHA-512/tarball doğrulaması ve zafiyet incelemesi hâlâ eksik.
2. **Aynı W8 sahibi ve tedarik zinciri sorumlusu:** C05 kaynak/dependency/legal onayı; **ancak sonra** C06 install, C07 tam backend/Next.js build, C08 native tarayıcı testi. Yeni CI yetkisi varsayılmaz; PR #4 dar istisnası genellenmez.
3. **MI-04/G2/G9/ORG/Authority sahipleri:** PR #19'daki tek `intent_authority.py` varyantına sahip incelemesi. Yalnız ratifikasyon ve 553 W8 sonuçlarından **sonra** 562'lik aday için yeniden sabit manifest referansı ve **tam W8 tekrar kabulü**.
4. **MI-02 güvenlik/PG/IV:** Independent Option A root, issuer/claim custody, sink-side fencing+idempotency, eski veri+journal+pin restore tekrar yürütme açığı; korumalı PostgreSQL gerçek COMMIT, RLS ve A-AT01..08 **0/8**. Bağımsız onay olmadan gerçek yetki/PROD yok.
5. **Merkezi entegrasyon:** Sahip imzaları, source pins, tam build, yeni negatif kanıtlar ve geri dönüş incelemesi alındıktan sonra kontrollü transfer; acele `main`/staging/otomatik merge yapılmaz. Dondurulmuş 10-grup kriterleri onaylanmadan global yüzde hesaplanmaz.

## 5. Mimari / teknik katalog / bakım / devir
- **Mimari:** H01, Orchestrator, IAM–ORG–T1, bağımsız root/IV, salt okunur Office/UI ve 553 kanonik ürün sınırları **değişmedi**.
- **Teknik katalog:** Dosya/işlev/API/veritabanı/bağımlılık **yeni veya değişen ürün ögesi 0**; bu turun tek kapsamı `progress/MASTER_INTEGRATION_CURRENT.json` anlık göstergesi ve bu belge. Bağımlılık riski npm 61 lock girişi, 14 isteğe bağlı LGPL içeren paketin/1 CC-BY-4.0 metadata kaydının önceki sahibi incelemesine bağlıdır; otomatik hukuk uygunluğu değildir.
- **Arıza / bakım:** W8 manifest/lock uyuşmazlığında `MANIFEST` ve `product/SOURCE_MANIFEST.json` source SHA'sını karşılaştır; önce sahip onayı, sonra pin/adapter düzeltmesi ve tam regresyon. Güvenlik restore açığı kapanmadan yürütme yok.
- **Rollback:** Yalnız bu iki governance belge değişikliğini normal `revert` ile geri al; historik kanıtlar, PR #19/#20, ürün dalı ve `main` korunur. Force push, claim reset, etki yükseltmesi yok.
