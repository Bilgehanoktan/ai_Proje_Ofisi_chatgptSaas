# AI Company OS — CTL-01 | G9 / 539→553 owner-pin ve manifest geri okuması
2026-11-20 · Merkezi entegrasyon tamamlayıcı incelemesi · **READ_ONLY_SOURCE_ANALYSIS / GOVERNANCE_DOCUMENTATION_ONLY**

## Kapsam / değişiklik nedeni
PR #7, 505→539 sahiplik incelemesinin mevcut taslak teslimatıdır; bu inceleme **tekrarlanmadı**. PR #5/#6 Core–OperationsStore ve IAM/ORG sahiplik hatlarının mevcut işidir; bunlar da yeniden kodlanmadı. Bu kayıt, mevcut merkezi CTL-01'in yalnız **G9 kaynak sürümü ve 539→553 manifest** eksik kısmını immutable GitHub kaynakları üzerinden bağımsız olarak daraltır. Kod, runtime, SQL, API, permission, CI, product-dev/main, owner pin veya PR merge yapılmadı.

## Kesin kaynak pinleri
| Referans | SHA / Git blob | Kanıt |
|---|---|---|
| `integration/product-dev` | `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` | Git ref geri okuma: değişmedi; 505 ürün dosyası, 504 manifest girdisi |
| Ortak kaynak `integration/mi-common-source-review-01` | `4035d1a884362dae56a60d91358ea6e8e7dc0cdd` | 539 dosya / 538 manifest; `product/SOURCE_MANIFEST.json` blob `03af243e8683f92c5d9c0b24e90b70d2bd6af29f` |
| ORG/Core `integration/mi03-gate03-org-runtime-closure-01` | `d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` | 553 dosya / 552 manifest; `product/SOURCE_MANIFEST.json` blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76` |
| Tarihsel ORG/G9 dosyası | `planning/0230-d5g9-exact-three-store-checkout:candidates/ORG-05R3/durable_ops.py` | blob `43ed448c02904ab44b3cf8665f4aeafb0a38f10a`, 162 fiziksel satır (son boş satır dahil) |
| ORG sahibi tarafından genişletilmiş dosya | `6efc6714757ebd698d27efd7022afc2c92af70d0:candidates/ORG-05R3/durable_ops.py` | blob `619fe224c05d7f7f7efe998583e4730cb2cb4d3e`, 203 fiziksel satır |
| ORG/Core taşınmış dosya | `d6b82dc4:product/ai-company-os-backend/durable_ops.py` | aynı blob: `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` |
| Yeni atama bağımlılığı | `d6b82dc4:product/ai-company-os-backend/assignment_lifecycle.py` | blob `9f259e89fd339804292eb6c7fa8e7fd177c71b70` |

## G9 kod delta / teknik katalog
Tarihsel 162 satır ile önerilen 203 satır GitHub'dan ayrı ayrı alınıp **satır tabanlı LCS** ile karşılaştırıldı. Mevcut satırların tamamı aynı sırada korunuyor; **41 eklenen, 0 silinen/değiştirilen satır** var. Ekler iki blok:
1. Yeni satır 25–33: `initialize_assignment_ops(path)` (9 satır; `assignment_lifecycle.DDL` üzerinden yalnız boş/geçici ORG veritabanını hazırlar).
2. Yeni satır 151–182: `OperationsStore.record_assignment_review(...)` ve `OperationsStore.assignment_review(...)` (32 satır). SQLite transaction + history CAS + özgün Core readback + assignment karar/yapı incelemesini bağlar; farklı scope/hata koşulunda HOLD.

**Yeni/etkilenen semboller:** `initialize_assignment_ops`; `OperationsStore.record_assignment_review`; `OperationsStore.assignment_review`; `assignment_lifecycle.AssignmentPin`, `append_decision`, `inspect_assignment`, `verify_core_reference`. **Yeni gerçek API/endpoint:** yok. **Yeni kanonik DB/PG migration:** yok; ORG SQLite kaynak şema adayları önceki sahip dizisinde kalır. **Etkin güvenlik grantı:** yok. Bu salt-okunur yapısal uzlaştırılabilirlik gözlemidir; G9 owner ratifikasyonu, bağımlılık davranış testi ve gerçek issuer güvenliği yerine geçmez.

## Manifest delta / kaynak bütünlüğü
GitHub'dan iki manifestin `files` nesneleri okundu; 538 eski girdinin her birinde kayıtlı `bytes` ve `sha256` **birebir aynı**. Yeni kümede 14 ilave kayıt, 0 silinen, 0 eskiden değiştirilmiş kayıt var. GitHub commit compare ile 14 eklenmiş `product` kaynağı + yalnız `product/SOURCE_MANIFEST.json` değişikliği ayrı doğrulandı. Yeni 14 kaynak:
`durable_ops.py`, `integration_guard.py`, `operations.py`, `office_bridge.py`, `persistence.py`, `staffing.py`, `org_model.py`, `assignment_lifecycle.py`, `operations.sql`, `schema.sql`, `assignment_review.sql`, `org_core_bridge.py`, `tests/test_org_runtime_packaging_mi03.py`, `tests/test_org_sql_runtime_mi03.py` (tamamı `product/ai-company-os-backend/` altında).

**Kanıt sınırı:** Bu turda tüm 552 gerçek dosyanın içerik SHA-256 yeniden hesaplanmadı; manifest kaydı eşitliği, özgün Git blob SHA pinleri ve GitHub diff geri okuması yapıldı. Başka hatlardaki 10/10 PR6 D0 CI ve 42/42 PR4 T1 ayrı tarihsel/doğrulanmış koşumlardır, **bu incelemede yeniden çalıştırılmadı**. Tam W8, özgün G9 7/G2 50/Memory T1 10, protected PG/restore ve IV açık.

## Sahip incelemesi için dar karar matrisi
| Kapı | Sorumlu mevcut hat | Gerekli kanıt | Durum |
|---|---|---|---|
| CTL-01.A G9 sürüm | ORG/G9 + MI-03/MI-04 | `43ed...` tabanının `619fe...` additive genişletmeyle kabulü veya gerekçeli reddi; D0 API/dependency sözleşmeleri ve geri dönüş | **HOLD_OWNER_DECISION** |
| CTL-01.B 552 manifest | MI-01/W8 + ORG/Core ürün sahibi | 14 eklenen dosyanın exact pin ve dependency closure kontrolü, owner onayı, tam build/regresyon, orijinal lock/fingerprint | **HOLD_OWNER_RATIFICATION** |
| CTL-01.C gerçek otorite | MI-02/03/06; D4/ORG/IAM | D-03/D-04 **Seçenek A yalnız mimari yön**; bağımsız issuer/registry/member/role/assignment, revocation, restore ve sink fence | **HOLD** |
| CTL-01.D kaynak promotion | Master Integration + yetkili owner | Yukarıdakilere ek gerçek korumalı PG, W8 ve IV sınırları ile ayrıca izinli kontrollü taşıma | **HOLD_NO_PROMOTION** |

G2 `intent_authority.py` sürüm çakışması da başka mevcut owner hattındadır; bu dosyaya müdahale edilmez. Eski ürün+yerel otorite+pin restore açıklığı kapatılmış sayılmaz. PR #7 kendi 505→539 kapsamını korur; bu kayıt PR #7'nin otomatik onayı değildir. Owner review gönderme/PR yorumları ayrı, merge yok.

## İlerleme, teslim ve geri dönüş
- Tarihsel IAM/ORG ağırlıklı gelişim: **%42,50 → %42,50 (Δ 0 yüzde puan)**; yeni test/yürütme/entegrasyon/nihai kabul yok.
- Global 15/35/20/20/10 gelişim: **HESAPLANAMADI → HESAPLANAMADI**, kriter ve hat paydaları henüz ratifiye değil.
- Ürün kabulü: Core **12/16 (%75) → 12/16**, MVP **0/11 → 0/11**, bağımsız güvenlik **0/7 → 0/7**; Δ0.
- Bu tur: ürün kodu 0, ürün DB/API 0, test yürütme 0, izin değişimi 0, branch merge 0; yalnız koordinasyon kaydı.
- Öncelikli izleyen iş: sahipler G9 `43ed→619fe` kararını ve 552 manifest için explicit acceptance/reject gerekçesini aynı pinlerle versin. Kanıt gelmeden ürün dalı ilerletilmesin.
- Teşhis: yeni head görünürse bu SHA pinleriyle yeniden diff yap; test türü/owner ortam/run ID'si ve manifest kaydını ayır; eski delilleri silme.
- Rollback: yalnız bu governance dokümanını normal `git revert` ile geri al; asla force push, yetki yükseltme, `product-dev` veya `main` değişikliği yapma.

İlgili merkez referans: `docs/master-integration/MI-P0-CENTRAL-SOURCE-RECONCILIATION-20261120.md`; `progress/MASTER_INTEGRATION_CURRENT.json`; `progress/REPORTING_STANDARD_20261118.md`; `docs/master-integration/WORKING_STANDARD.md`.
