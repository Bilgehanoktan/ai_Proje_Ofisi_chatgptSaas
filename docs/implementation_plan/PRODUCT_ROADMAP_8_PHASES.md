# AI Company OS — ana ürün yol haritası (15.11.2026)
Kullanıcının paylaştığı plan ve "planımızı hafızana al ve ilerlet" yönü. Kaynak metin SHA-256: f6244fe03a812e2a535a0b2d10c56eed746eabc50c693b79b0f9a092b8d538ce. Bu çalışma referansı normatif ADR veya yeni yürütme izni değildir. Resmi 21 domain/63 alt modül ve 24 geliştirme alanı korunur; sekiz ürün fazı ürün odaklı gruplandırmadır.

## Vizyon
İnsan H01 şirket sahibi ve nihai otorite, Orchestrator mantıksal icra koordinasyonu. Hiyerarşik AI çalışanları, kimlik/yetki/uzmanlık, projeler ve DAG, kurumsal hafıza, bütçe, QA, bağımsız IV, SaaS ve çok katlı sanal ofis. Güvenlik ve IV operasyon yönetiminden bağımsız. Hedef organizasyon: icra, proje, mühendislik, Ar-Ge, QA, bağımsız denetim, finans, İK, hukuk/uyum, satış/pazarlama, bilgi yönetimi, güvenlik. Hedef UI: CEO kontrol merkezi, ofis, proje/görev, ajan, kurumsal hafıza, güvenlik/onay. Hedef kapsam mevcut uygulama anlamına gelmez.

## Sekiz ürün fazı
1. Mimari ve geliştirme altyapısı — büyük ölçüde hazır, kabul ayrı.
2. Ürün çekirdeği — T1, PostgreSQL, Runtime, Orchestrator, DAG, Event Store, Outbox, Idempotency; kalıcı ve güvenli görev backend'i. Mevcut öncelik.
3. AI çalışanları — Model Gateway, Skill/Tool/ToolGateway, Memory/Knowledge, collaboration, budget; gerçek yetkiler ayrıca.
4. Sanal şirket/ofis — Frontend, EDS, 2.5D çok katlı ofis, gerçek olaylardan projection, UI salt okunur; paralel.
5. İlk bütünleşik MVP — aşağıdaki 11 ölçüt kanıtlanır.
6. SaaS — tenant izolasyonu, kimlik/rol, hesap, abonelik, kotalar, şablonlar, maliyet.
7. Güvenlik/ölçek/üretim — bağımsız kabul, yük, backup/restore, izleme, CI/CD, PROD kapısı.
8. Denetimli otonom şirket — ekip ve proje oluşturma, öğrenme, performans ve iyileştirme; insan/güvenlik otoritesi korunur.

## Paralel hatlar
A: PostgreSQL/T1/Event Store/Outbox.
B: Runtime/Orchestrator/Scheduler.
C: Model Gateway/Skill/Tool.
D: Memory/Knowledge/Retrieval.
E: Frontend/EDS/Office.
F: SaaS/IAM/Billing/güvenlik.
G: W8 Windows/build/test/bağımsız kabul.
W8 tamamlanması diğer bağımsız işlerin önkoşulu değildir; ortak sözleşmeler ve gerçek bağımlılıklar korunur. Ayrı W8 dalı kendiliğinden birleştirilmez.

## MVP kabul hedefleri
1. Şirket oluşturma.
2. Departman ve ajan tanımı.
3. Kullanıcı görev talebi.
4. Otomatik görev planı.
5. DAG bağımlılık sırasına uygun yürütme.
6. Ajanların izinli AI modeli kullanımı.
7. İzinli araç kullanımı.
8. Kalıcı hafıza/sonuç.
9. Ofisin gerçek durum projection'ı.
10. QA ve bağımsız IV.
11. İnsan onayları ve bütçe sınırları.
Kritik uçtan uca zincir: şirket → ajan → proje → plan/dağıtım → yürütme → kalıcı sonuç/QA/IV → ofis. D0 sentetik test gerçek MVP kabulü değildir.

## Çalışma ve devir
Her tur güncel pinned source, Design Master, kararlar ve tracker okunur. Kodla, entegre et, izinli test/build çalıştır, hataları düzelt, kaynak/manifest/readback doğrula; dosya/sembol/API/DB/event/bağımlılık/test kataloğunu, mimari ve devir kayıtlarını güncelle. Çalıştırılamayanları NOT_RUN veya BLOCKED bırak; skorları kanıtsız yükseltme. CEO-0174 ve CEO-0179=B kapsamında izole geliştirme dalı, yerel build/sentetik test; gerçek ajan/araç/sağlayıcı, harcama, gerçek veri, dış etkiler, bağımsız kabul, CI/main/PROD ayrı kapılar.

Başlangıç referansı: 0192 commit 4f2c6d131c38ca7207d0b89ca001580466fd06d4; ilerleyen turlarda CURRENT ve NEXT_STEP kanonik işaretlerdir.


## 0218 approved integration direction
[0218–0225 sequence](INTEGRATION_SEQUENCE_0218_0225.md) and [source-card crosswalk](../0218/TRACEABILITY.json). This prioritizes existing phase delivery; no phase replacement, new grant or independent acceptance.
