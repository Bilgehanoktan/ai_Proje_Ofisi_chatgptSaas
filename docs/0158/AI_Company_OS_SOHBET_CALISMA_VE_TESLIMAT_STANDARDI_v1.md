# AI Company OS — Sohbet Çalışma, Teslimat ve Devir Standardı

**Belge ID:** SOP-CHAT-001 · **Sürüm:** 1.0 · **Tarih:** 14 Kasım 2026  
**Nitelik:** Proje çalışma talimatı ve tekrar kullanılabilir teslimat şablonu. Normatif güvenlik ratifikasyonu veya yürütme yetkisi değildir.  
**Amaç:** Her yeni sohbetin son doğrulanmış mimari, kaynak kodu ve teknik katalog üzerinden devam etmesini; yapılan her değişikliğin izlenebilmesini; sonraki adımın mimari bağımlılıklardan çıkarılmasını sağlamak.

## 1. Yeni sohbete başlangıç talimatı

Bu belgeyi her yeni sohbetin başında oku. Aynı proje içinde bulunmak, önceki dosyaların erişilebilir olduğunu veya geçmiş yetkilerin etkinleştiğini kanıtlamaz. Bu standart kalıcı çalışma yöntemidir; güncel sürümler ve açık işler ayrı `AI_Company_OS_GUNCEL_DEVIR_KAYDI.md` dosyasında tutulur. Bu iki belgeyi birlikte kullan. Kullanıcı yalnızca “devam et” derse, son doğrulanmış iş sırasından devam et; cevaplanmış tercihleri yeniden sorma.

### Okunacak asgari kaynaklar

| Sıra | Kaynak | Kullanım |
|---|---|---|
| 1 | Bu çalışma standardı | İşleyiş ve çıktı biçimi |
| 2 | Güncel devir kaydı | Son tur, sürüm, engel ve sıradaki işler |
| 3 | Son doğrulanmış tam Design Master + varsa yeni revizyon ekleri | Kanonik hedef, kararlar, güvenlik, görev bağımlılıkları |
| 4 | Son kaynak ZIP ve sonraki ayrı ekler | Gerçek dosya, sembol, API ve değişiklik incelemesi |
| 5 | Teknik katalog MD/JSON, manifest, karar ve kanıt defterleri | Bakım, etki analizi, genişletme, teşhis |
| 6 | Kullanıcının bu turdaki açık talebi | Kapsam ve varsa yeni karar |

Özet, eski sohbet yanıtı veya dosya adı, dosyanın özgün içeriği yerine geçmez. Dosya erişimini, manifesti, SHA-256 değerlerini ve önceki master ile tam koruma ilişkisini mümkün olduğunda doğrula. Uyuşmazlık varsa `BASELINE_GAP` / `PROVENANCE_HOLD` olarak kaydet. Son tam kaynak bulunmuyorsa mevcut ekleri üzerine yazma; sadece yetki içinde yapılabilecek bağımsız inceleme veya ayrı ek hazırlığı yap. Bütünleştirilmiş sürüm üretildiğini iddia etme. Eksik dosyanın adını ve neden gerekli olduğunu belirt.

## 2. Karar ve yetki kuralları

- Hedef tasarım, kullanıcı kararı, normatif ratifikasyon, kaynak adayı, gerçek uygulama, gerçek TEST ve üretim kabulü ayrı durumlardır. Birinden diğerine otomatik geçiş yoktur.
- H01 tek insan CEO; Orchestrator operasyonel yönetici; Research, Engineer, QA çekirdek roller; IV ayrı doğrulama bileşeni. Codex ve Antigravity geliştirme yardımcılarıdır; şirketin runtime çalışanı veya bağımsız imzacı değildir.
- CODE, REPO, DEV ayrı grant; gerçek TEST, PROD, harcama, müşteri, dış işlem, F0/Security, freeze ve snapshot ayrıca değerlendirilir. Önceki şartları kaldırmadan yeni kapsam varsayma. Eksik bağımsız insan makbuzu, AI tarafından oluşturulamaz.
- Son devirdeki kararlar kaynaktan doğrulanır; eski bir durum kaydı yeni açık ve geçerli kararın yerine geçmez. Çelişki varsa kaynak ve otoriteyi göster, etkilenen işi HOLD tut.
- `NOT_RUN`, `HOLD`, `UNKNOWN`, `NULL` değerlerini gerçek PASS veya sıfır risk olarak sunma. Kaynak yazmak, build yapmak ve işlevi test etmek farklı faaliyetlerdir. Kaynak adayını resmî kodlama izni, çalışan ürün veya istisna olarak gösterme.
- Resmi yetki yoksa repo açma, kurulum, komutla ürün çalıştırma, build, gerçek test, model/araç çağrısı veya dış mutasyon yapma. İzin kapsamını genişletmek için belgeyi kullanma. Statik belge/manifest doğrulamasının sınırını açıkça belirt.

## 3. Her turun çalışma algoritması

1. **Devir doğrulaması:** Erişilen dosyalar, sürümler, hash ve gerçek/koşullu yetki durumunu belirle. Önceki açık işleri ve kararları koru.
2. **Mimari eşleme:** Talebi D01–D21, 63 alt modül, ilgili KS/NS sözleşmesi, v130 genel kartları ve v135 UI/BE/QA/OPS kartlarına bağla. Doğrudan eşleme bulunmazsa yeni aday kayıt olarak işaretle; kaynak ID uydurma.
3. **Öncelik:** Mevcut DAG, güvenlik kapıları ve ilk P0 teslimat ölçütünden kritik yolu çıkar. Bağımsız ve izinli işleri W1–W8 hatlarında birlikte planla; bağımlılıkları atlama.
4. **İşlem:** Yalnız etkin kapsamda iş yap. Her değişiklik için eski/yeni kaynak, gerekçe, yöntem, güvenlik ve geriye uyumluluk etkisini kaydet. İş tamamlanamazsa somut kısmi sonuç ve kalan engeli göster.
5. **Doğrulama:** Gerçekten yapılan kontrolleri ayrı yaz; dosya bütünlüğü, statik inceleme, build ve gerçek TEST sonuçlarını ayır. Test izni yoksa oracle hazırla, `NOT_RUN` olarak bırak. Kanıt olmadan görev kapatma.
6. **Teslimat:** Kaynak paketi, master veya doğrulanmış tabana bağlı ek, teknik katalog, değişiklik geçmişi, test/kanıt defteri ve bütünlük raporunu güncelle. Değişmeyen tarihsel kaynakları koru.
7. **Sonraki adım:** Güncel mimarinin başlık/çapa/satır/kart referanslarıyla gerekçelendir. Zorunlu bağımlılık, paralel işler, beklenen çıktı, kabul ölçütü, STOP koşulu ve gerekiyorsa H01 kararını yaz.
8. **Devir:** Aşağıdaki kullanıcı raporunu tamamla; ardından güncel devir dosyasını yeni gerçek durumla doldur, önceki devir kaydının sürümünü/hash'ini koru. Yapılmamış gelecekteki işi yapılmış gibi yazma.

## 4. Sabit sekiz çalışma hattı

| Hat | Alan | Bağımlılık ve sınır |
|---|---|---|
| W1 | Frontend, CEO, Office Engine | Snapshot/seq/layout, UI-01..15; görsel veri gerçek otorite değildir |
| W2 | API ve ortak sözleşmeler | Tek kaynak, FE tüketici pini, 16 KS/NS ile uzlaşma |
| W3 | Orchestrator, Runtime, DAG, organizasyon | Admission, lease, T1 ve yetki bağları |
| W4 | Güvenlik, PEP, W-A, altyapı, Event Store | T1/restore/fencing, bağımsız kabul, fail-closed |
| W5 | Skill, bilgi, hafıza ve model adaptörleri | Karantina, provenance, F0, CAT-B |
| W6 | Research, Excel W1, Obligation, IV | QA/IV/release ayrımı, ürün ve veri kabulü |
| W7 | SaaS, finans, tenant ve büyüme | Tenant/company kapsamı; gelir/tahsilat ayrı; gerçek dış etki ayrı |
| W8 | QA, entegrasyon, teknik katalog | Oracle, gerçek kanıt, kaynak bütünlüğü, geri dönüş |

Her turda sekiz hat için ayrı durum göster; gerçekten ilerlemeyen hatta `UNCHANGED` yaz. Paralel planlama, gerçek paralel ajan çalıştırıldığı anlamına gelmez.

## 5. Kullanıcıya her sohbet sonunda verilecek zorunlu rapor biçimi

Aşağıdaki başlıkları kullan. İçerik, turun gerçek kapsamına göre doldurulur. Boş alanları atlama; `UYGULANMADI`, `UNKNOWN` veya `NOT_APPLICABLE` ile açıkla. Yüzde veya sayıları ancak pay/payda tanımı ve doğrulanmış veri varsa kullan.

### A — Sürüm ve kısa sonuç
- Tarih / tur ID / kaynak master / yeni master ya da ek / kaynak ürün / yeni ürün / katalog sürümü.
- Yapılan işin düzeyi: `DOCUMENT_ONLY`, `SOURCE_CANDIDATE`, `AUTHORIZED_IMPLEMENTATION`, `BUILD_RUN`, `REAL_TEST_RUN` (kanıta göre; birbirinin yerine geçmez).
- En önemli somut sonuç, çözülmeyen ana engel ve kullanıcıya teslim edilen dosyalar.

### B — Mimari ve görev karşılığı
| Alan / modül | Kaynak çapa, satır veya kart | Yapılan | Durum | Kabul kanıtı / eksik |
|---|---|---|---|---|
| [Dxx / modül] | [master sürümü + referans] | [somut çıktı] | [statü] | [gerçek makbuz ya da NULL] |

### C — W1–W8 paralel ilerleme
| Hat | Önceki durum | Bu tur | Son durum | Bağımlılık / sonraki iş |
|---|---|---|---|---|
| W1 | ... | ... | ... | ... |
| W2 | ... | ... | ... | ... |
| W3 | ... | ... | ... | ... |
| W4 | ... | ... | ... | ... |
| W5 | ... | ... | ... | ... |
| W6 | ... | ... | ... | ... |
| W7 | ... | ... | ... | ... |
| W8 | ... | ... | ... | ... |

### D — Teknik değişiklik ve bakım kayıtları
| CHG-ID | Dosya / sembol / satır | Ne, neden, nasıl | Bağımlılık ve etki | Arıza / genişletme / rollback |
|---|---|---|---|---|
| [ID] | [path::symbol] | [açıklama] | [etkilenen sözleşme] | [teşhis sırası, güvenli geri dönüş] |

### E — Doğrulama, güvenlik ve gerçek ilerleme
| Kontrol / test | Beklenen | Gerçek işlem ve sonuç | Kanıt | Açık |
|---|---|---|---|---|
| [ID] | [oracle] | [NOT_RUN veya gözlenen] | [ref / NULL] | [evet/hayır] |

Etkin CODE/REPO/DEV, C01–C24, F0–F4, F0 makbuzları, NEG, UX135, JOB, R27, FZ ve H01 imzalarını son doğrulanmış durumlarıyla göster. Değişmeyen sayaçları yeniden kanıtlanmış gibi sunma. Kaynak hash ile ürün TEST PASS'i ayrıdır.

### F — Açık işler ve kritik yol
| Öncelik | Açık iş / engel | Neyi engelliyor | Gerekli gerçek kaynak veya kabul | Durum |
|---|---|---|---|---|
| P0 | ... | ... | ... | HOLD / UNKNOWN |

### G — Mimariye göre sıradaki adım (zorunlu son bölüm)
| Sıra | İş / kart | Mimari gerekçe (master + çapa/satır) | Önkoşul | Somut çıktı | Kabul / STOP |
|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... |

**Kritik yol:** [önkoşul → iş → kabul]. **Paralel işler:** [yalnız izinli ve bağımsız işler]. **H01 kararı:** [gerekmiyor / gerekli yeni karar ve seçenekler / bağımsız makam gerektiriyor]. **Bir sonraki sohbetin ilk görevi:** [tek somut adım]. Eski önerileri otomatik tekrar etme; son gerçek gelişmeye göre yeniden hesapla.

## 6. Her teslimatta tutulacak teknik kayıtlar

| Dosya veya bölüm | İçerik |
|---|---|
| `ARCHITECTURE.md` / Design Master | D01–D21, modüller, kararlar, kaynak çapaları; tarihsel bütünlük |
| `CHANGELOG.md` | Önceki/sonraki sürüm, eklenen/değişen/silinen dosya, CHG-ID |
| `CODE_CATALOG.json` | Dosya hash, sınıf/fonksiyon, satır, import, kaynak sürüm |
| `MODULE_CATALOG.md` | Modül rolü, giriş/çıkış, sahiplik, bağlı domain/kart |
| `API_CATALOG.md` | Endpoint, schema, scope, ret, yetki, gerçek doğrulama durumu |
| `DATABASE_CATALOG.md` | Tablolar, FK, migration, T1, RLS, outbox, restore; yoksa açık eksik |
| `DEPENDENCY_MAP.md` | Modüller ve FE/BE sözleşme pinleri, ters bağımlılıklar |
| `DECISION_LOG.md` | Karar ID, kullanıcı seçimi / aday / normatif durum, neden, alternatif, ret |
| `TROUBLESHOOTING.md` | Belirti, hipotez, dosya/fonksiyon, teşhis, güvenli çözüm, oracle |
| `EXTENSION_GUIDE.md` | Yeni ajan, departman, kat, beceri, WorkType veya event etki analizi |
| `KNOWN_ISSUES.md` | Gerçek gözlem ile tahmini risk ayrımı, etki, sahip, engel |
| `TEST_EVIDENCE.md` | Oracle, gerçek koşum, sonuç, kanıt; NOT_RUN ayrımı |
| `ROLLBACK_GUIDE.md` | Önceki digest, pairing, veri uyumu, restore sonrası revoke/epoch; gerçek restore iddiası yok |
| `SOURCE_MANIFEST.json` | Gerçek kaynak byte/hash ve ZIP doğrulaması |
| `AI_Company_OS_GUNCEL_DEVIR_KAYDI.md` | Son durum ve mimariye bağlı sonraki işler |

Bu isimler hedef kayıt standardıdır; tamamının fiziksel olarak önceden oluştuğu anlamına gelmez. Mevcut belgelerde eşdeğer bölüm varsa bağlantısını koru. Her turda değişen kayıtları güncelle; eski içeriği silme; eksikleri görünür tut. Kaynak paketi üzerinde gerçekten yapılan ekleme/değişiklikleri diff ile çıkar; kaynak bulunmuyorsa yalnız ek kayıt üret.

**CHG kaydının asgari alanları:** change_id, önceki/yeni sürüm, H01 talebi/karar, domain/task_id, source_ref/digest, path/symbol/line, old/new hash, ne/neden/nasıl, alternatif, giriş/çıkış, hata, dependency, güvenlik etkisi, test oracle, gerçek sonuç/kanıt, bilinen açık, genişletme, rollback, reviewer/receipt, supersedes. Bilinmeyen alanlar NULL; imza, commit, test veya tarih uydurulmaz.

## 7. Güncel devir dosyası — her turda güncellenecek şablon

`AI_Company_OS_GUNCEL_DEVIR_KAYDI.md` dosyasında bu alanlar bulunmalıdır:

1. Tur kimliği ve tarih; çalışma standardı sürümü; önceki devir dosyası/digest.
2. Kaynak matrisi: hedef master, son tam doğrulanmış master, sonraki ekler, kaynak ZIP, katalog MD/JSON, manifest; her biri `VERIFIED`, `AVAILABLE_UNVERIFIED`, `MISSING` veya `REPORTED_ONLY`; gerçek SHA-256 varsa yaz.
3. H01 kararları ve etkin grant durumu; açık güvenlik/bağımsız kabul; gerçek sayaçlar ve kaynakları.
4. Son turda yapılan gerçek faaliyetler; çıktı yolları, değişiklik ID'leri, mimari/kart eşlemesi; yapılmayanlar.
5. W1–W8 durumları ve açık bağımlılıklar; kritik yol.
6. Mimariye dayalı sonraki iş tablosu: sıra, kart/domain, master referansı, önkoşul, çıktı, kabul/STOP; paralel işler ve H01 gereksinimi.
7. Eksik dosyalar, bilinen kusurlar, bağımsız kabul borçları, güvenli geri dönüş, bir sonraki sohbetin ilk işlemi.

## 8. Yeni sohbet açarken gönderilecek kısa mesaj

> AI Company OS projesine kaldığımız yerden devam et. Yüklediğim SOP-CHAT-001 çalışma standardını, güncel devir kaydını, son doğrulanmış Design Master'ı, kaynak paketini ve teknik kataloğu önce incele. Eksik kaynak veya yetkiyi varsayma. Mimari bağımlılıklara göre izinli işleri ilerlet. Her turda yapılanları, teknik değişiklikleri, gerçek test/kanıt durumunu ve sonraki adımı standart A–G raporuyla ver; güncel devir kaydını ve etkilenen katalogları güncelle. Önceki kararlarımı yeniden sorma, yeni karar gerekmiyorsa doğrudan ilerle.

## 9. Kaynak ve kapsam

Bu çalışma standardı kullanıcının her sohbet için mimariye dayalı sonraki adım ve sürekli teknik katalog talebini somutlaştırır. v135 §07–§12 (özellikle L164–217) uygulama kapıları ve backlog; DOC-REV-0143 ekinin entegrasyon ve katalog hükümleri kaynak referanslarıdır. Güncel sürüm/sayaçlar bu sabit belgeye gömülmez; güncel devir kaydında tutulur. Projede kalıcı hafıza kapalı olduğundan belge her yeni sohbette erişilebilir tutulmalıdır. Bu dosya v142'ye fiziksel olarak eklenmedi: v142'nin özgün dosyası bu oturumda yoktur. Birleştirme yapılınca bu standardı ve değişiklik kaydını kaynağa referansla ekle; hiçbir güvenlik yetkisini değiştirme.
