# AI Company OS — MI-P0 | 553 kanonik geliştirme kaynak aktarımı: kapalı / yeni kaynak tabanı

**Tarih: 20 Kasım 2026 · Gerçek kaynak aktarımı: PASS · Ürün, güvenlik ve W8 kabulü: HOLD.**

## Sonuç / neden
H01'in "engelleri kaldır ve aktar" talimatı kapsamında özgün ortak 553 kaynak ağacı, sıfır kaynak yeniden yazımı ve mevcut koruma sınırlarıyla **`integration/product-dev`** dalına alındı. Bu **development-source only** işlemdir; ürünün çalıştığı, bağımsız güvenlik kabulü olduğu, gerçek COMMIT veya PROD yetkisinin açıldığı anlamına gelmez.

- **Önceki kanonik kaynak:** `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`, 505 ürün dosyası / 504 manifest kaydı.
- **Yeni kanonik geliştirme kaynak:** `9a3571d6a06537ba718bafc45398c309bf3dc9b1`, 553 ürün dosyası / 552 manifest kaydı.
- **Aktarım incelemesi:** [PR #15](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/15) **MERGED**, normal merge commit (parents sırasıyla eski kanonik `8a3b05...`, candidate `98808d...`).
- **Kaynak Git tree:** `f4cdcf68115917ab69ba6441414539fe32a59369`, özgün PR12 553 ortak ürünle birebir.
- **Manifest blob:** `27b4eb5816265d4e6e6d2458acb6220db7dd0c76` (552 entries) ve W8 adapter manifest literal birebir aynı.
- **Gerçek diff:** 63 `product/` yolu + `tests/integration/w8_unified_u3.py` dışında **hiçbir dosya** değişmedi. Özellikle Design Master, CURRENT/NEXT_STEP, mimari, kararlar, `.github`, infrastructure, lock/wheelhouse ve main korunuyor.
- Geniş, aynı ürün değişikliklerini ikinci kez taşıyacak [PR #14](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/14) **CLOSED / UNMERGED**; kalan 137 doküman/yardımcı/test kaynakları özgün ortak adayda korundu, owner review gerektirenler ayrı taşınacak.

## Teknik katalog: ürün içindeki mevcut değişiklikler
Tüm 64 yol ve sorumlusu, bu turun [TECHNICAL_CATALOG.json](TECHNICAL_CATALOG.json) dosyasında. Son kabul edilen kaynak referansı [TECHNICAL_CATALOG_CURRENT.json](TECHNICAL_CATALOG_CURRENT.json). Kritik kümeler:
1. **G9/ORG:** `durable_ops.py` 162 özgün satırı koruyan 41 satırlık D0 uzantı. `initialize_assignment_ops`, `OperationsStore.record_assignment_review` ve `OperationsStore.assignment_review` yalnız sentetik/local gözlem; owner ratifikasyonu bekliyor. `assignment_lifecycle.py`, `assignment_review.sql` ve diğer ORG kaynaklarının son sürümü ürün dosyalarına alındı. Gerçek PostgreSQL migration veya IAM grantı çalıştırılmadı.
2. **G2/IAM:** `intent_authority.py` için `fa47acd...` ortak ve `b28788f...` G2 varyant çatışması kaynak sahibinin kararını bekliyor; otomatik seçilmedi. Bağımsız root/consumed claims/sink implementasyonu yapılmış sayılmaz.
3. **MI-07/08 Model–Memory, MI-09 Skill, MI-05/06 Projection/Office, MI-01 UI:** önceki 505→539 adımında kaynak sahibi pinleri korunarak alınan mevcut kaynaklar; 553 üzerinde full orkestrasyon testleri ayrı.
4. **MI-01/W8:** `tests/integration/w8_unified_u3.py` eski manifest literalini yeni kesin blob'a bağlandı; tarihi `p24.HISTORICAL` ayrımı kaybedilmedi. Bu yalnız **statik pin düzeltmesi**.

## Mevcut testler, yeni çalıştırılmayanlar
| Kanıt | Durum | Kabul sınırı |
|---|---|---|
| GitHub güncel ürün git tree + 552 entry manifest + U3 W8 pin | **PASS exact readback** | kaynak bütünlüğü; ürün çalışma testi değil |
| PR #11 CI #44628704044, ORG paketleme 4/4 ve SQL 11/11, manifest 552/552 | **PASS, tarihsel aynı 553 ürün ağacı** | D0 SQLite; gerçek IAM–PG değil |
| PR #6 CI #44620141705, Core–OperationsStore 10/10 | **PASS, tarihsel özgün owner kaynağı** | ayrı kaynak pin; yeni koşum değil |
| PR #4, tanısal Next/SSE seçili | **PASS, tarihsel eski kaynak/izole** | exact 553 tam W8 değil |
| Özgün 553 `prepare→install→test→smoke`, native browser, model344/Core29 | **NOT_RUN / HOLD** | tam W8 ürün entegrasyon engeli |
| G2 50, G9 7, Memory–T1 10; real PG/RLS/restore; A1 8 negatif / IV | **NOT_RUN / HOLD** | bağımsız güvenlik ve ürünü çalıştırma kabulü |

## Güncel mimari, yetki ve aşama ayrımı
**D-03/D-04 Option A** bağımsız yönetilen uzlaşı/root, işlem alıcısında sink-side fencing/idempotency mimarisi olarak seçili; uygulanmış ve bağımsız kabul edilmiş değildir. Eski DB+pin restore replay zafiyeti açık. Gerçek issuer/root/claim/COMMIT/dış etkiler **HOLD/DENY**; otomatik yürüteç, gizli anahtar, harcama, deploy veya PROD yetkisi değişmedi.

Önceden 505 kaynak vardı, şimdi **553 kaynak gerçekten kanonik dev dalında**. Core ürün kabulü **12/16 (%75) → 12/16 (%75)**; UI **21/40 (%52,5)**; MVP **0/11 (%0)**; IV **0/7**. Genel geliştirme (%15 tasarım / %35 kaynak / %20 fonksiyonel / %20 entegrasyon / %10 kabul) için owner-ratified kriter paydaları henüz tam değil, dolayısıyla tek bir yüzde **HESAPLANAMADI**. Kaynak dosyası artışı ürün kabulünü otomatik yükseltmez.

## Bakım, rollback, izlenebilirlik
- **Gerçek SHA doğrulaması:** `integration/product-dev@9a3571d6a06537ba718bafc45398c309bf3dc9b1` + ürün Git tree `f4cdcf...` + manifest blob `27b4eb...`; bunlardan herhangi biri değişirse veri/toplama/analiz dönemi yeniden pinlenmeli.
- **Arıza teşhisi:** W8 adapter manifest uyuşmazlığında sabit literal/manifest blob'u kıyasla; G2/G9 source drift'te owner pinned SHA ve regression hash'lerini kontrol et; tam W8 koşmadan build PASS değil.
- **Rollback önerisi:** ayrı inceleme dalında önce commit/etki ve tarihsel test sonuçlarını koruyarak `git revert -m 1 9a3571d6a06537ba718bafc45398c309bf3dc9b1` uygulanması değerlendirilir; kanonik daldaki normal revert de ancak kullanıcı/sahip kararıyla yapılır. Force push / history rewrite yok. Geri dönüş referansı eski `8a3b05aa`.
- **Sonraki kanonik iş:** MI01-W8 553 exact full fresh lock fingerprint + prepare/install/test/smoke/native browser; MI03/G9 ve MI02/G2 owner source regression, Memory/T1, strict protected PG ve ayrı A1 IV. Tekrar kaynak prototipi üretme.

**Makine kanıtı:** [POST_MERGE_VERIFICATION.json](POST_MERGE_VERIFICATION.json). Bu devir eski **pre-merge** `ARCHITECTURE_CATALOG_HANDOVER.md` dosyasını silmez; tarihsel ek olarak korur.
