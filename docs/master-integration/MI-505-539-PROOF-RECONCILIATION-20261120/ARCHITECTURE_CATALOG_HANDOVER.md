# AI Company OS — Kanıt, teknik katalog, mimari ve devir kaydı
**Revizyon:** MI-505-539-PROOF-RECONCILIATION-20261120 · **Kaynak:** `integration/product-dev@8a3b05aa` → `integration/mi-common-source-review-01@bd57cc82` · **Durum:** yalnız inceleme. Mevcut yetkiler genişletilmedi.

## Kaynak farkı — kapatılan inceleme
GitHub farkı **172 path**, bunun **49**'u ürün altında, **123**'ü belge/yardımcı/test altında. Önceki kaynak manifesti **504**, yeni **538** girdidir: **490** aynı SHA-256+byte, **13** değiştirilmiş, **35** yeni, **1** çıkarılmış eski yol (`DraftInspector.tsx` → `WorkflowDraftInspector.tsx`). 49 ürün Git diff: **34 added, 14 modified (manifest dahil), 1 renamed**. Sahibine eşlenemeyen **0** değişiklik. Makine-okunur 49 yol ve önceki/yeni SHA-256/byte kataloğu: [SOURCE_DELTA_AND_PROOF.json](./SOURCE_DELTA_AND_PROOF.json).

**Sahiplik:** MI-01 **3** (UI rename/import/test); MI-03/04 **4** (`postgres_session.py`, `identity_binding.py`, `intent_identity.py`, preclaim test); MI-07/08 **26** (model gateway/memory runtime ve özgün testler); MI-05/06/09 **15** (ORG ve Skill read-only projection, registry test); ortak manifest **1**.

## Mevcut test kanıtlarını tekrar çalıştırmadan koruma
- **10/10 özgün Core–OperationsStore sentetik SQLite PASS**: frozen `3b59f54e...`, test SHA-256 `1ef392356f7f605cff573069d77da31d9188f874636d1179eb7a3751a32e636d`, [CI run 44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705). Bu kanıt ayrı owner-source D0 alt kapısıdır; ortak ürün security/PG kabulü değildir.
- **1.953/1.953 full Git checkout** ve **538/538 original W8 source SHA256**: [CI run 44617509366](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44617509366); ürün ağacı sabit (`61bb06e` → `bd57cc8` arasında **0** `product/` değişikliği). Belgeler/yardımcı scriptler eşitlik kapsamı dışındadır.
- Aynı CI kapsamındaki **42/42 seçili özgün T1 SQLite**, Next.js build/typecheck ve SSE-compatible browser PASS eski kanıttır. Yeni test sayılmadı; full native U3 veya korumalı işlem sayılmaz.

## Açık özgün sınamalar / test seçimi
`original W8 prepare/install/test/smoke` **NOT_RUN**, native U3 **HOLD**, Model/Memory344 **HOLD (cryptography metadata)**, Historical Core29 **NOT_RUN**, G2 50, G9 7, T1 0214 10 **NOT_RUN**. GATE02 bağımsız issuer/registry/member/role/assignment provenance ve `durable_ops.py` sürüm çakışması; GATE04 old-DB+old-pin restore replay riski, immutable independent latest witness ve strict PostgreSQL COMMIT **HOLD**. Yalnız eksik özgün testleri, sahip onaylı exact pinned ortamda çalıştır; test motoru tekrarı üretme.

## Mimari ve teknik yüzey
- UI: WorkflowDraft rename ve mevcut import/test ilişkisi.
- IAM/Core: identity/intent bağlama, `postgres_session` transport; gerçek grant veya yeni güvenlik motoru tanımlanmadı.
- Model/Memory: `joint_context`, `memory_witness`, `snapshot_store`, `model_gateway` ve testleri; kaynak owner onayı ve 344 özgün regresyon gerekli.
- ORG/Skill: read-only `GET /api/demo/organization`, `organizationOwnerBinding`, `organizationProxy`, `organizationProjection`, projection registry, ExternalSkillCatalog. Backend owner yoksa 503 HOLD; skill örnekleri aktive değil.
- Bu 49-path ürün farkında DB migration veya ürün bağımlılık kilidi değişikliği görünmüyor; **bu, DB/bağımlılık kabulünün yapıldığı anlamına gelmez.** Veritabanı atomikliği, protected API, runtime gerçek yetkiler, dış event ve provider etkisi doğrulanmadı.

## Owner karar kuyruğu ve kesin kapanış sırası
1. MI-01/Unified mevcut adayı ve lock/fingerprint gözden geçirir; onaylı exact W8 ve original U3 eksik testleri.
2. MI-03/04, ORG ve D4 sahibi `durable_ops` sürümünü ve gerçek assignment/role provenance sözleşmesini karara bağlar; GATE02/01.
3. MI-07/08 özgün 344'ü, bağımlılık preflight ve kaynak referansıyla tamamlar; ayrı Core29.
4. MI-05/06/09 yalnız read-only ORG/Skill sözleşmesini, ORG31 ve Skill41 özgün kapsamını doğrular.
5. MI-04/IV protected PG COMMIT/revoke/restore ve bağımsız anti-replay witness güvenlik kapısını kapatır.
6. Unified sahibi kontrollü ürün aktarımını ancak review + yetki + regresyon + rollback kanıtıyla önerir; eski 11 MVP kriterini değiştirmez.

## İlerleme ve sürüm kontrol
Yeni ürün kodu **0**, bu incelemede yeni fonksiyonel test **0**, merkezi ürün commit etkisi **0**, kabul delta **0 pp**. Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**. Genel ağırlıklı gelişim yüzdesi **HESAPLANAMADI** (grup kriter paydası 0/10 onay). Tarihsel `PR6 0/10 NOT_RUN` snapshot'ı silinmez; güncel 10/10 kanıtı ayrıca tanımlanır.

**Bakım/arıza:** Drift için 49 SHA kayıtları ve `git compare`; ortam hatasında Python/SQLite/cryptography metadata ve fresh wheelhouse; ürün hatasında özgün W8 logları; güvenlik olayında owner-provenance/latest witness + no-write. Tek test tekrarının yüzde/acceptance kazanımı olmadığını koru.

**Rollback/devir:** Taslak PR'ı kapat veya izole inceleme dalında normal revert yap. `product-dev`, `main`, CI iş akışları, owner dalları, PROD/secret/gerçek DB/harcama değişmedi. Merge yok, force-push yok. Bu kayıt sahip onayı veya release izni değildir.

## 2026-11-20 — PR #7 inceleme düzeltmesi (ürün aktarımı yok)

- Sabit `8a3b05aadd32` → `bd57cc8235a1` GitHub karşılaştırması: **172 yol (49 product + 123 diğer)**. Önceki 176/127 sayısı, adayın sonrasındaki `MI-COMMON-08-WIN-ISOLATED-ENV` kapsamından dört dosyanın yanlışlıkla bu sürüme dahil edilmesiydi. Bu dört dosya şimdi `SOURCE_DELTA_AND_PROOF.json.diff.later_revision_exclusions` altında ayrı gösteriliyor. **49 ürün değişikliği, 490 aynı + 13 değişen + 35 yeni + 1 çıkarılan manifest yolu ve sahiplik sınıflandırması değişmedi.**
- Önceden eksik olan `product/SOURCE_MANIFEST.json` hash/byte kayıtları özgün sabit commitlerden hesaplandı: eski **90448 byte / SHA-256 `6b9b02e73b133e901fcee31713c31125cbd825020068e4f5e531ea5323b81792`**; yeni **96898 byte / SHA-256 `2ce5f642393184b04d7df1ea411e1fa13f627ba971fbc3010c2bce2b77d9c01a`**. Git blob referansları ayrıca makine-okunur katalogda.
- PR #7'nin eski inceleme tabanı, güncel governance dalından ayrışmıştı. PR #7 inceleme dalında dört dosyalık düzeltme `7776bf0af7f2818ceab761c9a07d2b4797be0a6e` commit'iyle doğrulandı; ancak başka merkezi entegrasyon turu bu PR'ı **birleştirmeden, yerine geçen governance kaydı nedeniyle kapattı**. PR #7'nin ilerleme JSON'ları kanonik yönetime taşınmıyor; merkezi `MASTER_INTEGRATION_CURRENT.json` ve `MASTER_INTEGRATION_PARTIAL_PROGRESS.json` kaynakları ve sonraki D-03/D-04 **A** tercihi, owner provenance HOLD, CI kanıtları, PR9/PR11 ve Model/Memory kayıtları aynen korunuyor. Bu ayrı düzeltme yalnız kaynak farkı kataloğunu ve devir belgesini incelemeye sunuyor; **yeni bir sahip veya ürün kabulü oluşturmuyor**.
- Bu turda ürün kaynak dosyası değişimi **0**, yeni ürün fonksiyonel testi **0**, bağımsız IV güvenlik matrisinde **0/8**, MVP kabulü **0/11**, ağırlıklı genel geliştirme oranı **HESAPLANAMADI**. Bu çalışma yalnız GitHub statik kaynak farkı ve belgelerin bütünlük denetimidir; yeni Core/T1/PG/W8/Model regresyonu çalıştırılmadı.
- **Geri dönüş:** PR #7'yi kapatmak veya yalnız inceleme dalındaki bu uzlaştırma commit'ini normal `git revert` ile geri almak. `integration/product-dev`, `main`, CI iş akışları, güvenlik ve yürütme izinleri aynı kalır.
