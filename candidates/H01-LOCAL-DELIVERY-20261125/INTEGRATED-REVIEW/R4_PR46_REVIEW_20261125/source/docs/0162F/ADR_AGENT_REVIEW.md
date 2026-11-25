# ADR-0162F — şirket içi ajan incelemesi ve dar bootstrap önerisi
Durum: PROPOSED_NOT_RATIFIED. Kaynak: CEO-AGENT-REVIEW-0162F; 0151 T01 zarfı; AUTH-PREP-0162B; SCOPE-0162E-UI-04-05. Yeni karar mevcut normu sessizce değiştirmez.

## İki farklı kabul sınıfı
A. Teknik inceleme: Engineer kaynak üretir, Research gereksinim doğrular, QA olumsuz/olumlu oracle ve test hazırlığı, Security kapsam ve politika incelemesi, IV Agent bağımsız kanıt değerlendirmesi. Agent review = teknik delil, gerçek doğal kişi veya mevcut T06 makbuzu değil.
B. Normatif kabul: mevcut gerçek bağımsız makam koşulu geçerli; yetkili normatif değişiklik olmadan T01 etkin değil. Öneri: yalnız sentetik, salt-okunur UI-04/05 bootstrap dilimi için H01 kontrollü geçici istisna; gerçek güvenlik kabulü, T02/T03/04/T09, üretim, ödeme, dış etki ve canlı veri ayrı. H01 tek insan CEO; başka insan kadrosu varsayılmaz. İstisna ancak geçerli yetkili normatif değişiklik ve sınırlandırılmış grant ile etkinleşebilir.

## Ajan ayrılığı
Engineer source write sadece izinli kapsam; QA ve Security read-only review, IV ayrı principal ve ayrı custody; Orchestrator planlar, imza yetkisi veremez. Policy Gateway fail closed. IV üretici kanıtından bağımsız olarak kaynak/digest ve policy epoch kontrol eder. Ayrı isim/istem tek başına bağımsızlık değildir; ayrı yürütme, erişim, değişmez kanıt ve doğrulanmış kimlik gerekir. Tek ChatGPT yanıtı gerçek bağımsız çok ajan çalışması değildir. Henüz ajan runtime etkin değil.

## Önerilen bootstrap kapsamı
0162E SCOPE_0162E.json'daki dört kaynak hedefi, R8 manifesti ve tam aday hash'leri; yalnız offline synthetic UI, üç ekleme + bir değiştirme; gerçek uygulama etkileşimi yok. Kaynak manifesti güncellemesi yetkide açıkça belirtilmeli. Backend, API, DB, schema, dependency, provider, CI, DEV, TEST, main ve PROD kapsam dışı. İstisna için grant subject, exact scope digest, validity, revoke, bağımsız teknik review ve POST sınırı gerekir; herhangi bir hash/policy mismatch STOP. Uygulanması için mevcut normatif makam yetki ve değişiklik prosedürünü çözmeli. Gerçek bağımsız F0 kabulü bu tasarım ile verilmez.

## Sonraki adım
H01 bu dar bootstrap önerisini ayrı kapsamlı normatif değişiklik talebi olarak açıkça seçebilir; mevcut bağımsız normatif makam şartı çözülmeden etkin sayılmaz. Sonra PRE teknik inceleme, gerçek kapsam yetkisi, izinli source patch, POST, ayrı repo ve yürütme kapıları. R8 değişmez; 0162-D 12 açık bulgu, 55/20 eşleme ve 42 oracle korunur.
