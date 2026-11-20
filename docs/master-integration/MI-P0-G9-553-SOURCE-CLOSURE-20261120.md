# MI-P0 — G9 özgün yedili testin kanonik 553 kaynak kapatma teşhisi
20 Kasım 2026 · **SOURCE-ONLY STATIC GIT BLOB PRECHECK / 0 YENİ FONKSİYONEL TEST**

## Neden / görev çakışması
PR #15 başka merkez entegrasyon hattınca zaten `integration/product-dev` ürün kaynağına birleştirildi: **9a3571d6a06537ba718bafc45398c309bf3dc9b1**, ürün Git tree `f4cdcf68115917ab69ba6441414539fe32a59369`, 553 dosya/552 manifest. PR #12/11 ORG 4+11 ve MI-04 özgün 0214 10-case D0 CI #44695937454 yeniden çalıştırılmadı. W8 MI-01 hattında ve orijinal tam koşumu ayrı HOLD. Bu turda yalnız *eski G9 7 testinin güncel kaynakta doğrudan koşulabilirliği* incelendi; yeni runner veya PR/prototip oluşturulmadı.

## Kesin başlangıç ve bitiş kanıtı
- Kaynak alınan özgün `planning/0230-d5g9-exact-three-store-checkout:candidates/D5-G7/SOURCE_PINS.json` Git blob: `cef9ce82a497522d2e4a9347b77453879e4790f3`. İçinde 56 Git blob pini; **29'u product kaynakları**, diğer 27'si ayrı `candidates/`, `database/` gibi yardımcı dosyalardır.
- Kıyaslanan GitHub **tam recursive tree**, `integration/product-dev@9a3571d6a06537ba718bafc45398c309bf3dc9b1`; truncated=false. 29 eski product pininin **21'i aynı exact Git blob**, **7'si kanonik ürün yolunda yok**, **1'i farklı Git blob**. Bu **tam 29 ürün pini için statik fark** kanıtıdır, 7 test koşumu/uyumluluk testi değildir.
- **Tek farklı içerik**: `product/ai-company-os-backend/app/core/transaction/intent_authority.py`; G9 fixture'ın istediği **G2** varyantı `b28788f46a39c282d79d29c4abd817ed5fc9de99`, kanonik sürüm `fa47acd32adb309896f762ec50e47bf26641adbb`. G2/Authority sahibi seçim yapmadan bunu sessizce overwrite/repin etme.

## Kanonik product yolunda eksik yedi özgün G9 dosyası
1. `product/ai-company-os-backend/app/core/iam_session.py`
2. `product/ai-company-os-backend/app/core/transaction/identity_fence_review.py`
3. `product/ai-company-os-backend/tests/test_iam_identity_d5g4.py`
4. `product/ai-company-os-backend/app/core/transaction/org_membership_review.py`
5. `product/ai-company-os-backend/tests/test_iam_org_d5g5.py`
6. `product/ai-company-os-backend/app/core/transaction/core_org_session_review.py`
7. `product/ai-company-os-backend/tests/test_core_org_session_sqlite_d5g7.py`

Bu **eksiklik**, özgün geliştirme dallarında da bu dosyaların mevcut olmadığı anlamına gelmez; yalnız `product-dev` birleşik `product/` ağacında bu exact yollarda olmadığını gösterir. Tarihsel G9 `candidates/D5-G9/run_exact_checkout.py` 403 manifest/248 backend koşulunu ve `candidates/D5-G7/test_checkout.py` özgün 7 testi sabitler. Kanonik ürün artık 552 manifestli olduğundan **403→552 manifest pinini otomatik değiştirerek** test PASS elde etmek tarihsel/gerçek güvenlik kanıtı olamaz.

## Teknik katalog ve etkiler
- **Kaynak/API/DB/event/Class/Function değişikliği:** 0 (salt-okunur inceleme). Özellikle G2 `intent_authority.py`, G9 `core_org_session_review`, `iam_session` ve eski `test_checkout.py` dosyalarına müdahale yok.
- Bağımlılık: özgün G9 runner `cryptography==46.0.4`, disposable SQLite, özgün G7 56 pin, G8 manifest 403 ve exact test setini ister. Current-553 W8/Node zinciri ayrı bağımlılıktır.
- Yapılmış test: GitHub tree/blob-pin set eşitliği, **21/29 same, 7/29 missing, 1/29 mismatched**; orijinal G9 7/7 **NOT_RUN**, G2 50/50 **NOT_RUN**. G9 7 test senaryosunun ürün 553 üzerinde güvenlik kabulü **HOLD**. Bu 8/29 eksik/farklı kaynağın her biri için sahip onayı gereklidir.

## Tek-yazıcı sahibi aksiyon matrisi
| Kapı | Mevcut sahibi | Yapılacak iş | Kanıt/karar durumu |
|---|---|---|---|
| G9 historical exact runner | MI-03/04 + ORG/G9 | Özgün G8/G9 403-manifest repo checkout ve 56-pin testleri özgün ortamında çalıştır; yeni 553 ürün testiymiş gibi etiketleme | **NOT_RUN; SOURCE_SCOPE_SEPARATE** |
| 7 eksik product yolu | IAM/D4/ORG sahipleri | Önce özgün branch/source pin ve 553 taban arasında transitive import/DB uyumu, güvenlik sürüm incelemesi, ayrı owner-controlled aktarım | **HOLD_OWNER_REVIEW** |
| 1 çakışan authority yolu | G2/Authority sahibi + bağımsız Security | `b28788f...` vs `fa47acd...` tek sürüm kararı, gerçek issuer/role/sink güven zinciri; yanlış yetki yükseltme yok | **HOLD_SECURITY** |
| W8 | MI-01/Unified | Aynı `product-dev@9a3571d6` kaynağında gerçek tam fresh lock `prepare/install/test/smoke` + native browser | **NOT_RUN** |
| PG+IV | MI-02/06/Security/IV | Gerçek protected PG COMMIT, eski DB restore replay önleme, bağımsız 8 negatif senaryo | **HOLD** |

## Test / teşhis / bakım / rollback
Bir sonraki owner koşumunda hem historical `403/248/56` fixture hem canonical `552/553` kaynak sürümleri ayrı raporlanmalı. `G6B_SOURCE_PIN_HOLD`, `MANIFEST_COUNT_HOLD`, `SOURCE_PIN_HOLD` saptanırsa mevcut yanlış SHA'yı PASS için değiştirme; bağımsız kod/izin sahibi kararını iste. Sonradan farklı SHA geldiğinde `product-dev` tam Git tree ve immutable source pinleri üzerinden yeniden matris hesapla. Tamamlanmış CI sonuçlarını tekrarlama. Geri dönüş yalnız bu governance raporunu normal revert; ürün/PR/claim geçmişi değişmez.

## İlerleme
IAM/ORG geliştirme önce/sonra **%42,50/%42,50 (Δ0 puan)**. Genel 15/35/20/20/10 yüzde paydalar dondurulmadığından **HESAPLANAMADI**. Core kabul **12/16**, UI **21/40**, MVP **0/11**, bağımsız güvenlik **0/7**; bu statik çalışma kabul değişikliği değildir.

Kaynak devir referansı: `progress/MASTER_INTEGRATION_CURRENT.json`, `docs/master-integration/WORKING_STANDARD.md`, `progress/REPORTING_STANDARD_20261118.md`, `docs/master-integration/MI-P0-PR14-PR15-SINGLE-WRITER-CLOSEOUT-20261120.md`.
