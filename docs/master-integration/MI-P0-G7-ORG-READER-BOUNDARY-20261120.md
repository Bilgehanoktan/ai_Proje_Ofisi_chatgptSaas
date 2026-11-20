# AI Company OS — CTL-01 / G7 tarihsel ORG okuyucu sınırı ve PR6 durum düzeltmesi
Tarih: 2026-11-20 | Durum: TAMAMLANAN BAĞIMSIZ KAYNAK DENETİMİ / **ÜRÜN KABULÜ DEĞİL**

## Neden / kaynak sabitleme
- Kanonik ürün: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` (**553 ürün dosyası**, 552 manifest).
- G2/G9 izole PR19: `0a8907f177bb3e9b458aefb3ea3441b15537f542`; özgün CI checkout `93e6c84db1a061ee914aa2c1d543620404515c0b`; 562 ürün dosyası, 561 manifest.
- CI #44700495037: G2 50/50 + ORG 15/15 + G7 7/7 = **72/72 özgün D0 seçili test yürütmesi**, daha önce bildirilmiş kanıt; **bu turda yeniden yürütülmedi**.
- W8 PR20 `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542` 553 manifestine sabitli; PR19 562 manifesti ile kontrolsüz birleştirme `U3_MANIFEST_HOLD`.

## Bu turda ne yapıldı?
1. PR19 gerçek workflow başlığından ve özgün G7 test kaynağından **gerçek yedi vakayı** belirledik: `candidates/D5-G7/test_checkout.py::ActualReadbackTests`.
2. Exact GitHub bloblarına dayalı **9/9 statik kaynak denetimi** yapıldı. Bu test çalıştırma, Python import veya gerçek PostgreSQL doğrulaması değildir.
3. G7 özgün 7'nin *gerçek* geçici SQLite Core, ORG-05R3 `OperationsStore` ve D0SessionResolver kullandığı; `read_current_org_reference` ve `inspect_core_org_session_reference` orijinal modüllerinin çağrıldığı doğrulandı. Yedi vakayı `product/.../tests/test_core_org_session_sqlite_d5g7.py` içindeki stub/patch kullanan **ayrı testlerle karıştırma**.
4. G7 runner `candidates/ORG-05R3` ve `candidates/ORG-06` yollarını Python import listesine ekliyor. ORG-06 fixture, ORG-05R3 tarihsel `durable_ops.py` kullanıyor; bu, **güncel ürünün genişletilmiş** `durable_ops.py` sınıfıyla ayrıca koşum kanıtı değildir.
5. Tarihsel `durable_ops.py` Git blob `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` (161 gerçek kod satırı, son newline hariç), güncel ürün karşılığı `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` (202 satır). Kaynak satırlarının deterministik sırayla karşılaştırılması: **161/161 eski satır korundu; 41 ek satır; 0 eski satır silme/değiştirme**; eklenen kümeler satır 25 ve 151 dolaylarında. Bu yalnız kaynak uyumluluğudur, çalışma zamanı/sahiplik kabulü değildir.
6. Başarılı özgün PR6 Core–OperationsStore CI #44620141705 (10/10 D0) nedeniyle GitHub PR #6 başlığındaki tarihsel `NOT_RUN` yanlış güncel durum düzeltildi. PR açık/draft; eski başarısız staging denemesi gövde içinde tarihsel olarak korundu.

## Teknik katalog deltası
| Özgün kaynak | Sorumluluk | İlgili Git blob / sınır |
|---|---|---|
| `candidates/D5-G7/test_checkout.py` | Gerçek G7 yedi-case SQLite readback fixture | `6bd86d7972c8bca511b5702117be3542431e7493` |
| `candidates/ORG-06/test_org_core_checkout.py` | Orijinal Core Research + tarihsel ORG SQLite fixture | `04ecd44417e97fa44d3b9e59f56db6db30e5cb87` |
| `candidates/ORG-05R3/durable_ops.py` | Tarihsel ORG OperationsStore | `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` |
| `product/ai-company-os-backend/durable_ops.py` | Güncel 562 adayındaki ilaveli OperationsStore ve assignment incelemesi | `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` |
| `product/ai-company-os-backend/app/core/transaction/org_membership_review.py` | Gerçek G7 okuyucusu; ayrı store, atomik olmayan fresh read | `675615e04059280ec6aa99e9679b4388cd018c2d` |
| `product/ai-company-os-backend/tests/test_core_org_session_sqlite_d5g7.py` | Ayrı, bazı portları stub/patch eden protokol suite'i; **CI 7 ile aynı değil** | `ed8963a87d69d62ae8a827a2d5c681c6cd1eb463` |

**Değişmeyenler:** Ürün, fonksiyon, API, DB, event, dependency/lock, CI, güvenlik politikası, yetki, main ve product-dev source tree. Bu turda Python/Node ürün testi **0**; statik denetim **9/9**.

## Kalan gerçek kapanış işi / sorumluluk
- **MI04/G2/G9 kaynak sahipleri:** PR19 `intent_authority.py` sürümünü ve ORG/G9 kontratını açıkça onayla/reddet; 41 satır eklenmesi kendi başına onay değildir.
- **MI01/W8 sahibi:** önce 553 tabanında C04/C05 dependency owner review + C06-C08 orijinal full build/native browser; 562 adayına *ayrı* manifest re-pin/yeniden yeterlilik şart. PR20 sahip dalına müdahale edilmedi.
- **MI03/ORG sahibi:** G7 yedi özgün senaryoyu güncel üründeki `durable_ops.__file__` ve `OperationsStore` sınıfını assert ederek, owner kontrollü exact source/dependency altında ayrıca çalıştır; eski source pinlerini körlemesine değiştirme.
- **MI02/IV sahibi:** gerçek bağımsız issuer/custody, GATE02 P02, korumalı PostgreSQL COMMIT/restore, sink-side fencing, 8 bağımsız güvenlik negatifi ve IV; HOLD.

## İlerleme / teslim / geri dönüş
- Genel geliştirme ağırlıkları %15/%35/%20/%20/%10; onaylanmış 10 grup paydasından 0: **önceki/güncel HESAPLANAMADI, delta yok**.
- Core kabul **12/16 → 12/16**; UI **21/40 → 21/40**; MVP **0/11 → 0/11**; bağımsız güvenlik **0/7 → 0/7**. Ürün kabul artışı **0 yüzde puan**.
- Test 72/72 ve 10/10 daha önceki özgün CI kanıtlarıdır; **yeni ya da benzersiz test eklenmedi**.
- Kanıt kaynağı: [PR19 sahibi bilgilendirme](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19#issuecomment-7037145027), [PR6 güncel durum](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/6).
- Arıza: yanlış import kökü tarihsel ORG kaynaklarını kullanabilir; tanı `durable_ops.__file__` + Git blob + source pins. Maintenance: source prefix ve yeni fonksiyonların owner review'u. Rollback: bu belgenin ve ilgili merkezi JSON delta kaydının normal revert'i; PR6 açıklama/title düzeltmesi gerekirse GitHub geçmişinden önceki metadata restore edilir. Herhangi bir kaynak dalında force push, güvenlik claim reseti veya otomatik merge yok.
