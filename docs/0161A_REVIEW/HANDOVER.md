# 0161-A — devir ve bir sonraki adım
Güncel kanonik repo durumu: 0160 / R7, v1.19. Bu turdaki 0161-A ayrı A0 tasarım deltasıdır; v1.20 aday katalog, gerçek repo revizyonu değildir. 31 yeni oracle tanımı, 0 çalıştırılan test, 0 yeni ürün kodu, 0 repo yazımı, 0 merge.

## Açık blokajlar
- Tam 0160 ZIP'i burada yok. Mevcut dalda `delivery/0160-helper` 3 dosya ekler; helper kaynaklarını çalıştırmadım. Tam tarihsel arşiv ve kaynak hash doğrulaması gerekiyor.
- T01 HOLD; gerçek CODE/REPO/DEV 0/3. Root AGENTS 0158/0159/0160 dar repo istisnası; 0161 için yeni repo yazımı/merge varsayılmaz. Önceki kaynak adayı ile NO_CODE normatif gerilimi kapanmadı.
- R03 beşinci readback UNKNOWN; 4/5/7 fiziksel kararları ve gerçek owner açık. R06 0/16 owner, 0/55 fields. IV/witness/PEP bağımsız kanıt yok. D4/D5 özgün ZIP eksik. R1/T1/F3 yönü değişmedi.

## Sıradaki 0161-B hazırlığı
1. Kullanıcıdan 0160 tam proje arşivini (delivery helper ile oluşturulmuş arşiv dahil) al; exact manifest ve hashleri doğrula; önceki ZIP'leri koru. 0160 root source commit ve son doc commit ayrımını kaydet.
2. Yeni, sınırlı offline kaynak adayı ve gerekirse ayrı 0161 branch yazımı için izin kapsamını teyit et; gerçek test/CI/DEV/PROD/merge ayrı kalır.
3. W2 canonical schema mapping + W4 read-set tasarımına öncelik; W7 budget review, W6 IV envelope, W1 join/freshness ve W8 oracle bağımlılıklarına göre kod adayı (yalnız izin varsa). D0 disabled adapter'lar değişmeden kalsın. T1 fiziksel DB mapping kabul edilmeden SQL/migration yok.
4. Yeni kaynak manifesti, teknik katalog, 24 alan tracker, devir, ADR, test raporu ve tam ZIP. 0162 merge hedefi yalnız öneri, birleştirme için tam kaynak, değişiklik incelemesi, izin ve uygun doğrulama gereklidir.

## Rollback
Bu paket repo değiştirmez; uygulanmamış delta göz ardı edilerek 0160'a dönülebilir. Gelecekteki aday branch rollback'i 0160 pininden yeni recovery veya yetkili revert; force push, grant/cache/outbox revival, canlı veri değişimi yok.
