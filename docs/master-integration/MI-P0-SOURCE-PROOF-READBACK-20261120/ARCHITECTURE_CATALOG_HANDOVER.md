# AI Company OS — MI-P0 kaynak kanıtı / teknik katalog / devir
**20 Kasım 2026 · MASTER INTEGRATION · READ_ONLY_STATIC_SOURCE_RECONCILIATION**

## Ne, neden, nerede, nasıl
Mevcut PR #7 (`505→539`) ve PR #9 (`539→553`) kaynak farkını ürün kodunu yeniden yazmadan, GitHub manifest kaynakları ve commit diff ile karşılaştırdık. Amaç, ortak ürün transferini engelleyen **hangi değişikliğin gerçekten kanıtlandığını ve hangisinin owner/entegrasyon kabulü beklediğini** ayırmak. Çalışma yalnız `planning/master-integration-governance` üzerindeki bu doküman ve `SOURCE_RECONCILIATION.json` ile sonraki merkezi indeks eklerini kapsar. `integration/product-dev`, `main`, kod, API, SQL, runtime ve CI değiştirilmedi.

## Sabit kaynak ve sonuçlar
| Aşama | Kaynak | Manifest | Doğrulama |
|---|---|---:|---|
| Kanonik ürün | `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` | 504 / ürün 505 | referans, değiştirilmedi |
| PR7'in 539 aday kanıtı | `bd57cc8235a13ba5bf10545a7879be98fd7b47f5` | 538 / ürün 539 | 49/49 dosya yolu ve eski/yeni manifest kaydı eşleşti |
| Güncel 539 ortak aday | `59c0fc505ca286e681ed0965ee317eadf571a806` | 538 / ürün 539 | aynı manifest Git blob; PR7 adayından ürün dosya farkı 0 |
| PR9 ORG/Core adayı | `d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` | 552 / ürün 553 | 14 yeni manifest kaydı, eski 538/538 korunmuş |

PR7: 35 eklenen, 13 değişen, 1 kaldırılan, 490 değişmeyen manifest kaydı. GitHub'da 49 `product/` yol değişimi (34 add, 14 modify — manifest dahil, 1 rename). PR7'in 49 yol/owner kaydı ile GitHub diff ve karşılaştırılan ilgili manifest kayıtları tutarlı; **0 uyuşmazlık**. Önceden raporlanan test koşumları *tekrar çalıştırılmadı*.

PR9: 14 yeni `product/` dosyası; 12 modül/SQL kaynak + 2 test dosyası. Önceki 538 manifest girdisinin hiçbirinin hash/bytes kaydı değişmedi, hiçbir giriş silinmedi. GitHub compare `59c0f…→d6b82d…` **diverged (ahead 2, behind 5)** bildiriyor; basit doğrusal fast-forward varsayma. Yeni 14 dosyanın entegrasyonu **owner ve W8 sahibi** kontrolünden geçmedikçe HOLD.

## Katalog ve bağımlılık haritası
- **G9 / ORG dosya-sürüm çatışması:** `product/ai-company-os-backend/durable_ops.py`. Tarihsel G9 blob `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` ile ORG/Core genişletilmiş blob `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` farklı. Mevcut CTL-01 raporu: 41 ek satır ve yeni `initialize_assignment_ops()`, `OperationsStore.record_assignment_review()`, `OperationsStore.assignment_review()`. Bu kodun kabulü için ORG/G9 sahibi, import ve original smoke kontrolü gerekiyor.
- **G2 Authority aynı-yol sürüm çatışması:** `product/ai-company-os-backend/app/core/transaction/intent_authority.py`; mevcut `fa47acd32adb309896f762ec50e47bf26641adbb`, G2 `b28788f46a39c282d79d29c4abd817ed5fc9de99`. Bu turda hiçbir kaynak sürümü seçilmedi. IAM/T1/Authority owner kararı gerekiyor.
- **Ortak kapsam:** `assignment_lifecycle.py`, `org_core_bridge.py`, `operations.sql`, `schema.sql`, `assignment_review.sql` ORG adayı içinde. PostgreSQL kanonik migration **eklenmedi**. API/endpoint, event grubu, kullanıcıya yetki ve dış etki **eklenmedi**. PR9 tam bağımlılık, import ve veri kapsamı bakımından sahip incelemesi gerektiriyor.
- **A mimarisi:** bağımsız güvenlik root/issuer/custody/claim, restore, sink-side fencing+idempotency yalnız mimari seçimdir; PR #10 A1 sahip incelemesi 10/10 **PENDING_OWNER**, bağımsız A-AT01..08 **0/8 NOT_RUN**. PR #8 kapandı, PR #10 aynı işin temiz yalnız-belge taslağıdır. Ek hat açılmadı.

## Test kanıtlarının ayrımı
| Kanıt | Durum | İspatladığı / kanıtlamadığı |
|---|---|---|
| Bu turun 49 yol ve 14 manifest kontrolü | **PASS — statik GitHub readback** | kaynak/manifest uyumu, *gerçek test değil* |
| PR6 Core–OperationsStore 10 özgün D0 SQLite | **PASS** (tarihsel CI `44620141705`; son tekrarı `44623379375`) | sentetik Core-ORG pozitif/negatif readback; issuer / PG değil |
| PR4 sınırlı CI 3/3 | **PASS** (run `44620987573`) | tanısal D0 kaynak+Next/SSE; tam W8/native U3 değil |
| PR9 ORG/SQL özgün 11 | **ayrı tarihsel PASS** | yerel sentetik kapsam, gerçek ORG yetki sahibi değil |
| PR9 özgün ORG paketleme 4 smoke | **NOT_RUN** | gerçek tam ortam bağlantısı açık |
| Özgün G2 50, G9 7, Memory–T1 0214 10 | **NOT_RUN** | gerekli orijinal çapraz güvenlik kanıtları |
| PostgreSQL korumalı T1/restore ve IV | **HOLD** | gerçek bağımsız işlem/güvenlik kabulü yok |

Özgün test tekrarlarına yeni test adedi verilmez. Bu tur yeni fonksiyonel test/CI çalıştırmadı.

## İlerleme / eski ve güncel
- **Geliştirme ağırlıkları:** tasarım 15, kod 35, fonksiyonel 20, entegrasyon 20, nihai kabul 10. Onaylı genel kriter/payda bulunmadığından eski/yeni **HESAPLANAMADI**, delta yok.
- **Core kabulü:** 12/16 = %75 → 12/16 = %75; **Δ 0**.
- **UI kabulü:** 21/40 = %52,5; değişiklik yok. **MVP:** 0/11 → 0/11; **Δ 0**. **Bağımsız güvenlik:** 0/7; ayrıca A1 bağımsız test matrisi 0/8 NOT_RUN.
- **MI03 kaynak gelişimi:** %42,5 → %42,5. **MI08:** %45 → %45. Bunlar global kabul değildir.
- **Yeni ürün kodu / API / DB / test / CI / permission:** 0.

## Bakım, arıza teşhisi, geri dönüş, sıradaki iş
1. **PR7 merkezi JSON geçmiş kaybı riski:** Eski PR7 `progress/MASTER_INTEGRATION_CURRENT.json` tüm dosya olarak alındığında sonraki Option A / MI-COMMON-09 / PR9 kayıtlarını silebilir. **Yöntem:** PR7'in yalnız yeni `mi_505_539_proof_reconciliation` statik kanıt anahtarını owner-reviewed *review-only* indeksine ekle; tüm güncel HEAD'i koru. Eski `revision`, `queue.next`, `review_history` gibi alanlarla overwrite yok.
2. **PR8→PR10:** PR8 kapandı; PR10 ilerleme JSON'u değiştirmiyor. Bu nedenle PR7/PR8 eski çift yazıcı çatışması güncel açık PR'lar bakımından azaldı. PR7 halen eski bazdadır; PR9 ürün aktarımı da HOLD.
3. **Bir sonraki P0 kapı:** ORG/G9 `durable_ops.py` seçimi, G2 Authority sürüm seçimi, exact lock/fingerprint + orijinal W8, PR9 paketleme smoke ve gerçek PG/IV. Onaylar olmadan `product-dev` transferi **yok**.
4. **Rollback:** Governance dosyaları normal revert ile geri alınır. Başlangıç `product-dev@8a3b05aa` ve `main` korunur; force push, otomatik merge veya kaynak overwrite yapılmaz.

**Makine kanıtı:** [SOURCE_RECONCILIATION.json](SOURCE_RECONCILIATION.json) · [PR7](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/7) · [PR9](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/9) · [PR10](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/10).
