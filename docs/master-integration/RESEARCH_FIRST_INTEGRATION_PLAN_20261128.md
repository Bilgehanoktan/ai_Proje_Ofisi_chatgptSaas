# AI COMPANY OS — Detaylı ana entegrasyon ve geliştirme planı | 28.11.2026
Durum: H01'in planı kaydetme talebiyle sürümlenen uygulama planı. Yeni normatif mimari, yürütme izni, kabul, atama veya CI izni değildir. 21 alan, 63 alt modül, 24 teknik alan, 3 WorkType, 8 faz, özgün 8 hat, A–G ve MI-01–MI-10 korunur. Aşağıdaki 40 başlık ve T01–T12 yalnız plan içi takip etiketleridir; kanonik görev/kapı ID'lerini değiştirmez. Mevcut CEO/ADR/security kuralları üstündür.
 
## 1. Başlangıç ve kaynak otoritesi
- [ ] Her tur canlı HEAD, sahiplik, etkilenen tam Design Master ve ekleri, AGENTS, katalog, ADR/CEO, manifest, CURRENT/NEXT_STEP ve kanıtları denetle.
- Başlangıç gözlemi: product-dev `9acf778bc71568cdb20ea4298ce86ac539afe07d` (576 dosya/575 manifest); tek aday `integration/h01-r6-research-unified-20261127@4245b569797a2742579e4619a0e546d25281c0ca` (593 dosya/592 manifest, blob `4e0bd2dfc2265e191b1a5f008f3e541174b81c12`); raporlama `b6983047430cecde80a02c6384a22fe80301ad93`.
- Son aday kaydı: W1-0198-P09 üç özgün kaynak aktarımı (admission_sample.py, paired_read_guard.py, task_budget_snapshot.py), 2 güncelleme/1 ek; D0 read guard. Tarihsel 39/39 raporlanmış; son aktarımda test NOT_RUN. Kaynak: adayın catalog/revisions/H01_UNIFIED_SOURCE_RECONCILIATION_20261128.json. 350 ref karşılaştırması kayıtlı; tüm farklı sürümlerin işlevsel incelemesi tamamlanmış değil.
- Bu sayılar başlangıç referansıdır; yeni turda canlı HEAD kullan.

## 2. Ana yön ve mimari
- Önce RESEARCH kritik kaynakları → CEO → API/IAM/ORG → WorkType/Project/WorkItem → mevcut T1/PostgreSQL → yetkili aynı-ID geri okuma/CEO.
- Ardından aynı WorkItem'a Orchestrator → DAG → Scheduler → ayrı AGENT admission/Runtime → Model/Skill/Tool/Memory → korumalı sonuç/Evidence → QA → bağımsız IV → H01/CEO/Office projection.
- Security/Policy/Budget/Audit/tenant izolasyonu tüm zinciri kapsar. Tüm tarihsel dallar, Studio ve SaaS tamamlanması ilk dilimin önkoşulu değildir. İlk kalıcı görev kayıt dilimi tam MVP kabulü değildir. Mevcut motorları yeniden kullan; ikinci runtime/transaction engine ve sahte başarı yok.

# A. Kaynak uzlaştırması — P0, merkezi yazıcı MI-01–09
## 3. Tek ürün ağacı
- [ ] Canlı aday/product-dev ve ilgili aktif PR başlarını, yetkili tek yazıcı ve çakışmaları denetle; yeni aday/dal açma.
- [ ] RESEARCH için Dashboard/ResearchRequestPanel, API, IAM/ORG, Project/WorkItem/WorkType, T1/Postgres/Event/Outbox, Orchestrator/DAG/Scheduler/Runtime, Model/Skill/Tool/Memory, Evidence/QA/IV/Projection bağımlılık envanterini oluştur.
- [ ] 350 ref mevcut envanterini tekrar sıfırdan üretme. Farklı sürümleri path/blob/byte/SHA256 ve sınıf/fonksiyon/API/DB/event/import/bağımlılık düzeyinde incele. Güncel Studio ve daha sıkı güvenliği koru; mükerrer ve superseded kaynakları ayıkla, eksik işlevleri tespit et.
- [ ] PR10 fiziksel authority; PR19/31 IAM/ORG/G2/G9; PR46 gerçek IAM/T1; PR47 API; PR45/48/49 CEO/Office; PR50/51 MIME; PR52 C50/R9; PR53/54 router/scheduler mevcut; PR55 resolver; 0172-R12 legacy readback; MEM05E Runtime/Memory/Authority sürümlerini ilgili kapsamda uzlaştır.
- [ ] Bağımsız uygun kaynakları aktar; zorunlu kanıtı eksik olan değişikliği HOLD tut; tarihsel/karantina kaynaklarını yanlışlıkla ürünleştirme.
- [ ] Tek SOURCE_MANIFEST, tam path/blob/byte/SHA256, bağımlılık ve mevcut kanıt pinleri; teknik katalog/devir, expected-parent non-force commit, GitHub SHA/tree readback, tam arşiv ve rollback. Tam arşiv yoksa açıkça HOLD/eksik yaz.
Çıkış: RESEARCH için uygun kaynak kapanışı, ayrıştırılmış HOLD ve doğrulanmış tek manifest.

# B. İlk ürün dilimi — CEO'nun yetkili görev kaydı
## 4. CEO talebi — MI-05/06
- [ ] Mevcut Dashboard ve ResearchRequestPanel; yetkili proje seçimi, RESEARCH, plan ve revizyon gösterimi, giriş doğrulaması, çift gönderim önleme, gönderim/geri okuma ve HOLD/hata durumları.
- [ ] Yalnız onaylı dört alan: worktype, project_ref, plan_ref, expected_plan_revision; ayrı Idempotency-Key header. Tenant/company/environment/principal/project_revision/worktype_version/workowner_ref/approval sunucu otoritesinden; tarayıcıdan güvenilir kabul edilmez.
- [ ] Yetkili komut ve geri okuma doğrulanmadan butonu etkinleştirme.
Çıkış: mevcut arayüzden doğru kapsamlı yetkili talep, sahte başarı yok.

## 5. HUMAN IAM — MI-03/04, PR46
- [ ] iam_session.py ve D5-G1/G2/G7 sözleşmelerini uzlaştır; gerçek issuer/root/custody, HUMAN ve AGENT ayrımı, H01 principal, session geçerlilik/expiry/revoke, scope ve role/grant/policy ilişkisi.
- [ ] Project create/read izinlerini ayrı doğrula; güncel üyelik ve yetki, iptal/expiry COMMIT ve readback'e yansısın; caller kimliği güvenilir sayılmasın; tenant/proje erişim sınırı korunsun. HUMAN'a sahte agent grant/lease yok.
Çıkış: gerçek sunucu doğrulamalı HUMAN ve proje yetkisi. Gerçek issuer/provenance ve bağımsız inceleme HOLD.

## 6. ORG ve Project — MI-02/03/06
- [ ] Tenant/Company/Environment ve üyelik/ORG revision; yetkili Project otoritesi, head/immutable revision, create/read yetkisi, tek WorkOwner ve onaylı proje politikası.
- [ ] Plan proje bağı, plan approval, stale revision reddi, Project revision ile ORG revision ayrımı; Project Studio ortak kimlikleri.
Çıkış: yetkili şirket/proje/WorkOwner kapsamı; gerçek otorite olmadan HOLD.

## 7. RESEARCH WorkType yayını — H01/katalog sahibi/QA/MI-10
- [ ] Mevcut research.worktype.publication_candidate.json, RESEARCH@mvp03-request-1-rc1, content/provenance digest, source commit/manifest ve sabit D0 plan referansı. D0 plan gerçek onay değildir.
- [ ] Dört giriş alanı ve scope; QA ve bağımsız IV exact version incelemesi; içerik değişirse immutable yeni sürüm önerisi.
- [ ] Gerçek yayın custody/decision kaydı, H01 exact sürüm yayın kararı, WorkTypeVersion; ayrı tenant entitlement/scope binding, gerektiğinde G8. Yayın, G7/G8, AGENT admission ayrı; silent upgrade yok.
Çıkış: yetkili yayımlanmış sürüm ve kapsam kullanım kanıtı. H01 dar yayın sahibi ataması tamam; specific release HOLD. Tekrar atama istenmez.

# C. Core/T1/PostgreSQL — P0
## 8. Fiziksel veri modeli — MI-02/03/04
- [ ] Mevcut yetkili eşdeğerleri ara ve yeniden kullan. A1 yönü onaylı; nihai DDL ve gerçek otorite onaylanmamış.
- [ ] Önerilen project_heads, project_revisions: kapsam PK/FK, immutable revision ve WorkOwner/policy, current head.
- [ ] Önerilen worktype_versions, worktype_scope_bindings: immutable version/content digest, publication/entitlement/activation, binding revision/digest, revoke.
- [ ] Önerilen workitem_heads: scoped request ID, Project revision, WorkType/version/binding, plan approval, HUMAN creator/issuer/session/authz, policy/witness, WorkOwner, immutable creation anchor ve transaction/digest.
- [ ] PK/FK/unique/CAS, ayrı RUN ve WORKITEM discriminated eşleme; mevcut run constraint'lerini zayıflatma; RLS ENABLE+FORCE, least privilege non-owner/non-BYPASSRLS, güvenilir server scope. Yetkili DBA/owner ve MI10 incelemesi, migration/rollback planı.
Çıkış: onaylı fiziksel ve otorite sözleşmesi; migration/real DB ayrı kapı.

## 9. Mevcut T1 Coordinator — MI-02/04
- [ ] review.py, port.py, intent_authority.py, readback_review.py; WorkItemRequestDraft'tan onaylı typed HUMAN WORKITEM_REQUEST işlemine geçiş. AGENT ADMISSION ayrı; sahte run/grant/lease/budget ve generic bypass yok.
- [ ] HEAD/MUTATION/FENCE/EVENT/OUTBOX/AUDIT operation-specific completeness, aynı transaction ve request digest/immutable creation anchor; kısmi kayıt yok.
- [ ] Gerçek COMMIT anında yetki, revoke/expiry, D03 dış race/D04 restore, bağımsız root/sink fencing ve W-A/F0. Strict transport fail-closed korunsun.
- [ ] Tek korumalı transaction; write set doğrula, mismatch rollback; COMMIT sonrası fresh authorized consistent readback; belirsizlik UNKNOWN/HOLD.
Çıkış: gerçek korumalı kalıcı WorkItem yazma ve geri okuma; PR10/MI10 bağımsız kapısı.

## 10. Idempotency/fencing/recovery
- [ ] Opaque Idempotency-Key kapsamı, canonical request digest, creator/scope/operation namespace eşleşmesi; aynı key/same payload orijinal receipt, farklı payload conflict.
- [ ] Fence reservation ve absent-head CAS, concurrency, tekrar/duplicate önleme; bağlantı kopması ve restart aynı ID; restore/revoke/expiry bağımsız uzlaştırma; UNKNOWN otomatik yeniden deneme değil.

## 11. Backend komut/geri okuma — MI-02/03/05
- [ ] Salt okunur demo API korunur; ayrı yetkili POST/GET mevcut sözleşmeye bağlanır, dört alan validate, server IAM/ORG/Project/WorkType/plan, digest/fence/T1.
- [ ] HTTP201 yalnız verified protected COMMIT ve authorized readback. HTTP200 replay öneri/onay bekliyor; HTTP202 yalnız ayrı kalıcı AGENT admission; deny/conflict/HOLD/UNKNOWN fail-closed.
- [ ] GET fresh HUMAN read permission, scoped request ID, immutable creation C, tutarlı altı rol, current head ayrı; normal yetkili reader creator olmak zorunda değil; replay creator eşlemesi ayrı. GET mutation yok, tenant/existence leak yok.

## 12. CEO paneli ilk gerçek geri okuma — MI-05/06
- [ ] Gerçek request ID, WorkType/version/project/WorkOwner/durum/audit ref; reload ve restart aynı kalıcı görev, revocation deny, D0/historical/live ayrımı. Admission olmadan running gösterme.
- Çıkış (ilk ürün teslimatı): gerçek HUMAN ile yetkili RESEARCH talebi → korumalı PostgreSQL kaydı → aynı ID'li yetkili panel readback. E01–E10 kanıtı ayrı; ajan çalıştırma, tam MVP veya release değildir. Yürütme kaynak hazırlığı paralel, gerçek dispatch bu dilime ve kendi yetkilerine bağlı.

# D. Orchestrator, DAG ve Scheduler
## 13. Orchestrator — MI-02/04
- [ ] Mevcut engine.py/research_command_review.py; kalıcı WorkItem ve approved plan ilişkilendirme; scope/WorkOwner/revision/digest; yetkili plan oluşturma/kullanma, duplicate plan yok; kalıcı durum/hata/CEO projection.
## 14. DAG
- [ ] PR54 mevcut DAG, Task/WorkItem, dependency/acyclic/plan digest, scheduling waves, paralel görevler, predecessor fail/HOLD, Event Store. Sabit D0 referansı 7 görev/6 dalga: plan → (draft,research) → merge → qa → iv → release. Gerçek plan approval ve release ayrı.
## 15. Scheduler
- [ ] scheduler_review.py, plan revision, ready task, agent capability/role, budget/capacity, dedup, ayrı AGENT admission, no dispatch before admission, retry/recovery, Orchestrator/CEO state.
Çıkış: aynı kalıcı WorkItem ile yetkili plan ve bağımlılık sıralı yürütme.

# E. AI çalışanları
## 16. Agent Runtime — MI-03/04/07
- [ ] AgentDefinition/Instance, şirket/departman/takım/rol/principal, current grant/assignment.
- [ ] WorkItem/Task/AgentRun ilişkisi, admission/lease/fence/budget/permission ve durable T1; HUMAN request ayrı.
- [ ] Başlat/ilerleme/timeout/stop/cancel/revoke/lease/retry/recovery, terminal sonucu T1 ve scheduler/CEO/Office. Fake running yok.
## 17. Model Gateway — MI-07
- [ ] Registry/router PR53, profile/capability/fallback, WorkType/agent role/policy, Runtime ve IAM; runtime_model_review.py ve sample adapter uzlaştırması.
- [ ] Yetkili Memory context, token/cost, standart çıktı, hata/timeout, Evidence; gerçek sağlayıcı/harcama ayrı izin.
## 18. Skill/Tool — MI-09
- [ ] Registry/manifest/resolver, PR55 ve daha sıkı güncel source pin kontrolleri, version/provenance/license, agent capability/permission, WorkType vs G7/G8 ayrımı.
- [ ] Runtime/Tool Gateway/Policy, parametre, dış etki ayrı yetki, hata/çıktı/Evidence/maliyet. Firecrawl/Paperclip zorunlu değil.
## 19. Memory/Knowledge — MI-08
- [ ] Tenant/company/project/workitem/task/agent scope, retrieval permission, provenance, snapshot/revision.
- [ ] MEM05E Runtime/Memory/Model context ve Witness/restore/anti-replay.
- [ ] Sonuç ve revizyon/kanıt kalıcı kayıt, T1, yetkisiz yazma yok; Memory Studio aynı veri.

# F. Finans/QA/IV
## 20. Finance/Budget (MVP minimum)
- [ ] Company/project/task/agent/model limitleri; admission budget/reservation/T1, gerçek maliyet/settlement/release, dedup, limit fail-closed, panel. H01 olmadan harcama yok.
## 21. QA
- [ ] Mevcut QA, WorkType completion, eksik çıktı, claim/source/evidence, sonuç kalite, WorkItem-bound karar, fail → no release, Orchestrator düzeltme, karar/kanıt kalıcılığı. QA != IV.
## 22. Security/Independent Verifier — MI-10 bağımsız
- [ ] Yetkili bağımsız reviewer, exact PR10/46/52; F0/W-A/Witness/D03/D04/root custody, tenant/COMMIT/restore, dependency/license/security.
- [ ] QA çıktısı ve kaynaklar, model/tool/evidence, yetki/bütçe, provenance, sonuç kalıcılığı, bağımsız PASS/FAIL/HOLD, olumsuz karar no release, H01 ayrı. Merkezi teknik yazıcı bağımsız kabul vermez.

# G. CEO/Office ve Studio
## 23. Event Store / Projection
- [ ] WorkItem vs AgentRun olayları, request-recorded non-dispatchable, Outbox consumer, event order/revision, stale/offline/timeouts; ortak gerçek read model, yetki kapsamı.
## 24. CEO Command Center
- [ ] Şirket/proje/WorkItem, DAG, görev/ajan/Runtime, maliyet, HOLD, sonuç, QA/IV/H01; gerçek hata ve provenance, sahte animasyon yok.
## 25. 2.5D Office
- [ ] Mevcut layout/kat/departman, AgentInstance-workstation, gerçek assignment/runtime/wait/HOLD/terminal/handoff/QA/IV, offline freshness. Read-only projection otorite değildir.
## 26. Diğer Studio (paralel, kritik yol değil)
- [ ] Project (WorkItem/plan), Workflow (DAG), Organization (hiyerarşi), Agent (rol/atama), Model (catalog/cost), Skill (version/permission), Memory (provenance), Finance (budget), Security (IAM/audit), QA/IV görünümü. Mevcut güncel ekranları koru.

# H. Ortam ve doğrulama
## 27. Çalışma ortamı — MI-01/MI-10/Codex
- [ ] PR52 25-row C50/R9 review-only lock, cryptography/native wheel/provenance/license/security; exact approved runtime/lock olmadan install/execute HOLD.
- [ ] Onaylı Python/Node ve npm lock, backend app.main:app/Next.js aynı loopback port sözleşmesi, izinli PostgreSQL ortamı; müşteri verisi/PROD/gerçek sağlayıcı izinsiz yok.
## 28. Doğrulama sınırı
- İlk kaynak birleştirmesinde yeni test ve rutin koşum yok; exact blob/byte/hash/manifest/arşiv/closure kontrolü, önceki geçerli kanıt yeniden kullanılır.
- Farklı kaynak sürümünde işlev/sözleşme incelemesi; API, IAM, DB/T1, Runtime, Model/Skill/Memory, UI davranışı değişirse etkilenen akışın zorunlu doğrulaması ayrı izinli kapsamda; doğrulanamayan kalem HOLD. Doğrulamaları sona yığma; bağımsız işi sürdür. Yeni test/koşum izni bu planla verilmez. PASS/FAIL/NOT_RUN/BLOCKED/HOLD ve tarihsel/sentetik/gerçek/bağımsız ayrımı korunur.
## 29. Mevcut MVP-03 E01–E10
| ID | Kapsam | Başlangıç |
|---|---|---|
| E01 | CEO arayüz | NOT_RUN |
| E02 | Gerçek HUMAN permission | HOLD |
| E03 | Plan ve request binding | NOT_RUN |
| E04 | Protected durable COMMIT | HOLD |
| E05 | Authorized same-ID readback | HOLD |
| E06 | Restart persistence | HOLD |
| E07 | Durable idempotency | HOLD |
| E08 | Negative IAM/RLS | HOLD |
| E09 | Rollback/revoke/UNKNOWN | HOLD |
| E10 | No unauthorized execution on request | NOT_RUN |
D0 kanıtları kendi kapsamındadır. E01–E10 mevcut oracle'dır, yeni genel MVP paydası değildir.
## 30. W8
- [ ] Kaynak sahibi → zorunlu güvenlik/bağımlılık/lisans ön inceleme → tam resmi C07 → gerçek Chromium C08 → bağımsız C05 → kabul. Tam arşiv ve rollback. Bağımsız kaynak çalışmasını durdurma.

# I. Teslimat ve bağımlılık sırası
## 31. Plan içi 12 teslimat noktası
| Etiket | Çıkış | Bağımlılık |
|---|---|---|
| T01 | RESEARCH kaynak uzlaştırması/tek manifest | mevcut aday |
| T02 | Gerçek HUMAN IAM/ORG | yetkili issuer/project |
| T03 | WorkType yayın/A1 fiziksel eşleme | owner/QA/IV/H01 |
| T04 | Korumalı T1/PostgreSQL/readback | T02/T03, approved runtime/protection |
| T05 | CEO create + same-ID readback | T02–T04 |
| T06 | Orchestrator/DAG/Scheduler | T05 gerçek akış; kaynak paralel |
| T07 | Agent Runtime/admission | T06 + gerçek grant/lease/budget |
| T08 | Model/Skill/Memory | T07 yetkisi; kaynak paralel |
| T09 | Kalıcı sonuç/QA | T08 |
| T10 | Independent IV/H01 | bağımsız, T09 çıktı kanıtı |
| T11 | CEO/Office/Studio | gerçek projection; kaynak paralel |
| T12 | Bütünleşik kabul | ilgili tüm normatif kriterler/W8 |
Kritik yol: RESEARCH kaynakları → HUMAN IAM/ORG + WorkType/Project/DB + Security/C50 (paralel) → T1 ve CEO readback → Orchestrator/Scheduler/Runtime → Model/Skill/Memory → kalıcı sonuç/QA/IV/H01 ve Office. QA/IV kaynak incelemesi başlangıçta, sonuç kabulü gerçek çıktıya bağlı.

# J. Görev paylaşımı
## 32. ChatGPT
- Merkezi kaynak uzlaştırma, teknik owner review, mevcut ürün bağlantıları, API/DB/event uyum, tek path yazıcı, isolated commit/manifest/readback, katalog/devir/rollback ve sonraki uygulanabilir görev; bağımsız MI10 değil.
## 33. Codex
- Exact checkout, approved lock/runtime, tahsisli kaynak, yerel hata/build/izinli zorunlu doğrulama, backend/frontend/PG, W8/Chromium kanıtları, SHA-bound devir. ChatGPT ile aynı path'e eşzamanlı yazma yok. Araçtır, ürün ajanı değildir.
## 34. H01
- Öncelik, gerçekten yeni normatif karar, bağımsız yetkili reviewer/custody, exact RESEARCH sürüm yayın kararı, gerçek execution/provider/spend, nihai kabul, gerektiğinde ayrı transfer/main/PROD kararı. Verilmiş kararları tekrar isteme.

# K. Ölçüm
## 35. Başlangıç resmî kabul
UI21/40 (%52,5), Core12/16 (%75), MVP0/11, W8 3/8 (%37,5), IV0/7; GOAL INTEGRATION ve ağırlıklı genel gelişim HESAPLANAMADI. Kaynak sayısı kabul değildir.
## 36. Mevcut 11 MVP kriteri
1. Şirket oluşturma.
2. Departman ve ajan tanımı.
3. Kullanıcı görev talebi.
4. Otomatik görev planı.
5. DAG bağımlılık sırasına uygun yürütme.
6. İzinli AI modeli kullanımı.
7. İzinli araç kullanımı.
8. Kalıcı hafıza/sonuç.
9. Ofisin gerçek durum projection'ı.
10. QA ve bağımsız IV.
11. İnsan onayları ve bütçe sınırları.
İlk WorkItem kaydı tüm kriterleri kapatmaz; her biri ayrı kanıt.
## 37. Geliştirme metrikleri
Tasarım15 + kaynak35 + fonksiyonel test20 + entegrasyon20 + nihai kabul10; onaylı stage kriter/payda ve kanıt olmadan HESAPLANAMADI. Ürün kabulü ayrı; 24 alan ordinal 0/25/50/75/100 ayrı. Mükerrer kanıt sayma. Plan checklist ilerlemesi normatif oran değil.

# L. MVP sonrası
## 38. Genişleme
- [ ] Diğer iki WorkType, otomatik proje/departman/takım, delegasyon, multi-agent collaboration, eşzamanlı projeler, performans/öğrenme, optimizasyon, Premium UI/çok katlı ofis, finans/risk, SaaS şablon/kota/abonelik/faturalandırma, ölçek, backup/restore, izleme ve denetimli otonom şirket. Zorunlu tenant/security/budget minimumu ilk MVP'de korunur. Bunlar ilk RESEARCH kaydını bekletmez.

# M. Operasyonel kuyruk
## 39. Hemen uygulanacak sıra ve engeller
1. Güncel tek adayda RESEARCH fonksiyon düzeyinde kaynak uzlaştırması.
2. PR10/46/52 exact teknik ve bağımsız reviewer kararları (başlangıçta üçünde de submitted review 0; canlı tekrar doğrula).
3. A1 Project/WorkItem fiziksel ve authority sözleşmesi.
4. RESEARCH exact version QA/IV yayın incelemesi ve H01 kararı.
5. Gerçek HUMAN IAM ve Project permission.
6. Mevcut T1 typed HUMAN WorkItem işlemi.
7. Protected PostgreSQL ve authorized readback.
8. CEO komut bağlantısı.
9. Aynı WorkItem'a Orchestrator/Scheduler.
10. Runtime/Model/Skill/Memory.
11. Kalıcı sonuç/QA/IV/Office.
12. Zorunlu doğrulama ve yetkili kabul.
P0 ortak engeller: bağımsız MI10 yetkili reviewer, PR10 physical/COMMIT, PR46 HUMAN issuer, PR52 C50/R9, final schema, actual publication/binding, PG/custody. P1 execution yetkileri/W8. Diğer Studio/SaaS ve eski kaynaklar paralel. HOLD yalnız bağımlı kapsam; sıradaki bağımsız işe geç.
## 40. Çalışma disiplini ve nihai hedef
- Tek ürün/tek mevcut aday, yeni prototip/mükerrer motor yok. Fonksiyon kazanımı > commit/test/rapor adedi. Önce RESEARCH kaynakları, sonra CEO gerçek kayıt/readback, ardından aynı kayda yürütme. Zorunlu doğrulama atlanmaz; tekrar test yok, HOLD ayrıştırılır.
- Her tur kaynak/commit/manifest/kanıt, önceki/yeni kriter-payda-delta, mimari/katalog, owner/blocker, rollback, sonraki somut görev ve yeni CEO kararı gereği raporlanır.
- Ortak product-dev ve main doğrudan yazılmaz; mevcut kullanıcının tek izole aday kısıtı korunur. Yeni CI, PROD, gerçek IAM/grant, protected COMMIT/migration, dış etki, harcama, müşteri verisi, bağımsız kabul izinleri değişmez. H01 karar ve mevcut policy sınırları geçerlidir.
- Nihai hedef: görev oluşturma, otomatik planlama, görev dağıtımı, yetkili araştırma, kalıcı sonuç, bağımsız denetim ve CEO/ofis üzerinden yönetim.
- Kaydetme turu yalnız yönetişim dokümanı; kod/test/ürün manifesti/kabul değişikliği yok. Tam Design Master ek uzlaştırması ve tam arşiv doğrulaması açık, bu plan normatif şema onayı değildir.

## Kaynaklar ve geri dönüş
- [WORKING_STANDARD.md](WORKING_STANDARD.md), [merkezi görev kaydı](../../progress/MASTER_INTEGRATION_CURRENT.json), [raporlama standardı](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/b6983047430cecde80a02c6384a22fe80301ad93/progress/REPORTING_STANDARD_20261118.md).
- [Aday kaynak uzlaştırması](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/4245b569797a2742579e4619a0e546d25281c0ca/catalog/revisions/H01_UNIFIED_SOURCE_RECONCILIATION_20261128.json).
- [A1 WorkItem eşleme incelemesi](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/4245b569797a2742579e4619a0e546d25281c0ca/docs/architecture/H01_MVP03_PROTECTED_WORKITEM_MAPPING_REVIEW_20261127.md).
- Rollback: bu yönetişim commit'inin normal revert'i; önceki kararlar ve ürün dalları korunur.
