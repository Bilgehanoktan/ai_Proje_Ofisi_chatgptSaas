# AI Company OS — MI-P0 / 566 dosyalık kontrollü birleşik kaynak adayı

**Tarih:** 20.11.2026 · **Statü:** DRAFT / REVIEW ONLY / FULL W8 & SECURITY HOLD

## 1. Ne tamamlandı?
- Kanonik `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` **değişmedi**. Kanonik ürün 553 dosya / manifest 552 girdi.
- PR #19 G2/G9 sahibi `0a8907f177bb3e9b458aefb3ea3441b15537f542` ile PR #29 Office + dört proxy sahibi `59c098b0ec3387ef1318e4957248e843e1526d81` arasındaki ürün dosyaları Git tree üzerinden karşılaştırıldı.
- G2/G9: **10** kaynak yolu farkı (1 mevcut `intent_authority.py` varyantı + 9 ek dosya). Office/proxy: **8** yol farkı (4 route değişikliği + 4 yeni yardımcı/test dosyası). Ortak değişen *ürün kodu* yolu **0**; ortak manifest yolu **1**.
- İki taraftaki 18 kaynak dosya, özgün Git blob SHA'larıyla **yeniden yazılmadan** kanonik tabana alındı. `product/SOURCE_MANIFEST.json` owner kaynaklarının tam `sha256` ve `bytes` kayıtları birleştirilerek **565 girdi** olarak yeniden üretildi.
- **İzole GitHub commit:** `886e45d352389c483cd463487b74e3a1da04689a`. Ebeveyn kanonik commit `254e0188...`, tree `9c0409efaa8a2dfaed85176a5fac6b7552629686`; source manifest blob `35ef4764f9fa724bed182b96d76a2746b0c38602`.
- GitHub source readback: **565/565** manifest path ve bytes/mode eşleşmesi, **566** ürün dosyası (manifest dahil), **19** kaynak/manifest değişikliği, diğer repo yolunda değişiklik **0**, commit ahead **1**, behind **0**. Bu bir **kaynak/manifest statik bütünlük** testidir; tam ürün build veya işlevsel entegrasyon değildir.

## 2. Mimari ve teknik katalog

| İlgili alt sistem | Kaynak transferi | Sembol / API / DB / event etkisi |
|---|---|---|
| IAM / T1 / ORG güven sınırı | `app/core/iam_session.py`, `core_org_session_review.py`, `identity_fence_review.py`, `org_membership_review.py`, owner `intent_authority.py` varyantı | Owner G2/G9 semantiği korunur; bağımsız root, gerçek issuer/claim/sink yetkisi **kanıtlanmadı**; DB/event sözleşmesi kabul edilmedi |
| IAM / Core regresyonu | `test_iam_session_d5g1.py`, `test_iam_authority_d5g2.py`, `test_iam_identity_d5g4.py`, `test_iam_org_d5g5.py`, `test_core_org_session_sqlite_d5g7.py` | Kaynak adayı içine owner testleri taşındı; bu ortak 566 kaynak üzerinde gerçek çalıştırma **NOT_RUN** |
| Salt okunur Office / Frontend proxy | `app/api/demo/office-workbench/route.ts`, `admission/route.ts`, `outbox/route.ts`, `task-budget/route.ts` | D0 proxy HTTP HOLD/503 timeout koruması owner kaynaklarıyla birebir; gerçek provider/harcama veya yeni API tanımı yok |
| Ortak frontend yardımcı katmanı | `features/mvp/readBoundedD0Json.ts` ve üç özgün test dosyası | Yeni bir transitive dependency yok, değiştirilen endpointler korunur; tam Next/TypeScript/native browser **NOT_RUN** |
| Kaynak bütünlüğü | `product/SOURCE_MANIFEST.json` | 565 doğrulanmış kaynak yolu; owner SHA256 ve bytes taşındı; bu birleşim yeni kaynak kabulü vermez |

**Düzgün kanıt sınırı:** PR #19 tarihsel 72/72 seçili D0, PR #29 12/12 seçili ortak frontend QA, PR #23 güncel bağımsız Office 15/15 testi **başka sabit source commit'lerde** çalıştırıldı. Yeni 566 adayındaki işlevsel test sayısı **0**; önceki PASS sonuçları bu adaya transfer edilmedi. Güncel G7 özgün testleri `current OperationsStore` altında 0/7 NOT_RUN. Tam W8 C04–C08, native browser, protected PostgreSQL, bağımsız güvenlik ve gerçek MVP 0/11 HOLD/NOT_RUN.

## 3. Neden doğrudan kanonik ürüne alınmadı?
Bu yeni dal, farklı yetki alanlarının **izole kaynak derlemesidir**. Dosya yolu çakışmasının sıfır olması; çalışma zamanı sözleşmesi, kimlik yetkisi, kaynak sahibi incelemesi, PostgreSQL restore-idempotency veya kullanıcı onayı bulunduğunu göstermez. Özellikle `intent_authority.py` varyantının bağımsız güvenlik kökeni henüz ratifiye edilmedi. W8 kaynak manifesti sabit 553'e bağlıyken 566 adayına körlemesine yeniden pinleme yasaktır.

`integration/product-dev`, `main`, CI workflow, secret, grants, cloud provider, müşteri verisi, harcama, harici işlem ve PROD değişmedi. Tek etkili değişiklik izole taslak kaynak commit'idir.

## 4. Uygulama / test planı (yetkili ortamda, mevcut özgün runner'larla)
1. Kaynak sahibi MI-01, **önce** kanonik 553 SHA üzerinde W8 **C04 prepare** (Python `pip --isolated download` ile wheelhouse/`python.lock`/`locks/REVIEW.json`). Bu sohbetin çalışma konteynerinde GitHub/PyPI/DNS erişimi yoktur; eski 14.11.2026 arşivi ile C04 yerine getirilmedi.
2. C05: bağımlılık/fingerprint/lisans/supply-chain sahibi bağımsız inceleme ve onay; manifest belgesi tek başına onay değildir.
3. C06–C08: onaylanmış hashlerle W8 install, bütün backend/Next/TypeScript regresyonu, loopback/native browser smoke ve orijinal ekran denetimleri.
4. G2/G9/ORG kaynak sahipleri `intent_authority.py` varyantını/bağlayıcıları onayladıktan sonra güncel `OperationsStore` altında **özgün G7 yedi testini** çalıştırır. Yeni bu 566 SHA için yeni manifest ve W8 source pinleri bilinçli şekilde onaylanır; CI kapsamı otomatik genişletilmez.
5. MI-02 bağımsız root/issuer/sink, gerçek protected PostgreSQL commit/RLS, full restore/replay, 8 negatif güvenlik ve 7 IV kabulünü yürütür.
6. 11 özgün MVP kabul zinciri yalnız gerçek kanıtla kapatılır: şirket → ajan → görev → plan → DAG → izinli model/araç → kalıcı sonuç → ofis → QA/IV → insan bütçe/onayı.

## 5. Kanıt, ilerleme ve devir
- Statik kaynak denetimi: **565/565 PASS**, source Git blob path overlap: **0**, CI/native W8/PG/IV: **NOT_RUN/HOLD**.
- Genel geliştirme oranı: *önce HESAPLANAMADI / şimdi HESAPLANAMADI* (10 grubun 0'ında resmi kriter paydası onaylı). Standart ağırlık tasarım 15, kod 35, fonksiyonel 20, entegrasyon 20, kabul 10.
- Core ayrı kabul 12/16, UI 21/40, MVP 0/11, bağımsız IV 0/7. Bu turda yeni kaynak satırı net +13 **yalnız aday dalında**, kanonik ürün kaynak kazanımı 0; ürün kabul delta 0 puan.
- Tam teknik referans: `docs/master-integration/MI-P0-566-G2G9-OFFICEPROXY-20261120/EVIDENCE_AND_CATALOG.json`.
- Bakım/arıza teşhisi: owner SHA değiştiğinde 18 kaynak yolunun blob pinlerini yeniden karşılaştır; manifest path/size/SHA256 uyuşmazsa **HOLD**, hiçbir testin PASS iddiasını taşıma. G2/G9 ve proxy branch'lerinden biri değişirse yeni aday R2 aç; eski adayı silme.
- Rollback: yalnız bu review PR'ını kapat veya source commit'i normal `revert` ile geri al; kanonik 553 ve önceki owner branch'lerine dokunma. Git geçmişini yeniden yazma.
- H01 yeni karar: gerçek yetkili security/PROD aktivasyonu için bağımsız owner ve kabul hâlâ gerekir. Bu tur bu alanlar için ek yürütme izni üretmedi.

## 6. Bir sonraki çalışma
**MI-01 W8 C04→C05→C06–C08**, ardından exact 566 manifest/pin üzerinde birleşik özgün testler, bağımsız PG/IV ve 11 MVP kriteri. Önceki kaynak adaylarının çalıştığı testleri yeniden başarıya sayma; önce gerçek hedef kaynak ortamını doğrula.
