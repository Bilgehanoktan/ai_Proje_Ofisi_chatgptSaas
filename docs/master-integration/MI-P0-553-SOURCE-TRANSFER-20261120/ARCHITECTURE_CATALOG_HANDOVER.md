# AI Company OS — MI-P0 | 553 ürünü kanonik dala kontrollü taşıma adayı

**20 Kasım 2026 · MASTER INTEGRATION · SRC-ONLY + EXACT W8-PIN · DRAFT/NO-MERGE**

## Geliştirme kararı ve kaynak bütünlüğü
Kullanıcı, kalan engellerin kaldırılmasını ve 553 ürün dosyasının kanonik `integration/product-dev` dalına aktarılmasını açıkça istedi. Mevcut geniş `PR #14`, kaynak dışı 137 yolu da değiştirdiği için aynı Owner Design Master, handover ve W8 dokümanlarına kontrolsüz dokunma riski taşır. Ürün kaynakları yeniden geliştirilmedi; zaten birleşmiş `integration/mi-common-source-review-01@a80932b6d5e99667889dfaa25b682feb267c6cba` ürün Git ağacı baz ürüne **tek atomik Git tree değiştirme** ile ayrı inceleme commit'i olarak aktarıldı. Tam W8 ve sahiplik güvenlik kapıları henüz kapanmadığı için **product-dev'e merge/production yoktur**.

### Kaynak pinleri
| Kayıt | Hash | Açıklama |
|---|---|---|
| Kanonik gelişim tabanı | `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` | 505 dosya / 504 manifest girdi |
| Ortak kaynak parent | `a80932b6d5e99667889dfaa25b682feb267c6cba` | 553 dosya / 552 manifest girdi, PR12 kaynak-only merge |
| Transfer branch | `integration/mi-p0-553-product-only-20261120` | İki fast-forward inceleme commit'i |
| Kaynak snapshot commit | `f0c583ebf6e382f0bc7f0a2a253e99968938b384` | `product/` Git tree exact taşıma |
| W8 pin revizyon commit | `98808d280dda13088a2561ecc7323f4a910c380d` | yalnız `tests/integration/w8_unified_u3.py` |
| Transfer Git product tree | `f4cdcf68115917ab69ba6441414539fe32a59369` | ortak 553 adayla birebir |
| Transfer manifest Git blob | `27b4eb5816265d4e6e6d2458acb6220db7dd0c76` | 552 kaynak girişi |
| W8 adapter Git blob | `e1330a7c33f6c5d5c353a19b0be1ae1281fd0700` | mevcut owner W8 adaptörü + yeni manifest literal |

**GitHub diff:** 64 yol; `product/` altında 63 yol (48 added, 14 modified — manifest dahil, 1 rename) ve 1 `tests/integration/w8_unified_u3.py` (3 ek, 1 silinmiş satır). Diğer `docs/`, `handover/`, `decisions/`, `config/`, `infrastructure/`, `.github/` ve veri tabanı dizinleri değişmedi. PR15 teknik olarak GitHub'da clean / mergeable'dır; bu yalnız Git merge çatışmasının olmadığını ifade eder, runtime kabul değildir.

## Çözülen gerçek çakışma
Eski `product-dev` W8 runner'ında `MANIFEST=07f1fc...`, ortak repo runner'ında `MANIFEST=b80e...` tutuluyordu. Yeni 553 ürün manifestinin gerçek blob'u `27b4eb...`. Ortak source owner'ın `w8_unified_u3.py` sürümünü aynen alıp **yalnız manifest literalini** doğrulanmış 553 blob'uyla değiştirdik. Owner'ın eklediği `p24.HISTORICAL` izolasyon override'ı da korundu. Böylece **statik W8 pin kaynak uyuşmazlığı** giderildi. Fresh `prepare → install → test → smoke`, npm lock/wheelhouse, native tarayıcı ve son kaynak sürümü üzerinde tam W8 **NOT_RUN**; `PASS` ilan edilmez.

## Mevcut fonksiyonel kanıt ve kapsam
- PR #11 run [44628704044](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44628704044): 552/552 SHA256 byte, özgün ORG paketleme 4/4, özgün SQL 11/11 **gerçek CI PASS**. `D0 SQLite` kapsamıdır; yeni transfer branch'inde tekrar çalıştırılmadı, çift sayılmaz.
- PR #6 run [44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705): gerçek özgün Core–OperationsStore 10/10 D0; farklı pinned owner source ve daha dar test kapsamı.
- PR #4 run [44620987573](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620987573): sınırlı Next/SSE D0 tanısı, full 553 build veya native U3 değil.
- Memory Windows 160 supplement ve 183/184 SKIP gibi diğer hat verileri bu tur yeniden doğrulanıp orijinal `344/344` olarak sayılmaz.

## Teknik katalog / mimari
- `product/ai-company-os-backend/durable_ops.py`: `initialize_assignment_ops()`, `OperationsStore.record_assignment_review()`, `OperationsStore.assignment_review()` mevcut +41 D0-only satır. G9 kaynak sahibi kararı ayrıca gerekli.
- `product/ai-company-os-backend/assignment_lifecycle.py`, `assignment_review.sql`, `schema.sql`, `operations.sql`: mevcut ORG adaylarının eklenmesi; gerçek PostgreSQL migration/ROL/owner grants uygulanmadı. API/DB/event/bağımlılık uyumu kanıtlanmış kabul edilmez.
- `product/ai-company-os-backend/app/core/transaction/intent_authority.py`: G2 varyant blob `b28788f46a39c282d79d29c4abd817ed5fc9de99` ile ortak D0 blob `fa47acd32adb309896f762ec50e47bf26641adbb` farklıdır. Tek doğru implementasyon seçilmedi; bağımsız root/issuer/custody/sink uygulanmadı.
- Semboller, sahipler ve tüm 64 dosya yolu [TECHNICAL_CATALOG.json](TECHNICAL_CATALOG.json) belgesindedir. Katman, eski kararlar ve sekiz fazlı yol haritası değiştirilmedi.

## Kanonik kapanış kapıları
1. MI-01 Unified/W8 owner'ın exact 553 checkout + native W8 source/dependency lock review; **full prepare/install/test/smoke** PASS.
2. MI-03/06 G9/ORG 41 satırlık ek sürüm ve MI-02/04 G2 IAM authority varyantı sahibinin imzalı sözleşme kararı; özgün G2 50, G9 7, 0214 Memory–T1 10 testleri.
3. Strict PostgreSQL owner/RLS gerçek izinli testleri; restore sonrası replay/fencing; bağımsız Option A root/claim authority ve effect-sink idempotency, IV ve sekiz güvenlik negatif testi. Bu gerçek işlem ve kabul kapıları kapatılmadan `authoritative=true`, COMMIT, dış etki veya PROD yok.

**Bu tur kapanan:** 553 kaynak taşıma hazırlığı, geniş PR14 non-product çakışma riski ve exact W8 manifest pin tutarsızlığı. **Bu tur kapanmayan:** W8 full, owner variant, real issuer, PG, IV. PR15 review candidate kalır; kabul yok.

## Geliştirme/ürün kabul çizelgesi
15/35/20/20/10 ölçümünde 10 grubun owner-ratified kriter paydası yok; önceki/güncel global **HESAPLANAMADI**, delta belirlenemez. Core **12/16→12/16**, Premium UI **21/40→21/40**, MVP **0/11→0/11**, bağımsız güvenlik **0/7→0/7**, delta **0 puan**. Aynı 15 eski ORG testi iki kere sayılmaz. Kanonik 505 kaynak dalında değişiklik yoktur, yalnız ayrı transfer adayı hazırlanmıştır.

## Bakım, hata ayıklama, geri dönüş ve sonraki görev
- **Manifest/checkouts:** PR15 `product` subtree `f4cdcf...` ve `product/SOURCE_MANIFEST.json` `27b4...` kimliklerini GitHub compare / branch Git tree ile tekrar kontrol et. Fark çıkarsa STOP/HOLD.
- **W8:** `w8_unified_u3.py` içindeki MANIFEST literalini gerçek manifest Git blob ile karşılaştır. Eşleşse bile `w8_p10j23.py`, `w8_p10j24.py`, historical pin ve native browser sonuçları tam koşulmadan ACCEPT yok.
- **SQL/IAM:** Old DB+pin restore güvenlik açığı mevcut; sentetik SQLite PASS bağımsız doğrulama değildir. NO production grants.
- **Rollback:** PR15 birleştirilmeden kapatılabilir; eğer ayrı owner+W8 onayıyla ileride birleştirilirse `98808d28` ve `f0c583eb` normal revert edilir. `integration/product-dev` başlangıç `8a3b05a...`; `main` değişmedi. Force push ve eski owner dalın üzerine yazma yok.
- **Sıradaki gerçek adım:** PR15 kapsamında MI01/W8 onaylı tam kaynak/doğal tarayıcı kanıtını almak ve G9/G2 owner kararını bağlamak; sonra kanonik kaynak aktarımı için otomatik olmayan, sahipçe incelenmiş karar.

[PR #15](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/15) · [PR #14 (geniş, aynı kaynak)](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/14) · [EVIDENCE.json](EVIDENCE.json).
