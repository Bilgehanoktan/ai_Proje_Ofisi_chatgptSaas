# MI-P0 553 → 565 — bağımsız sahip adayları manifest ve sürüm kapısı

## Ne / neden / nerede / nasıl
Bu tur, **özgün GitHub sürüm başlıklarından** PR19, PR26, PR22 ve PR20 kaynak listelerini karşılaştırdı. Ürün üzerinde değişiklik yapmadan kaynak çakışması ve W8 sürüm sabitleme riskini belirledi. 553 kanonik sürümden 562, 555 ve Office adaylarına ait yol/hashes kullanıldı. Elde edilen olgular `EVIDENCE.json` içinde; **565 yalnızca beklenen dosya sayısı, maddi birleştirme ya da sürüm değildir**.

## Aktif tek-yazıcı sahipliği ve değişiklik kapsamı
| Hat / PR | Ürün eklenen | Değişen | Güven sınırı |
| --- | ---: | ---: | --- |
| MI04 G2/G9 #19 | 9 | 1 (intent_authority.py) | D0 72/72, issuer güveni / owner HOLD |
| D0 Admission/Outbox/Task-Budget #26 | 2 | 3 API route.ts | 60/60 seçili, full W8 HOLD |
| MI05 Office #22 | 1 | 1 route.ts | 37/37 seçili, owner/browser HOLD |
| MI01 W8 #20 | 0 | W8 adapter (product dışı) | 553 hash pin, C04-C08 NOT_RUN |

Bu üç ürün adayı arasında **aynı ürün kaynak yoluna dokunma çakışması yok**. Bu durum sözleşme/bağımlılık uyumluluğu, bağımsız kabul, güvenlik veya dosyaların birleşik testten geçtiğini kanıtlamaz. Hepsinin bağlandığı ortak `product/SOURCE_MANIFEST.json` için **tek sahipli kaynak onayından sonra tek yeniden üretim** gerekir. PR22 kendi dalında manifesti yeniden yazmaz; ayrı bir rebind önerisi sunar.

## Kanıtlanmış kontrol
- GitHub'dan geri okunan manifest blobları: kanonik `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`, G2/G9 `566b7210b6edb95a21b999dc1d881a12284d9011`, proxy `56086553c3946d16a728bfaea877b3908fe96232`. Office önerisi `3674a309f2975c5edaebf30308a97269dc879220`; W8 adapter `b4043035e75c5a18b7b19a9f18eecfef8e8fe677`.
- **11/11 salt-okunur gerçek kaynak karşılaştırma koşulu sağlandı.** Yerel ürün kodu/Next.js derlemesi/entegrasyon regresyonu çalıştırılmadı.
- Üç sahip kaynağının yol kümelerinden beklenen tek birleşik ağaç **553 + 9 + 2 + 1 = 565 ürün dosyası**, **564 manifest girdisi**, +12 yeni ve 5 mevcut ürün yolu değişikliği; henüz oluşturulmadı, kaynak hash'i hesaplanmadı.
- Mevcut W8 sabit pin 553'e işaret eder. 562, 555 veya olası 565'e olduğu gibi uygulanırsa mevcut fail-closed denetim **HOLD** verir. Pin kendiliğinden değiştirilemez.

## Mimari / teknik katalog
Etkilenen bileşenler: `backend/app/core/transaction/intent_authority.py` (A güven kökeni tasarım sınırı), dokuz yeni IAM/ORG kaynak ve test dosyası, `frontend/app/api/demo/admission|outbox|task-budget|office-workbench/route.ts`, `frontend/features/mvp/readBoundedD0Json.ts` ve yeni iki test dosyası. Bunlar **yalnızca kaynak adaylarına aittir**; API rota isimleri korunur, gerçek sözleşme/DB/event/schema/dependency değişikliği bu turda yapılmadı. Yeni fonksiyon, sınıf, test veya dış çağrı eklenmedi.

## Çakışmasız iş sırası ve kabul
1. MI01 #20: kaynak/donanım/bağımlılık tam C04, C05 bağımsız değerlendirme, ardından C06-C08 orijinal 553 kurulum/build/tarayıcı testi.
2. MI04 #19: güvenilir root/issuer/sink ve G2/G9 sürümünün onayı; PR24'ün özgün yedi G7 testini mevcut ORG okuyucusuyla yetkili tam checkout'ta çalıştırma.
3. MI05 #22 ve D0 #26: ayrı sahip onayları; **aynı sabit kaynak tabanı** üzerinden değişikliklerin ve özgün sözleşmelerin incelemesi.
4. Yalnız bunlar tamamlanınca planlanan yeni manifest ve W8 pinini gerçek kaynak ağacından üret, yeniden özgün tüm W8/test/regresyon/PG/IV çalıştır.
5. Korumalı PostgreSQL geri yükleme, bağımsız güvenlik testleri, MVP ve H01 ürün kabulü ayrıca HOLD kalır.

## İlerleme, test ve geri dönüş
Ağırlık 15/35/20/20/10, onaylı payda 0/10; **genel geliştirme yüzdesi HESAPLANAMADI**. W8 3/8, Core 12/16, UI 21/40, MVP 0/11, IV 0/7; kabul delta 0. Kanıt türü: GitHub kaynak-okuma ve statik yol kontrolü (11/11), değil runtime PASS. Mevcut GitHub Actions istisnaları ve yetki sınırları değiştirilmedi. Arıza tanısı: manifest/pin uyuşmazlığında dosya hashini değiştirmek yerine hangi bağımsız adayın eklenmediğini `EVIDENCE.json` ile karşılaştır. Geri dönüş: yalnız bu izole PR'yi kapat veya normal revert uygula; PR19/20/22/26, kanonik `product-dev`, `main`, gerçek yetkiler ve kayıtlar aynen kalır.

## Handover
Merkezi görev: kaynak sahiplerinin onayını ve W8 gerçek C04-C08 çalışmasını izlemek; 565'i teslim edilmiş ürün kabul etmemek. Bu belge PR25 release-gate kaynaklarının yerine geçmez ve onların kriterlerini değiştirmez. Tek ürün birleştirme kararı ve güvenlik kabulü verilmemiştir.
