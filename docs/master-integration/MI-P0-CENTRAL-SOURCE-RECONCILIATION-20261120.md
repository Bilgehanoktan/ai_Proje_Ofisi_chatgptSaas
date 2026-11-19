# AI Company OS — P0 merkezi entegrasyon koordinasyonu / salt-okunur kaynak farkı

Tarih: 2026-11-20. Sınıflandırma: **ACTUAL_GITHUB_TREE_AND_MANIFEST_READBACK / NO PRODUCT EXECUTION**.

## Kullanıcı kararı ve kapsam
Kullanıcı, başka sohbetlerce sahiplenilen GATE-02 geliştirmesini bu sohbette mükerrer oluşturmadan, bu sohbetin **merkezi entegrasyon ve kapanış koordinasyonu** yürütmesini kabul etti (`olur`). Bu karar **kaynak birleştirme, yeni GitHub Actions, geniş CI, yeni IAM grant, PostgreSQL/PROD, ücretli provider, main/product-dev yazma veya bağımsız kabul izni değildir**. Önceki H01 PR #4 ve PR #6 dar kapsamlı CI izinleri bağımsız kalır.

Bu turun konusu sadece mevcut dalların immutable GitHub tree/manifest karşılaştırması, görev sahipliği ve sıradaki kanıt kapılarının tanımlanmasıdır. Başka sohbetlere talimat iletilmedi; arka plan hizmeti başlatılmadı.

## Doğrudan kontrol edilen kaynaklar (GitHub recursive trees, `truncated=false`)
| Kaynak rolü | Commit SHA | Gerçek `product/` blob | `product/SOURCE_MANIFEST.json` girdisi | Manifest Git blob |
| --- | --- | ---: | ---: | --- |
| Kanonik ürün, henüz build HOLD | `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` | 505 | 504 | `07f1fc919daa6dd3d7ffad7b67c3e9eebcd5d276` |
| Ortak kaynak adayı | `integration/mi-common-source-review-01@4035d1a884362dae56a60d91358ea6e8e7dc0cdd` | 539 | 538 | `03af243e8683f92c5d9c0b24e90b70d2bd6af29f` |
| Core–ORG kaynak adayı | `integration/mi03-gate03-org-runtime-closure-01@d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` | 553 | 552 | `27b4eb5816265d4e6e6d2458acb6220db7dd0c76` |
| PR #6 özgün Core+OperationsStore test adayı (gözlem anındaki head) | `review/mi03-gate02-core-positive-20261119@0f1dc66a84126c5e892d8d517ec23ed8f859a772` | 554 | Sahip incelemesi bekliyor | Ayrı başvuru |

### Delta A: kanonik ürün → ortak kaynak
`product/` farkı: **35 eklenen, 1 kaldırılan, 14 Git blob değişen**. Güncel küme 539; 505+35-1=539. Modüller Model Gateway/Memory, Core identity adapter, UI organization/workflow/skill ile ortak manifesti etkiler. Kaynak farkının sıfır çakışmalı olduğu ileri sürülmez; kaynak sahibinin onayı, taşınan mevcut sözleşmeler, tarihsel sürüm pinleri ve tam W8 testi hâlâ gerekir. Silinen `features/workflow/DraftInspector.tsx` / eklenen `WorkflowDraftInspector.tsx` nedeniyle eski import ve API uyumu kontrol edilmelidir.

### Delta B: ortak kaynak → Core–ORG adayı
`product/` farkı: **14 eklenen, 0 kaldırılan, 1 değişen (yalnız `SOURCE_MANIFEST.json`)**. Eklenen dosyalar:
- `product/ai-company-os-backend/assignment_lifecycle.py`
- `product/ai-company-os-backend/assignment_review.sql`
- `product/ai-company-os-backend/durable_ops.py`
- `product/ai-company-os-backend/integration_guard.py`
- `product/ai-company-os-backend/office_bridge.py`
- `product/ai-company-os-backend/operations.py`
- `product/ai-company-os-backend/operations.sql`
- `product/ai-company-os-backend/org_core_bridge.py`
- `product/ai-company-os-backend/org_model.py`
- `product/ai-company-os-backend/persistence.py`
- `product/ai-company-os-backend/schema.sql`
- `product/ai-company-os-backend/staffing.py`
- `product/ai-company-os-backend/tests/test_org_runtime_packaging_mi03.py`
- `product/ai-company-os-backend/tests/test_org_sql_runtime_mi03.py`

**Git tree düzeyinde mevcut dosyalar üzerine doğrudan yazma çakışması yoktur**, ama eski G9 özgün `durable_ops.py` sahibinin pin/version ayrımı, ORG authority issuance ve 552 girdili manifest owner ratifikasyonu **HOLD**. Dosya adı aynı/önceden başka dalda mevcut olabileceğinden semantik çakışmasız veya onaylanmış birleşim demek değildir.

## Paralel hat ve kanıt ayrımı
| Kapı | Sahip / çalışma hattı | Son kanıt | Kalan |
| --- | --- | --- | --- |
| GATE-03 D0 Core–OperationsStore | MI-03 / MI-06; PR #6 | [GitHub run 44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705) **özgün 10/10 PASS**; güncel PR6 tekrar koşumları yeni metot sayılmaz | Gerçek GATE-02 owner issuance; PostgreSQL/IV |
| GATE-02 IAM/ORG sahiplik | MI-02/03 + D4/G8/ORG sahipleri | izolasyon 20/20, seçili 79/79 | gerçek registry/member/role/assignment issuer, G9 kaynak sahipliği, **old DB+old pin restore bypass yeniden üretildi**; P02 |
| GATE-01 Authority/T1 | MI-03/04 ve Model/Memory sahipleri | sınırlı PR #4 [CI run 44620987573](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620987573) üç iş PASS; D0 seçili 42/42 | özgün G2 50, G9 7, Memory T1 0214 10, gerçek korumalı zincir |
| GATE-04 strict COMMIT/restore | MI-02/04 + bağımsız IV | kaynak/izolasyon regresyonları | gerçek PostgreSQL, rollback, restore ve bağımsız latest-witness |
| GATE-05 unified W8 / native U3 | MI-01/MI-10, UI owner | sınırlı build/typecheck ve SSE-compatible browser; 1953-file immutable source audit | W8 original fullchain, native browser freshness, owner-approved build staging; product-dev değişmedi |

Bunlar farklı test sınırlarıdır. Seçili/replayed kanıtı tekrar sayma; sentetik D0 için gerçek IAM authority/grant/production kabul çıkarımı yapma.

## Geliştirme, kabul ve güvenlik
Ortak `15/35/20/20/10` ağırlıklı ilerleme için tüm ürün grupları ve kanıt paydaları nihai dondurulmadı: **global gelişim yüzdesi HESAPLANAMADI**. IAM/ORG tarihsel ölçüm **42.5% → 42.5% (Δ0pp)**; kanonik Core kabul **12/16 (75%)**; MVP kabul **0/11 (0%)**. Bu turda **0** özgün test, **0** uygulama kaynak değişikliği, **0** DB/API sözleşme değişikliği, **0** yetki/branch merge; ürüne kabul ilerleme değişimi **0**.

## Merkez için çakışmasız sıradaki iş ve kabul şartı
1. **CTL-01 (merkezi/salt okunur):** 14 additive Core/ORG dosyasını, özgün G9 `durable_ops.py` owner pinini ve iki manifesti dosya/simge/API/DB/bağımlılık düzeyinde bağımsız inceleme; onaylanmamış alternatif kaynak için HOLD. GATE02 koduna müdahale etme.
2. **CTL-02 (sahipler):** MI-02/03 GATE02 gerçek kayıt veren otorite, üyelik, rol, revocation/restore ve P02 kaynak kanıtlarını bitirsin; mevcut 79/79 veya 10/10 tekrar yazılmasın.
3. **CTL-03 (sahipler):** MI-03/04 özgün G2/G9/Memory–T1, MI-02/04 PG, MI-01/10 W8; her sonuç exact owner SHA, araç/run ID, çevre, kapsam, negatif güvenlik kanıtı ve bağımsız kabul ayrımıyla teslim edilsin.
4. **CTL-04 (merkezi):** ancak owner concurrence, source manifest/fingerprint, regresyon/build, security gate ve uygun ayrı yetki mevcutsa source promotion adayı değerlendirilir; aksi halde `integration/product-dev` ve `main` HOLD.

## Bakım, teşhis, geri dönüş ve devir
GitHub recursive trees'den `truncated=false` denetimiyle immutable SHA bazında `product/` **blob set** farkı oluştur; manifest `files` uzunlukları 504/538/552'yi denetle. Sadece dosya sayısı geçmişi/çalışan uygulamayı kanıtlamaz; yeni SHA gelince diff'i yeniden hesapla. Orijinal test koşumlarını yineleme. Başarısız yeni birleşimde kaynak sahibinin değişiklikleri ters commit ile ayrı incele; force push/PR merge yok. Bu belge ve `progress/MASTER_INTEGRATION_CURRENT.json` alanı yalnız koordinasyon kanıtıdır, product source veya kabul kaydı değildir.
