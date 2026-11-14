# DOC-REV-0161-A — önerilen mimari ek
Statü: A0 design candidate; mevcut Design Master'a henüz işlenmedi.

## Korunan kurallar
H01 tek insan CEO; AI Orchestrator operasyonel planlayıcı; T1 tek lokal ACID işlem; R1 restore dışı W-A; PEP tek egress sınırı; QA, IV ve release ayrı güven düzlemleri; F3 sıfır dış yazma. CEO-19-01=C, CEO-19-02=B, GOV-00=B ve önceki ADR seçimleri aynen korunur. Gerçek CODE/REPO/DEV 0/3; T01 HOLD, hiçbir yeni grant yok. r67/r68 ve Sovereign ayrı; D4/D5 özgünleri eksik.

## İnceleme sonuçları
- 0160 manifesti 114 kayıt içerir. 0160 kendi raporunda 114/114, AST 60/60, TS parse 15/15, 48 test NOT_RUN bildirir. Bu turda bütün ürün arşivi indirilmediği için önceki sonuçlar bağımsız yeniden hesaplanmadı.
- W4: `inspect_write_set` mantıksal rol bütünlüğü kontrolüdür; `head_version`, lease/reference, transaction_ref çağıran tarafından sağlanır. Bağımsız readback, gerçek CAS ve atomik commit kanıtı yoktur. `CommitIntent` ve `LogicalIntent` kapsamları birebir değildir. Ayrı portlar ile sonuç şekilleri uzlaştırılmadan writer eklenmez.
- W4: `inspect_chain` per-run genesis zinciri ve eşit epoch ister; gerçek event payload, issuer, commit timestamp ve epoch geçişi kanıtı yoktur. Tarihsel event epoch ile canlı dispatch epoch ayrımı gerekir. `inspect_fence` ve `inspect_outbox` gerçek authoritative lookup değildir.
- W7: `LogicalIntent.budget_ref` referansının bulunması tutar, bakiye, rezervasyon veya muhasebe kanıtı değildir. `DisabledModelGateway.invoke` dış çağrıyı kapalı tutar. Budget/reconciliation ve maliyet tahmini ayrı kapsamlar.
- W6: `inspect_iv` kimlik çakışması ile artifact/readback/current eşitliği kontrol eder; ayrık string ID, gerçek farklı yöneticiler/anahtar kökü değildir. İmza doğrulama/receipt issuer yoktur.
- W2: 16 KS/NS şema pininin sahibi atanmadı; 55 canonical alan kabulü yok. 9 D0 FE/BE pin çifti başka bir envanterdir.
- W1: `office.snapshot.json` layout_revision `draft-hybrid-floor-1`, `core.preview.json` layout.revision `layout-d3-demo`. Ortak iki floor ve dört station ID mevcut olsa da join onayı yok. `Dashboard.tsx` açık HOLD gösteriyor. Python layout validator ile TS validator arasında kapsam/sınır eşitliği kanıtlanmamış. Dashboard footer hâlâ DOC-REV-0154; 0160 kaynak etiketinden bağımsız eski gösterim. Bu etiket ileride tek release metadata kaynağından türetilmeli.

## Önerilen yeni A0 sözleşme yönleri
1. Operasyon türü bazlı write/read-set tablosu, fiziksel eşlemeye ayrı referans; gözlem ile otoritatif kayıt ayrılmalı. Önceki 4/5/7 rakamlarını değiştirme.
2. Bütçe rezervasyonu, harcama gözlemi, kesinleşen ekonomik kayıt ve ödeme/tahsilat ayrı tipler; bilinmeyen sonuçta otomatik serbest bırakma yok.
3. IV receipt payload/digest, signature verification, root/admin/recovery kanıtı, immutable artifact readback ve ayrı release CAS kapısı.
4. Backend contract/source mevcut D0 aday kaynağı; frontend generated tüketici; kök registry indeks, üçüncü şema yazarı değil. KS/NS sahiplik önerileri onay değildir.
5. Ofis snapshot + canonical layout aynı tenant/company/environment/world, revision, digest, seq ve epoch bağlarında tek yönlü projection; stale durumda render dondurulur, hareket devre dışı kalır. UI hiçbir grant/state/release yazmaz.

## Öncelik ve bağımlılık
W2 alan/sahiplik envanteri ve W4 R03 read-set ayrımı paralel; W7 rezervasyon ve W6 IV receipt bu bağlara dayanır; W1 join/freshness kontratı W2 pininden sonra; W8 her hat için ayrı oracle. Kaynak adaylarının kodlanması mevcut izin kapsamı netleşmeden başlamaz. Main merge bu turda yok.
