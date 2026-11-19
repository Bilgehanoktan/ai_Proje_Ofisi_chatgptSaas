# AI Company OS — MI03-GATE03 Core–OperationsStore kaynak sözleşmesi okuması
Tarih: 2026-11-19. Tür: yalnız güncel GitHub kaynak ağacı ve sözleşme incelemesi; **ürün/entegrasyon testi değildir**.

## Esas ve sahiplik
- Yönetim: `planning/master-integration-governance/docs/master-integration/WORKING_STANDARD.md` ve `progress/MASTER_INTEGRATION_CURRENT.json`.
- Ortak ürün dalı: `integration/product-dev` @ `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` (505 dosya, tam build BLOCKED).
- İncelenen izole aday: `integration/mi03-gate03-org-runtime-closure-01` @ `d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` (553 product dosyası, 552 manifest girdisi).
- Aynı dala ait `MI03-GATE03-SQL-R1` 11/11 sentetik SQLite SQL testini ve eski adayın 71/71 seçili koşumunu koru; tekrar veya yeni testmiş gibi toplama.
- Paralel `MI03-GATE02-ASSIGNMENT-RECOVERY-79`: 79/79 (8 yeni, 71 tekrar) ve eski DB+eski pin ortak restore sınırlamasının tekrar üretildiği bağımsız kayıt. Bu sohbet o işi tekrar üstlenmez.

## Bu turda gerçekleşen kontroller
GitHub'ın recursive tree çıktısı ve adayın özgün kaynak pin kataloğu karşılaştırıldı. 12/12 `product/ai-company-os-backend/` kaynak dosyası için **Git blob SHA ve tree bayt boyutu** eşleşti. Bu kontrol yerel SHA-256, çalışma zamanı importu veya çalıştırılmış Core/Store fonksiyon testi DEĞİLDİR. Adayda tek ürün manifesti bulundu; 553 ürün dosyası sayıldı. İki mevcut test dosyasının blob'ları saptandı (4 paketleme smoke, 11 SQL testi).

## Gerçek API ve kontrol sınırı
- `app/core/development_review/research_slice.py:inspect_research_slice(cursor,plan,expected_revision,project_id,pins,members,pool,events,anchor,*,evidence=None)`: tarihsel, tutarlı Core T1 okuma kesiti; dispatch/release HOLD.
- `assignment_lifecycle.py:verify_core_reference(pin,cursor,args,intent,member,member_scope,principal)`: mevcut `derive_request` ve gerçek Core okuyucusu ile proje, plan revizyonu, görev, Member ve TaskHistory eşitliklerini denetler; bağımsız owner/role issuance KANITLAMAZ.
- `durable_ops.py:OperationsStore.record_assignment_review(...)`: mevcut ORG `BEGIN IMMEDIATE` transaction içinde `_current/_team/_history` denetimini, Core tarihsel okumasını ve `append_decision` yazımını sırayla çağırır. Core cursor **ayrı snapshot'tır**; iki depolu atomiklik veya güncel yetki çıkarılamaz.
- `assignment_lifecycle.py:source_match/read_chain/append_decision/inspect_assignment`: ORG head, seat, role, proposal, immutable revision 1 ACCEPTED_D0/revision 2 REVOKED_D0, CAS/hash ve red kontrolleri; her sonuçta `authoritative/dispatch_allowed/commit_allowed/retry_allowed=False`.
- `durable_ops.py` seçimi: G9 özgün `43ed448c...` ile atama ekli `619fe224...` farklı. İlave 41 satır eski G9 testlerinin kanıtını yeni sürüme otomatik aktaramaz. ORG/Core/G9 sahibi onayı HOLD.

## P0 açık test kapısı (kanıt henüz yok)
1. Orijinal `tests/test_canonical_research_0224.py:ResearchFixture` ile tek tutarlı salt okunur Core cursor oluştur; `test_org_core_checkout.py` eski ORG pozisyon/roster örneğini, current `initialize_assignment_ops` ve `OperationsStore` gerçek yazıcısını kullanarak aynı pinned kaynağı koştur.
2. Pozitif: doğru Core Member+plan/task/version, ORG head+seat+role, doğru `AssignmentPin`, sentetik `ApprovalObservation` ile SQLite COMMIT ve kapat/aç geri okuma; `ACCEPTED_D0`, no grant.
3. Negatif: yanlış görev/rol, farklı tenant/company/environment, eski plan/ORG revizyonu, değişmiş Core Member, eski expected SHA, tekrar atama, rol/üyelik kayması, geçersiz onay referansı; hepsinde `HOLD`, `op_assignment_review` ilave satır 0.
4. `REVOKED_D0` revizyon 2, duplicate/re-accept reddi, rollback, bozulan zincir ve eski yedek/ayrı tutulan son pin: hiçbir akış yürütme yetkisi üretmez. Restore güvenliği için bağımsız witness ayrıca gerekli.
5. Orijinal G9 7/7 test, G2 50, 0214 Memory–T1 10, PostgreSQL strict COMMIT ve ortak W8 build farklı kapılardır; bu kayıtta NOT_RUN.

## Engeller ve bakım
Tam pinned kaynak checkout/bağımlılık ve Core+Store birlikte koşulan ortam bu turda hazır değil; mevcut dar MI10 CI izni GATE03'e genişletilmiş sayılmaz. Kaynak çekilemez veya pin uyuşmazsa fail-closed ve `NOT_RUN`. Testler yalnız geçici sentetik SQLite; SQL'yi canlı DB'ye migration olarak uygulama. Candidate revert normal commit ile; `integration/product-dev`, `main`, gerçek grant ve PROD değişmesin.

## İlerleme / devir
MI03 IAM/ORG geliştirme önceki **%42,50**, güncel **%42,50**, delta **0,00 yüzde puan**. Core kanonik ürün kabulü **12/16 (%75)**; bütünleşik MVP **0/11 (%0)**, kabul değişimi **0**. Bu tur: ürün değişikliği 0, yeni işlevsel test 0, 12/12 yeni Git tree pin okuma; durum `SOURCE_READBACK_PASS_FUNCTIONAL_GATE03_HOLD`. Sonraki iş: sahip onayı ve orijinal Core+OperationsStore birlikte koşum, G9 sürüm uzlaştırması; kapı kapanmadan ortak ürün yükseltmesi yok.

## 2026-11-20 — PR #6 tam GitHub adayında kaynak kapanışı (test koşumu değildir)

- Açık taslak PR #6: `review/mi03-gate02-core-positive-20261119`, immutable incelenen head `0478d8003b0cbcc4b99f20f865c8173bbabf813e`.
- Tüm recursive Git tree üzerinden 19 Python Core/ORG/test yolu, yedi kanonik SQL fixture yolu (`database/` kökünde) ve bir `fixtures/core.preview.json` yolu: **27/27 mevcut**, eksik yol 0. PR test blob `23c2f019a27bc9e16d8de3f2af72c239eefac035`; mevcut Core `research_slice.py` blob `720044a4e4954820b8d298f73b6b75f2189b4f94`.
- Önceki `ModuleNotFoundError: test_canonical_research_0224`, eksik seçilmiş yerel dosya katmanından kaynaklanmıştır; tam PR dalındaki ilgili dosya mevcut. Bu kaynak varlığı, Python importunun ve bütün transitif bağımlılıkların çalışacağını kanıtlamaz.
- PR #6 test adayı zaten **10 yöntem** içeriyor. Testin yeniden yazılmasına ihtiyaç yok; tam pinned checkout ile orijinal test koşulmalı. Bu tur **0/10 gerçek fonksiyonel test**, kod değişikliği 0, GATE-03 hâlâ HOLD.
- İnceleme sonucu GitHub PR #6 yorumunda kayıtlı; bu yorum ürün sahibinin onayı değildir. MI-10 PR #4 kısıtlı CI kapsamı genişletilmedi. Kullanıcının bilgisayarında test beklenmiyor; izinli izole ortam sağlandığında tam test yürütmesi ayrı kanıtlanmalı.
- Devir / bakım: Kaynak sürümlerini değiştirmeden tam checkout alın; `product/ai-company-os-backend` kökünden `python -B -m unittest discover -s tests -p test_core_operations_assignment_mi03.py -v`; öncesinde pinned modülleri ve Python bağımlılıklarını doğrula. Negatif ve pozitif test logu, exit kodu, Core ve ORG veritabanı kapsamı, bağımsız owner incelemesi ayrı kaydedilecek. Fail-closed / rollback eski `d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` adayına incelemeli revert; product-dev/main değiştirilmez.
