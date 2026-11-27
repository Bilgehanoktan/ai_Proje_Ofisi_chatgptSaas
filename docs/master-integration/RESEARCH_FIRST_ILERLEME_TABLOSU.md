# AI Company OS — Proje ilerleme tablosu

Son güncelleme: 2026-11-28 · Revizyon 1 · Tek aday `645c081e2cc107440662600b749d34415ad2f713`.

Kaynak: [RESEARCH_FIRST_ILERLEME_TABLOSU.json](../../progress/RESEARCH_FIRST_ILERLEME_TABLOSU.json) · [40 başlıklı özgün plan](RESEARCH_FIRST_INTEGRATION_PLAN_20261128.md) · [son teknik kanıt](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/645c081e2cc107440662600b749d34415ad2f713/catalog/revisions/H01_UNIFIED_SOURCE_RECONCILIATION_20261128.json).

**Geliştirme: HESAPLANAMADI.** Onaylı aşama paydaları yok. 12 operasyonel görevin 0/12 tam kapanışı; UI21/40, Core12/16, MVP0/11, W8 3/8, IV0/7; kabul delta 0. 593 ürün dosyası, 592/592 yol/boyut eşleşmesi; tam raw SHA256 ve arşiv açık. D0 ve tarihsel kanıtlar gerçek kabul değildir. Gönderilen örneğin yalnız tablo yapısı kullanıldı; başka projeye ait yüzdeler/kanıtlar taşınmadı.

## 12 operasyonel görev — günlük yönetim

| Alan | Gelişim | Durum | Hazır olan | Eksik olan | Sıradaki iş |
| --- | --- | --- | --- | --- | --- |
| 01 — RESEARCH kaynak uzlaştırması (Merkezi entegrasyon) | HESAPLANAMADI | DEVAM | 593 dosya; 592/592 yol/boyut; 7 kaynak grubu. | D5-C-R8/PR46 birleşimi, kalan işlev farkları ve arşiv. | Exact birleşim ve doğrulanabilir kaynak aktarımı. |
| 02 — PR #10, #46, #52 kararları (MI-02/03/04 ve bağımsız MI-10) | HESAPLANAMADI | HOLD | Teknik inceleme kayıtlı; PR46 D0 kaynakları mevcut. | Bağımsız review, gerçek IAM/otorite ve dependency kararları. | Yetkili reviewer ve exact PR disposition. |
| 03 — A1 fiziksel WorkItem/Project (MI-02/03/04) | HESAPLANAMADI | HOLD | A1 tasarım yönü ve mantıksal eşleme. | Nihai schema, custody, RLS ve migration kararı. | Fiziksel eşlemeyi mevcut store ile kesinleştir. |
| 04 — RESEARCH WorkType yayını (H01 / QA / IV) | HESAPLANAMADI | HOLD | 8/8 tarihsel pin ve paket digest doğrulandı. | QA/IV/H01 exact yayın ve ayrı binding. | Mevcut paket üzerinden yayın kararı. |
| 05 — Gerçek HUMAN IAM ve Project (MI-03/04) | HESAPLANAMADI | HOLD | D0 session/ORG review kaynakları. | Gerçek issuer, güncel create/read permission. | Yetkili kimlik ve proje otoritesine bağla. |
| 06 — HUMAN WorkItem / T1 (MI-02/04) | HESAPLANAMADI | HOLD | Taslak ve strict transport deny guard. | Typed protected operation ve ortak ön kontrol. | D5-C-R8/PR46 no-fallback birleşimi. |
| 07 — PostgreSQL ve readback (MI-02/04) | HESAPLANAMADI | HOLD | Altı rol ve mantıksal readback sözleşmesi. | Gerçek kalıcı COMMIT, aynı-ID, restart, RLS. | Onaylı mapping ve protected DB bağlantısı. |
| 08 — CEO Paneli / Backend (MI-05/06) | HESAPLANAMADI | KISMEN HAZIR | Sabit plan seçimi ve panel mevcut. | Gerçek command ve readback; submit/read devre dışı. | Yetkili API ile gerçek kayıt gösterimi. |
| 09 — Orchestrator / Scheduler (Core / Runtime) | HESAPLANAMADI | KISMEN HAZIR | Mevcut DAG/Scheduler; D0 7 görev 6 dalga. | Kalıcı WorkItem ve gerçek admission bağlantısı. | Aynı WorkItem'a plan ve scheduler bağla. |
| 10 — Runtime / Model / Skill / Memory (MI-03/07/08/09) | HESAPLANAMADI | DEVAM | Güncel motor kaynakları ve korumalar mevcut. | Gerçek grant/lease/budget, retrieval ve yürütme. | Yetkili Runtime bağını mevcut motorlara kur. |
| 11 — Sonuç / QA / IV / Office (MI-02/05/06/10) | HESAPLANAMADI | KISMEN HAZIR | Mevcut D0 plan ve projection kaynakları. | Gerçek sonuç, bağımsız denetim ve ofis durumu. | Kalıcı sonuç ve gerçek event projection. |
| 12 — Zorunlu doğrulama ve kabul (MI-01/10 / H01) | HESAPLANAMADI | HOLD | Önceki geçerli kanıtlar ve E01–E10 kaydı. | Zorunlu gerçek doğrulama ve bağımsız kabul. | Kapıları yetkili sırayla kapat. |

## Özgün 40 plan başlığı — ayrıntılı takip

| Alan | Gelişim | Durum | Hazır olan | Eksik olan | Sıradaki iş |
| --- | --- | --- | --- | --- | --- |
| 01 — Başlangıç ve kaynak otoritesi | HESAPLANAMADI | AKTİF | Dört merkezi dal HEAD ve plan referansları doğrulandı. | Tam Design Master eklerinin ve kalan arşivin uzlaştırması açık. | Her tur exact SHA, sahiplik ve etkilenen kaynak kontrolü. |
| 02 — Ana yön ve mimari | HESAPLANAMADI | PLAN KAYITLI | RESEARCH-first yönü, tek WorkItem ve mevcut motorlar kayıtlı. | Gerçek uçtan uca ürün zinciri çalışır olarak kabul edilmedi. | Önce CEO–IAM–T1–readback dilimini kapat. |
| 03 — Tek ürün ağacı | HESAPLANAMADI | DEVAM | 593 dosya, 592/592 yol/boyut, 7 teknik kaynak grubu; üç özgün kaynak önceki turda aktarılmış. | D5-C-R8/PR46 ortak davranış, kalan farklı sürümler, tam arşiv ve tüm raw hash kontrolü. | Exact kaynak birleşimini değerlendir; yalnız doğrulanabilir kaynakları aktar. |
| 04 — CEO talebi — MI-05/06 | HESAPLANAMADI | KISMEN HAZIR | ResearchRequestPanel, gözleme bağlı sabit plan seçimi ve dört alanlı D0 komut sözleşmesi. | Yetkili proje, POST ve gerçek kayıt; gönderim devre dışı. | Yetkili komut sözleşmesine bağla; kapılar açıkken etkinleştirme. |
| 05 — HUMAN IAM — MI-03/04, PR46 | HESAPLANAMADI | HOLD | D5-G1/G2 ve PR46 D0 SessionClaimCheck mevcut. | Gerçek issuer/custody, HUMAN create/read izni ve bağımsız inceleme. | PR46 gerçek IAM otoritesi ve proje iznini kesinleştir. |
| 06 — ORG ve Project — MI-02/03/06 | HESAPLANAMADI | HOLD | ORG D0 okuma ve G4/G5 referans inceleme kaynakları mevcut. | Gerçek Project otoritesi, WorkOwner, üyelik ve güncel revizyon. | A1 Project otoritesini ve IAM/ORG bağını kesinleştir. |
| 07 — RESEARCH WorkType yayını — H01/katalog sahibi/QA/MI-10 | HESAPLANAMADI | HOLD | RESEARCH@mvp03-request-1-rc1 paket 4107 byte; 8/8 tarihsel pin, içerik/provenance digest doğrulandı. | QA/IV exact sürüm, H01 yayın kararı ve ayrı scope binding/entitlement. | Mevcut paket kimliğiyle yayın incelemesini tamamla. |
| 08 — Fiziksel veri modeli — MI-02/03/04 | HESAPLANAMADI | HOLD | A1 tasarım yönü ve Project/WorkType/WorkItem mantıksal eşlemesi. | Nihai PK/FK/DDL, RLS, veri sahibi ve bağımsız otorite; migration izni. | Mevcut eşdeğerleri araştır, fiziksel sözleşmeyi kesinleştir. |
| 09 — Mevcut T1 Coordinator — MI-02/04 | HESAPLANAMADI | HOLD | WorkItem taslağı, altı rol readback ve mevcut strict PostgreSQL deny guard. | Typed HUMAN protected COMMIT; D5-C-R8 ve PR46 birleşimi; D03/D04. | Mevcut Coordinator ve Authority içinde no-fallback birleşimini hazırla; zorunlu kanıt kapısı. |
| 10 — Idempotency/fencing/recovery | HESAPLANAMADI | HOLD | D0 digest/fence ve UNKNOWN inceleme sözleşmeleri mevcut. | Kalıcı WorkItem idempotency, absent-head CAS, restore ve gerçek readback. | Onaylı fiziksel eşleme üzerinde fence ve recovery sözleşmesini bağla. |
| 11 — Backend komut/geri okuma — MI-02/03/05 | HESAPLANAMADI | HOLD | D0 binder ve mevcut salt okunur demo API. | Yetkili ayrı POST/GET, gerçek 201 ve aynı-ID readback; replay kararı. | HUMAN/Project/T1 kapılarıyla mevcut backend komutunu bağla. |
| 12 — CEO paneli ilk gerçek geri okuma — MI-05/06 | HESAPLANAMADI | HOLD | ResearchRequestPanel geri okuma alanı ve plan seçimi mevcut; submit/read disabled. | Gerçek request ID ve reload/restart sonrası yetkili okuma. | Protected COMMIT sonrası gerçek API geri okumasını bağla. |
| 13 — Orchestrator — MI-02/04 | HESAPLANAMADI | KISMEN HAZIR | Mevcut engine.py ve research_command_review.py sabit plan binder. | Kalıcı WorkItem, approved plan ve kalıcı durum ilişkisi. | İlk görev kaydına mevcut Orchestrator'ı bağla. |
| 14 — DAG | HESAPLANAMADI | KISMEN HAZIR | PR54 DAG kaynakları mevcut; D0 7 görev/6 dalga. | Gerçek Task/WorkItem ilişkisi, yetkili yürütme ve event kaydı. | Mevcut DAG'ı kalıcı plan revizyonuna bağla. |
| 15 — Scheduler | HESAPLANAMADI | KISMEN HAZIR | Scheduler state/version guard korunuyor; PR54 kaynakları mevcut. | Gerçek AGENT admission, kapasite/bütçe, dispatch ve retry. | WorkItem planıyla mevcut Scheduler bağlantısını hazırla. |
| 16 — Agent Runtime — MI-03/04/07 | HESAPLANAMADI | HOLD | Runtime, admission ve D0 okuma kaynakları mevcut; paired read guard aktarılmış. | Gerçek agent grant/lease, RunAdmission/T1 ve lifecycle. | Ayrı AGENT admission ve mevcut Runtime sözleşmelerini bağla. |
| 17 — Model Gateway — MI-07 | HESAPLANAMADI | DEVAM | PR53 router, registry ve recovered-memory sample adapter kaynakları korunuyor. | Gerçek yetkili sağlayıcı, model/maliyet ve Runtime yürütme. | Mevcut model bağlantısını WorkItem/AgentRun bağlamında uzlaştır. |
| 18 — Skill/Tool — MI-09 | HESAPLANAMADI | DEVAM | PR55 daha sıkı exact SourcePin/string kontrolleri mevcut. | Gerçek skill/tool kullanım yetkisi ve sonuç/evidence. | Mevcut resolver ve Tool Gateway'i yetkili Runtime'a bağla. |
| 19 — Memory/Knowledge — MI-08 | HESAPLANAMADI | DEVAM | MEM05E Runtime, signed history, snapshot lineage korumaları mevcut. | Yetkili retrieval, T1 kalıcı WorkItem sonucu, gerçek scope. | Memory/Model ve kalıcı sonuç sözleşmesini aynı görevde birleştir. |
| 20 — Finance/Budget (MVP minimum) | HESAPLANAMADI | KISMEN HAZIR | D0 task_budget_snapshot ve paired read guard kaynakları mevcut. | Gerçek bütçe rezervasyonu, settlement ve maliyet kaydı. | Admission ve T1 budget bağını mevcut policy ile tamamla. |
| 21 — QA | HESAPLANAMADI | HOLD | D0 referans planında QA adımı ve kalite kapısı tanımlı. | Gerçek araştırma çıktısı, WorkItem-bound QA kararı ve kanıt. | Gerçek çıktı üretilince mevcut QA zincirini bağla. |
| 22 — Security/Independent Verifier — MI-10 bağımsız | HESAPLANAMADI | HOLD | PR10/46/52 teknik incelemesi; mevcut bağımsız kabul kuralları korunuyor. | Son kayıtta üç PR'da 0 review; MI10, custody, D03/D04 ve bağımsız kararlar. | Yetkili bağımsız incelemeci ve exact PR kararları. |
| 23 — Event Store / Projection | HESAPLANAMADI | KISMEN HAZIR | Event Store/Outbox ve D0 projection kaynakları mevcut. | Gerçek WorkItem/AgentRun olayları, non-dispatch ayrımı ve ortak read model. | Korumalı kayıttan gerçek olay tüketimine bağla. |
| 24 — CEO Command Center | HESAPLANAMADI | KISMEN HAZIR | Dashboard, mevcut source summary ve RESEARCH paneli; plan/ORG shared read. | Gerçek görev, sonuç, maliyet, QA/IV ve yetkili durum. | İlk aynı-ID readback ve gerçek projection. |
| 25 — 2.5D Office | HESAPLANAMADI | KISMEN HAZIR | Mevcut Office kaynakları ve ortak ORG/plan okuma kontrolleri; JOIN_HOLD. | Gerçek AgentInstance–workstation ve event projection. | Yetkili gerçek olaylarla ofis görünümünü bağla. |
| 26 — Diğer Studio (paralel, kritik yol değil) | HESAPLANAMADI | PARALEL | Güncel Project/Workflow Studio plan read/reset ve shared projection kaynakları korunuyor. | Diğer Studio alanlarının gerçek ortak backend bağlantıları. | RESEARCH kritik yolunu bekletmeden bağımsız uygun Studio işi. |
| 27 — Çalışma ortamı — MI-01/MI-10/Codex | HESAPLANAMADI | HOLD | Frontend lock, PR52 R9 20 paket ve C50/R9 25 paket adayları incelendi. | FastAPI 0.163.0→0.163.2 ve cryptography 46.0.4→50.0.2 owner/security/runtime/lisans kararı; onaylı ortam. | Exact lock kararları; onaysız install yok. |
| 28 — Doğrulama sınırı | HESAPLANAMADI | AKTİF | Yeni rutin test yok; önceki kanıt ayrımı ve 592/592 yol/boyut kontrolü. | Tam arşiv ve tüm raw SHA-256; değişen davranışın zorunlu doğrulaması. | Sadece ilgili zorunlu kapıyı izinli kapsamda kapat. |
| 29 — Mevcut MVP-03 E01–E10 | HESAPLANAMADI | HOLD | E01/E03/E10 NOT_RUN, E02/E04–E09 HOLD; D0 kanıtları ayrı. | Gerçek E01–E10 kabulü. | İlk korumalı RESEARCH akışını exact oracle ile doğrula. |
| 30 — W8 | HESAPLANAMADI | HOLD | W8 3/8 kayıtlı; önceki dar kapsamlı kanıtlar korunuyor. | Kaynak sahibi/bağımlılık/lisans, resmi C07, gerçek C08, bağımsız C05. | Mevcut W8 zincirinde sıradaki izinli kapıyı kapat. |
| 31 — Plan içi 12 teslimat noktası | HESAPLANAMADI | PLAN KAYITLI | T01–T12 teslimat noktaları ve bağımlılık sırası mevcut. | Hiçbir bütün teslimatın kapanışı son kayıtta kanıtlanmadı. | Aynı planı 12 operasyonel görev ve 40 bölüm düzeyinde izle. |
| 32 — ChatGPT | HESAPLANAMADI | AKTİF | H01 merkezi teknik yazıcı yetkisi mevcut; 7 grup teknik inceleme kayıtlı. | Uygun gerçek kaynak değişiklikleri ve aktarım; bağımsız IV ayrı. | D5-C-R8/PR46 ve diğer uygulanabilir kaynak işlerini ele al. |
| 33 — Codex | HESAPLANAMADI | KISMEN HAZIR | Codex yerel geliştirme/kanıt rolü planlı; mevcut tarihsel ortam kanıtları korunuyor. | Güncel exact checkout ve onaylı lock/runtime ile gerekli yerel doğrulamalar. | Yetkili kapsam ve SHA bağlı görev devri. |
| 34 — H01 | HESAPLANAMADI | HOLD | H01 nihai karar ve dar RESEARCH yayın sahibi ataması mevcut. | Exact yayın, bağımsız reviewer/custody ve gerçekten yeni yetki kararları. | Yalnız eksik yeni H01 kararlarını sun; önceki izni tekrar isteme. |
| 35 — Başlangıç resmî kabul | HESAPLANAMADI | KAYITLI | UI21/40, Core12/16, MVP0/11, W8 3/8, IV0/7; son delta 0. | GOAL INTEGRATION ve genel gelişim için onaylı payda. | Her tur önceki/güncel/delta kanıtıyla güncelle. |
| 36 — Mevcut 11 MVP kriteri | HESAPLANAMADI | HOLD | 11 normatif MVP kabul kriteri planlı ve kayıtlı. | Gerçek kabul 0/11; her kriter ayrı kanıt gerektirir. | İlk RESEARCH kayıt/readback, ardından yürütme ve kabul. |
| 37 — Geliştirme metrikleri | HESAPLANAMADI | KAYITLI | 15/35/20/20/10 standardı ve üç ayrı metrik mevcut. | Görev bazlı onaylı aşama kriter/payda yok. | Kriter setlerini onayla; yoksa HESAPLANAMADI. |
| 38 — Genişleme | HESAPLANAMADI | SONRA / PARALEL | Diğer WorkType ve SaaS genişleme planı kayıtlı. | Gerçek kapsam/entegrasyon ve ayrı kabul; ilk MVP önkoşulu değil. | Bağımsız uygun kaynakları ilerlet; kritik yolu koru. |
| 39 — Hemen uygulanacak sıra ve engeller | HESAPLANAMADI | AKTİF | 12 operasyonel görev, P0 ortak engeller ve ilk kaynak incelemesi kayıtlı. | 01–12 tam kapanışları açık. | Önce D5-C-R8/PR46, A1 ve yayın/IAM/bağımsız kapılar. |
| 40 — Çalışma disiplini ve nihai hedef | HESAPLANAMADI | AKTİF | Tek izole aday, mevcut yetkiler ve son devir kaydı korundu. | Çalışan bütünleşik ürün, tam arşiv ve eksik kabul kanıtları. | Her anlamlı işte ilgili satır, exact SHA, kanıt ve delta güncelle. |

## Güncelleme disiplini

Her anlamlı geliştirmede ilgili JSON satırına tarih, önceki/güncel durum, exact SHA/kanıt, kanıt türü, onaylı pay/payda/delta (varsa), engel/sahip ve sonraki aksiyon kaydedilir. MD aynı JSON kaydından güncellenir. Eski sürümler Git geçmişinde korunur. 12 operasyonel görev, 40 plan başlığına referanstır; örtüşen kapsamlar ikinci kez sayılmaz. Onaylı kriterler bulunana kadar gelişim HESAPLANAMADI, kabul ayrı gösterilir. Yeni test, yetki, ürün kodu veya kabul bu kayıtla oluşturulmaz. 

Rollback: yalnız tablo/yönetişim commit'inin normal revert'i.
