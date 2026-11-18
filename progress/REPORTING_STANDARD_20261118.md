# AI Company OS — Ortak ilerleme raporlama standardı (2026-11-18)
Kullanıcı talebi: önceki turda önerilen geliştirme/kabul ayrımını bütün AI Company OS sohbetlerine yaymak. Bu kayıt raporlama içindir; kaynak, güvenlik, yetki veya kabul politikası değişikliği değildir.

## Üç ayrı ölçüm
1. **Geliştirme ilerlemesi (yeni)**: tasarım %15, kaynak %35, fonksiyonel test %20, bütünleşik entegrasyon %20, nihai kabul %10. Her hat için sürümlü iş paketi ve önceden tanımlı kanıt kriteri gerekir. Her aşamada tamamlanan kriter / toplam kriter oranı alınır, ağırlıkla çarpılır. Kriterler eşit ağırlıklıdır; farklı ağırlık gerekirse önceden açıkça kaydedilir. Payda bilinmiyorsa HESAPLANAMADI; tahmin veya önceki ordinal puan dönüştürmesi yok. Tasarım/kaynak/yerel test kazanımları ilgili aşamada görünür; fixture yalnız kendi tanımlı kapsamını karşılar. Entegrasyon ve kabul için ayrı kanıt gerekir. Örtüşen kriter ve testleri iki kere sayma; yeni kapsam veya yeniden açılan kusur yüzdeleri değiştirebilir, önceki payda ve gerekçe korunur.
2. **Ürün kabulü (mevcut)**: kanonik kriterlerin tamamlanan/toplam oranı, örn. Core 12/16. UI, ORG, MVP, bağımsız güvenlik kendi ayrı kapsamlarında kalır. Bunların ortalaması tüm sistem yüzdesi değildir.
3. **24 alan olgunluğu (mevcut)**: TRACK-0227 ve haleflerindeki ordinal tasarım/kaynak puanları 0/25/50/75/100. Bu puanlar yüzde veya ETA değildir; eski rubric korunur. Yeni geliştirme yüzdesine otomatik dönüştürme yok.

## Her geliştirme turunda
- Başlangıçta güncel Design Master, uygulama planı, tracker, dal sahiplikleri ve kanıtları denetle; ortak standardı oku.
- Her hat için sabit kriter kimlikleri, önceki ve yeni pay/payda, ağırlıklı geliştirme yüzdesi (hesaplanabiliyorsa), kanonik kabul oranı, delta, kaynak commit, kanıt türü, engel, sorumlu hat ve sonraki gerçek ürün aksiyonu göster.
- PASS, NOT_RUN, HOLD, tarihsel/aktarılan, sentetik, bağımsız kabul ve tekrar koşumları ayır. Test sayısının artışı tek başına yüzde artışı değildir.
- Paralel hatları çakıştırma, aynı işi ikinci kez başlatma. Mevcut kaynak adaylarını yetkili izole dalda entegrasyona taşı; sadece gerçek eksik için yeni prototip aç. Açık test/build/entegrasyon engellerini önceliklendir; gerçek izin yoksa HOLD.
- Tek ortak sürümlü kayıt kullan; hatların kendi delta raporları referanslanır, çakışan sayılar uzlaştırılmadan birleşik toplam üretilmez. Genel proje yüzdesi için tüm hatların sabit kapsamı ve hat ağırlıkları ayrıca belirlenmelidir.
- Teknik katalog, mimari eki, devir ve bakım/rollback kayıtlarını koru. CEO-0174/0179=B ve bağımsız kabul, main merge, CI, gerçek yetkiler, harcama, dış etkiler, müşteri verisi, PROD sınırları aynen geçerli.

## Başlangıç referansı
0227 Core entegrasyonu 12/16 (%75), yalnız kendi kanonik kriter seti. TRACK-0227 24 alan rubric ve puanları değişmedi. Yeni metrik için hat başına kriter tabanı çıkarılmadı; bu kayıt yüzdeleri geriye dönük yükseltmez. Diğer hatların güncel kabul durumunu kendi sürümlü kaydından oku. Bir sonraki her hat turunda kendi kapsamını ve kriter tabanını çıkarıp deltasını raporla.

## Yayılım ve geri dönüş
Bu dosya ve JSON, ayrı raporlama dalında ortak referanstır. Kullanıcı proje talimatlarına referansı eklediğinde mevcut ve yeni proje sohbetleri aynı standardı kullanabilir; diğer sohbetlere otomatik mesaj gönderilmedi. Ana dal veya ürün dalları birleştirilmedi. Geri dönüş: raporlama standardı referansını kaldır; eski kanonik dosyalar aynen korunur.
