# AI Company OS — Proje ilerleme tablosu

Son güncelleme: 2026-11-28 · Revizyon 2 · Tek aday `645c081e2cc107440662600b749d34415ad2f713`.

Kaynak: [JSON ve alt kriterler](../../progress/RESEARCH_FIRST_ILERLEME_TABLOSU.json) · [40 başlıklı özgün plan](RESEARCH_FIRST_INTEGRATION_PLAN_20261128.md) · [son teknik kanıt](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/645c081e2cc107440662600b749d34415ad2f713/catalog/revisions/H01_UNIFIED_SOURCE_RECONCILIATION_20261128.json).

**Plan gelişimi*** = kapanan açıkça tanımlı plan alt adımları / toplam alt adımlar. Yüzde bir ondalığa yuvarlanır. Revizyon 2 ilk ölçüm tabanıdır; yeni ürün kazanımı değildir. Alt adım kriterleri raporlama önerisi olarak sabitlenmiştir, H01 normatif aşama/payda onayı değildir. D0 ve tasarım adımı yalnız kendi dar kapsamını kapatır. Resmî ağırlıklı gelişim ve GOAL INTEGRATION HESAPLANAMADI. 12 görev 0/12 tam kapanış; UI21/40, Core12/16, MVP0/11, W8 3/8, IV0/7; kabul delta 0. 593 ürün dosyası, 592/592 yol/boyut; tam raw hash ve arşiv açık. Örtüşen operasyonel satırlar toplanmaz/ortalaması alınmaz.

## 12 operasyonel görev

| Alan | Plan gelişimi* | Durum | Hazır olan | Eksik olan | Sıradaki iş |
| --- | --- | --- | --- | --- | --- |
| 01 — RESEARCH kaynak uzlaştırması | %50 (3/6) | DEVAM | 593 dosya; 592/592 yol/boyut; 7 kaynak grubu. | D5-C-R8/PR46 birleşimi, kalan işlev farkları ve arşiv. | Exact birleşim ve doğrulanabilir kaynak aktarımı. |
| 02 — PR #10, #46, #52 kararları | %21,4 (3/14) | HOLD | Teknik inceleme kayıtlı; PR46 D0 kaynakları mevcut. | Bağımsız review, gerçek IAM/otorite ve dependency kararları. | Yetkili reviewer ve exact PR disposition. |
| 03 — A1 fiziksel WorkItem/Project | %22,2 (2/9) | HOLD | A1 tasarım yönü ve mantıksal eşleme. | Nihai schema, custody, RLS ve migration kararı. | Fiziksel eşlemeyi mevcut store ile kesinleştir. |
| 04 — RESEARCH WorkType yayını | %40 (2/5) | HOLD | 8/8 tarihsel pin ve paket digest doğrulandı. | QA/IV/H01 exact yayın ve ayrı binding. | Mevcut paket üzerinden yayın kararı. |
| 05 — Gerçek HUMAN IAM ve Project | %22,2 (2/9) | HOLD | D0 session/ORG review kaynakları. | Gerçek issuer, güncel create/read permission. | Yetkili kimlik ve proje otoritesine bağla. |
| 06 — HUMAN WorkItem / T1 | %33,3 (3/9) | HOLD | Taslak ve strict transport deny guard. | Typed protected operation ve ortak ön kontrol. | D5-C-R8/PR46 no-fallback birleşimi. |
| 07 — PostgreSQL ve readback | %27,8 (5/18) | HOLD | Altı rol ve mantıksal readback sözleşmesi. | Gerçek kalıcı COMMIT, aynı-ID, restart, RLS. | Onaylı mapping ve protected DB bağlantısı. |
| 08 — CEO Paneli / Backend | %31,3 (5/16) | KISMEN HAZIR | Sabit plan seçimi ve panel mevcut. | Gerçek command ve readback; submit/read devre dışı. | Yetkili API ile gerçek kayıt gösterimi. |
| 09 — Orchestrator / Scheduler | %30 (3/10) | KISMEN HAZIR | Mevcut DAG/Scheduler; D0 7 görev 6 dalga. | Kalıcı WorkItem ve gerçek admission bağlantısı. | Aynı WorkItem'a plan ve scheduler bağla. |
| 10 — Runtime / Model / Skill / Memory | %36,8 (7/19) | DEVAM | Güncel motor kaynakları ve korumalar mevcut. | Gerçek grant/lease/budget, retrieval ve yürütme. | Yetkili Runtime bağını mevcut motorlara kur. |
| 11 — Sonuç / QA / IV / Office | %31,8 (7/22) | KISMEN HAZIR | Mevcut D0 plan ve projection kaynakları. | Gerçek sonuç, bağımsız denetim ve ofis durumu. | Kalıcı sonuç ve gerçek event projection. |
| 12 — Zorunlu doğrulama ve kabul | %18,6 (8/43) | HOLD | Önceki geçerli kanıtlar ve E01–E10 kaydı. | Zorunlu gerçek doğrulama ve bağımsız kabul. | Kapıları yetkili sırayla kapat. |

## 40 özgün plan başlığı

| Alan | Plan gelişimi* | Durum | Hazır olan | Eksik olan | Sıradaki iş |
| --- | --- | --- | --- | --- | --- |
| 01 — Başlangıç ve kaynak otoritesi | %50 (2/4) | AKTİF | Dört merkezi dal HEAD ve plan referansları doğrulandı. | Tam Design Master eklerinin ve kalan arşivin uzlaştırması açık. | Her tur exact SHA, sahiplik ve etkilenen kaynak kontrolü. |
| 02 — Ana yön ve mimari | %33,3 (1/3) | PLAN KAYITLI | RESEARCH-first yönü, tek WorkItem ve mevcut motorlar kayıtlı. | Gerçek uçtan uca ürün zinciri çalışır olarak kabul edilmedi. | Önce CEO–IAM–T1–readback dilimini kapat. |
| 03 — Tek ürün ağacı | %50 (3/6) | DEVAM | 593 dosya, 592/592 yol/boyut, 7 teknik kaynak grubu; üç özgün kaynak önceki turda aktarılmış. | D5-C-R8/PR46 ortak davranış, kalan farklı sürümler, tam arşiv ve tüm raw hash kontrolü. | Exact kaynak birleşimini değerlendir; yalnız doğrulanabilir kaynakları aktar. |
| 04 — CEO talebi — MI-05/06 | %40 (2/5) | KISMEN HAZIR | ResearchRequestPanel, gözleme bağlı sabit plan seçimi ve dört alanlı D0 komut sözleşmesi. | Yetkili proje, POST ve gerçek kayıt; gönderim devre dışı. | Yetkili komut sözleşmesine bağla; kapılar açıkken etkinleştirme. |
| 05 — HUMAN IAM — MI-03/04, PR46 | %20 (1/5) | HOLD | D5-G1/G2 ve PR46 D0 SessionClaimCheck mevcut. | Gerçek issuer/custody, HUMAN create/read izni ve bağımsız inceleme. | PR46 gerçek IAM otoritesi ve proje iznini kesinleştir. |
| 06 — ORG ve Project — MI-02/03/06 | %25 (1/4) | HOLD | ORG D0 okuma ve G4/G5 referans inceleme kaynakları mevcut. | Gerçek Project otoritesi, WorkOwner, üyelik ve güncel revizyon. | A1 Project otoritesini ve IAM/ORG bağını kesinleştir. |
| 07 — RESEARCH WorkType yayını — H01/katalog sahibi/QA/MI-10 | %40 (2/5) | HOLD | RESEARCH@mvp03-request-1-rc1 paket 4107 byte; 8/8 tarihsel pin, içerik/provenance digest doğrulandı. | QA/IV exact sürüm, H01 yayın kararı ve ayrı scope binding/entitlement. | Mevcut paket kimliğiyle yayın incelemesini tamamla. |
| 08 — Fiziksel veri modeli — MI-02/03/04 | %20 (1/5) | HOLD | A1 tasarım yönü ve Project/WorkType/WorkItem mantıksal eşlemesi. | Nihai PK/FK/DDL, RLS, veri sahibi ve bağımsız otorite; migration izni. | Mevcut eşdeğerleri araştır, fiziksel sözleşmeyi kesinleştir. |
| 09 — Mevcut T1 Coordinator — MI-02/04 | %40 (2/5) | HOLD | WorkItem taslağı, altı rol readback ve mevcut strict PostgreSQL deny guard. | Typed HUMAN protected COMMIT; D5-C-R8 ve PR46 birleşimi; D03/D04. | Mevcut Coordinator ve Authority içinde no-fallback birleşimini hazırla; zorunlu kanıt kapısı. |
| 10 — Idempotency/fencing/recovery | %25 (1/4) | HOLD | D0 digest/fence ve UNKNOWN inceleme sözleşmeleri mevcut. | Kalıcı WorkItem idempotency, absent-head CAS, restore ve gerçek readback. | Onaylı fiziksel eşleme üzerinde fence ve recovery sözleşmesini bağla. |
| 11 — Backend komut/geri okuma — MI-02/03/05 | %25 (1/4) | HOLD | D0 binder ve mevcut salt okunur demo API. | Yetkili ayrı POST/GET, gerçek 201 ve aynı-ID readback; replay kararı. | HUMAN/Project/T1 kapılarıyla mevcut backend komutunu bağla. |
| 12 — CEO paneli ilk gerçek geri okuma — MI-05/06 | %25 (1/4) | HOLD | ResearchRequestPanel geri okuma alanı ve plan seçimi mevcut; submit/read disabled. | Gerçek request ID ve reload/restart sonrası yetkili okuma. | Protected COMMIT sonrası gerçek API geri okumasını bağla. |
| 13 — Orchestrator — MI-02/04 | %33,3 (1/3) | KISMEN HAZIR | Mevcut engine.py ve research_command_review.py sabit plan binder. | Kalıcı WorkItem, approved plan ve kalıcı durum ilişkisi. | İlk görev kaydına mevcut Orchestrator'ı bağla. |
| 14 — DAG | %33,3 (1/3) | KISMEN HAZIR | PR54 DAG kaynakları mevcut; D0 7 görev/6 dalga. | Gerçek Task/WorkItem ilişkisi, yetkili yürütme ve event kaydı. | Mevcut DAG'ı kalıcı plan revizyonuna bağla. |
| 15 — Scheduler | %25 (1/4) | KISMEN HAZIR | Scheduler state/version guard korunuyor; PR54 kaynakları mevcut. | Gerçek AGENT admission, kapasite/bütçe, dispatch ve retry. | WorkItem planıyla mevcut Scheduler bağlantısını hazırla. |
| 16 — Agent Runtime — MI-03/04/07 | %25 (1/4) | HOLD | Runtime, admission ve D0 okuma kaynakları mevcut; paired read guard aktarılmış. | Gerçek agent grant/lease, RunAdmission/T1 ve lifecycle. | Ayrı AGENT admission ve mevcut Runtime sözleşmelerini bağla. |
| 17 — Model Gateway — MI-07 | %50 (2/4) | DEVAM | PR53 router, registry ve recovered-memory sample adapter kaynakları korunuyor. | Gerçek yetkili sağlayıcı, model/maliyet ve Runtime yürütme. | Mevcut model bağlantısını WorkItem/AgentRun bağlamında uzlaştır. |
| 18 — Skill/Tool — MI-09 | %25 (1/4) | DEVAM | PR55 daha sıkı exact SourcePin/string kontrolleri mevcut. | Gerçek skill/tool kullanım yetkisi ve sonuç/evidence. | Mevcut resolver ve Tool Gateway'i yetkili Runtime'a bağla. |
| 19 — Memory/Knowledge — MI-08 | %50 (2/4) | DEVAM | MEM05E Runtime, signed history, snapshot lineage korumaları mevcut. | Yetkili retrieval, T1 kalıcı WorkItem sonucu, gerçek scope. | Memory/Model ve kalıcı sonuç sözleşmesini aynı görevde birleştir. |
| 20 — Finance/Budget (MVP minimum) | %33,3 (1/3) | KISMEN HAZIR | D0 task_budget_snapshot ve paired read guard kaynakları mevcut. | Gerçek bütçe rezervasyonu, settlement ve maliyet kaydı. | Admission ve T1 budget bağını mevcut policy ile tamamla. |
| 21 — QA | %33,3 (1/3) | HOLD | D0 referans planında QA adımı ve kalite kapısı tanımlı. | Gerçek araştırma çıktısı, WorkItem-bound QA kararı ve kanıt. | Gerçek çıktı üretilince mevcut QA zincirini bağla. |
| 22 — Security/Independent Verifier — MI-10 bağımsız | %20 (1/5) | HOLD | PR10/46/52 teknik incelemesi; mevcut bağımsız kabul kuralları korunuyor. | Son kayıtta üç PR'da 0 review; MI10, custody, D03/D04 ve bağımsız kararlar. | Yetkili bağımsız incelemeci ve exact PR kararları. |
| 23 — Event Store / Projection | %25 (1/4) | KISMEN HAZIR | Event Store/Outbox ve D0 projection kaynakları mevcut. | Gerçek WorkItem/AgentRun olayları, non-dispatch ayrımı ve ortak read model. | Korumalı kayıttan gerçek olay tüketimine bağla. |
| 24 — CEO Command Center | %33,3 (1/3) | KISMEN HAZIR | Dashboard, mevcut source summary ve RESEARCH paneli; plan/ORG shared read. | Gerçek görev, sonuç, maliyet, QA/IV ve yetkili durum. | İlk aynı-ID readback ve gerçek projection. |
| 25 — 2.5D Office | %33,3 (1/3) | KISMEN HAZIR | Mevcut Office kaynakları ve ortak ORG/plan okuma kontrolleri; JOIN_HOLD. | Gerçek AgentInstance–workstation ve event projection. | Yetkili gerçek olaylarla ofis görünümünü bağla. |
| 26 — Diğer Studio (paralel, kritik yol değil) | %33,3 (1/3) | PARALEL | Güncel Project/Workflow Studio plan read/reset ve shared projection kaynakları korunuyor. | Diğer Studio alanlarının gerçek ortak backend bağlantıları. | RESEARCH kritik yolunu bekletmeden bağımsız uygun Studio işi. |
| 27 — Çalışma ortamı — MI-01/MI-10/Codex | %25 (1/4) | HOLD | Frontend lock, PR52 R9 20 paket ve C50/R9 25 paket adayları incelendi. | FastAPI 0.163.0→0.163.2 ve cryptography 46.0.4→50.0.2 owner/security/runtime/lisans kararı; onaylı ortam. | Exact lock kararları; onaysız install yok. |
| 28 — Doğrulama sınırı | %50 (2/4) | AKTİF | Yeni rutin test yok; önceki kanıt ayrımı ve 592/592 yol/boyut kontrolü. | Tam arşiv ve tüm raw SHA-256; değişen davranışın zorunlu doğrulaması. | Sadece ilgili zorunlu kapıyı izinli kapsamda kapat. |
| 29 — Mevcut MVP-03 E01–E10 | %0 (0/10) | HOLD | E01/E03/E10 NOT_RUN, E02/E04–E09 HOLD; D0 kanıtları ayrı. | Gerçek E01–E10 kabulü. | İlk korumalı RESEARCH akışını exact oracle ile doğrula. |
| 30 — W8 | %37,5 (3/8) | HOLD | W8 3/8 kayıtlı; önceki dar kapsamlı kanıtlar korunuyor. | Kaynak sahibi/bağımlılık/lisans, resmi C07, gerçek C08, bağımsız C05. | Mevcut W8 zincirinde sıradaki izinli kapıyı kapat. |
| 31 — Plan içi 12 teslimat noktası | %50 (1/2) | PLAN KAYITLI | T01–T12 teslimat noktaları ve bağımlılık sırası mevcut. | Hiçbir bütün teslimatın kapanışı son kayıtta kanıtlanmadı. | Aynı planı 12 operasyonel görev ve 40 bölüm düzeyinde izle. |
| 32 — ChatGPT | %66,7 (2/3) | AKTİF | H01 merkezi teknik yazıcı yetkisi mevcut; 7 grup teknik inceleme kayıtlı. | Uygun gerçek kaynak değişiklikleri ve aktarım; bağımsız IV ayrı. | D5-C-R8/PR46 ve diğer uygulanabilir kaynak işlerini ele al. |
| 33 — Codex | %33,3 (1/3) | KISMEN HAZIR | Codex yerel geliştirme/kanıt rolü planlı; mevcut tarihsel ortam kanıtları korunuyor. | Güncel exact checkout ve onaylı lock/runtime ile gerekli yerel doğrulamalar. | Yetkili kapsam ve SHA bağlı görev devri. |
| 34 — H01 | %25 (1/4) | HOLD | H01 nihai karar ve dar RESEARCH yayın sahibi ataması mevcut. | Exact yayın, bağımsız reviewer/custody ve gerçekten yeni yetki kararları. | Yalnız eksik yeni H01 kararlarını sun; önceki izni tekrar isteme. |
| 35 — Başlangıç resmî kabul | %33,3 (1/3) | KAYITLI | UI21/40, Core12/16, MVP0/11, W8 3/8, IV0/7; son delta 0. | GOAL INTEGRATION ve genel gelişim için onaylı payda. | Her tur önceki/güncel/delta kanıtıyla güncelle. |
| 36 — Mevcut 11 MVP kriteri | %0 (0/11) | HOLD | 11 normatif MVP kabul kriteri planlı ve kayıtlı. | Gerçek kabul 0/11; her kriter ayrı kanıt gerektirir. | İlk RESEARCH kayıt/readback, ardından yürütme ve kabul. |
| 37 — Geliştirme metrikleri | %33,3 (1/3) | KAYITLI | 15/35/20/20/10 standardı ve üç ayrı metrik mevcut. | Görev bazlı onaylı aşama kriter/payda yok. | Kriter setlerini onayla; yoksa HESAPLANAMADI. |
| 38 — Genişleme | %25 (1/4) | SONRA / PARALEL | Diğer WorkType ve SaaS genişleme planı kayıtlı. | Gerçek kapsam/entegrasyon ve ayrı kabul; ilk MVP önkoşulu değil. | Bağımsız uygun kaynakları ilerlet; kritik yolu koru. |
| 39 — Hemen uygulanacak sıra ve engeller | %66,7 (2/3) | AKTİF | 12 operasyonel görev, P0 ortak engeller ve ilk kaynak incelemesi kayıtlı. | 01–12 tam kapanışları açık. | Önce D5-C-R8/PR46, A1 ve yayın/IAM/bağımsız kapılar. |
| 40 — Çalışma disiplini ve nihai hedef | %50 (2/4) | AKTİF | Tek izole aday, mevcut yetkiler ve son devir kaydı korundu. | Çalışan bütünleşik ürün, tam arşiv ve eksik kabul kanıtları. | Her anlamlı işte ilgili satır, exact SHA, kanıt ve delta güncelle. |

## Güncelleme disiplini

Each meaningful development updates only affected rows with date, old/new status, evidence exact SHA/path, stage criterion/payda/delta if approved, acceptance separate, owner/blocker and next action; render MD from same JSON; preserve unaffected rows and prior versions in Git; no speculative progress, no extra reports merely to raise counts. Operational section mapping is navigation only, not new scoring or normative IDs. Read current heads and table every round. Plan checklist IDs/denominators remain fixed unless explicitly revised with reason and old/new baseline; record before/after counts and percentage points; no acceptance inference.

Kriter kimlikleri ve kapanış koşulları JSON'da bulunur. Satır yüzdesi gerçek ürün kabulü değildir; resmî 15/35/20/20/10 kriterleri/payda onaylanınca ayrı ölçülür. Bu turda kod/test/ürün kabulü değişmedi. Rollback: yalnız yönetişim commit'inin normal revert'i.
