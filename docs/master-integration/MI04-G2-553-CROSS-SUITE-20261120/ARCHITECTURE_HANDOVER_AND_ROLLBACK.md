# AI Company OS — MI04/G2 553 kaynak uyumluluğu: teknik kapanış (20.11.2026)

## Gerçek kaynak işi, neden ve nerede
Öncelik çakışması canlı GitHub üzerinden kontrol edildi. MI01/Unified 553 tam W8 zincirini, MI02 bağımsız PG/IV kontrolünü, MI07/08 Memory/344 ve Linux symlink sınamasını yürütüyor; bu kaynakların hiçbirine müdahale edilmedi. Önceki 553 kaynak `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` değişmeden kaldı. G2'nin mevcut IAM oturum modülü o kaynak ağacında eksikti ve mevcut D0 `intent_authority.py` dosyası G2 sahibiyle farklıydı.

İzole `review/mi04-g2-on-553-isolated-compat-20261120` dalına kanonik 553 ürün tabanı üzerinden yalnız **üç özgün G2/G1 ek dosya** ve **bir özgün G2 alternatif D0 authority dosya seçeneği** taşındı; yeni fonksiyon geliştirilmedi. Kodlar GitHub owner blob'larından aynen alınmıştır:
- `app/core/iam_session.py` — `f3c37428acd475e09c228bce47d534d6584cd944`.
- `tests/test_iam_session_d5g1.py` — `6be21cfdcaf7408d7d17b5848966bb7f6772581e`.
- `tests/test_iam_authority_d5g2.py` — `16bfc7013ae77cdcf437227b9fb6ac8a9a69d08c`.
- `app/core/transaction/intent_authority.py` — kanonik `fa47acd32adb309896f762ec50e47bf26641adbb` yerine **yalnız izole adayda** özgün G2 `b28788f46a39c282d79d29c4abd817ed5fc9de99`.

Aday `aac205efec6ffdc8a682dc4c9c9059af16842956`; ürün dosyaları 553→556 ve manifest 552→555 (izole aday için). Önceki 551 çakışmasız manifest girdi pinleri aynen korundu. **Kanonik 553 kaynak değişmedi.** Kod konumu/sınıf/fonksiyon, yeni olmayan public API, test/SQLite DB ve bağımlılık kapsamı ayrıca `TECHNICAL_CATALOG.json` dosyasındadır.

## Gerçek test ve kanıt sınırı
[PR #19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19) üzerinde exact immutable adaydan çalışan [CI #44699083111](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44699083111) **SUCCESS** (job `136162832360`); Python 3.13.5 / SQLite 3.45.1 / cryptography 46.0.4 / cffi 2.0.0 / pycparser 3.0. Git owner blob 8/8, manifest SHA256+bayt 555/555 PASS. Aynı Python süreç ve aynı ürün ağacında 6 özgün test modülünden:
- G2 `test_intent_authority_t1_0212` 7, `test_authority_fullchain_0214` 10, `test_iam_session_d5g1` 14, `test_iam_authority_d5g2` 19 ⇒ **50/50 PASS**.
- ORG özgün `test_org_runtime_packaging_mi03` 4, `test_org_sql_runtime_mi03` 11 ⇒ **15/15 PASS**.
- **Birleşik 65/65 PASS**, failures=0, errors=0, skipped=0.

Bu 65 test **mevcut testlerdir, bu turda yeni yazılmamıştır**. Daha önce G2 50 ve ORG 15 kendi pinlerinde ayrı ayrı koşulduğu için bunu 65 yeni ürün kabul/özgün yöntem olarak çift sayma; buradaki *yeni kanıt, aynı kaynak ağacı ve test sürecinde iki bileşenin birlikte çalışmasıdır*.

## Mimari güvenlik/kabul (değişmedi)
G2 IAM `D0SessionResolver` yerel sentetik oturum ve `D0IntentAuthority` fixture değildir; gerçek issuer/custody/root/consumed claim/effect sink oluşturmaz. Özgün `test_full_restore_residual_reproduced_not_security_pass` yine geçti: **eski ürün DB + eski journal + eski D0 authority birlikte restore edilirse replay açığı bilerek yeniden üretildi**. Bu PASS, gerçek güvenlik veya D-03/D-04 A çözümünün kabulü değildir. PostgreSQL strict COMMIT/restore, 8 negatif A senaryosu, independent IV, üretim, harcama, provider ve tenant grant **HOLD/DENY**.

G2/Authority **teknik dosya sahibi** mevcut aynı-yol varyant seçimini, G9/ORG sahibi kanonik iş sözleşmesini ve MI01/Unified tam W8 orijinal zincirini ayrıca onaylamadan PR #19 ürün geliştirme dalına **birleştirilmemelidir**. Testin başarısı bu kararların yerine geçmez.

## Arıza teşhisi, bakım, sürüm ve geri dönüş
Kritik giriş koşulları: owner Git blob pin 8/8; manifest 555/555 SHA-256+byte; test collection exactly 65; no skip/expected failure. Herhangi bir farklı SHA, role, root, eski authority sözleşmesi veya test ERROR durumunda **HOLD**, sadece ham log ve revizyon kaydıyla sürdür. G2 oturum simülasyonu PROD IAM yetkisi değildir; disposable SQLite şemalarını gerçek tenant DB'ye uygulama. Branch rollback: izole review PR #19'u kapat, başlığı sakla; source commit'i normal revert; `integration/product-dev`, main ve owner dallarını force-push etme, claim geçmişini sıfırlama. Kullanıcı genel izin verdi fakat bağımsız güvenlik kabulü test kanıtı olmadan yaratılmaz.

## Merkezi ilerleme ve devir
Önceki: kanonik G2+ORG aynı-source birleşik 65 testi **NOT_RUN**; güncel **65/65 PASS on isolated exact candidate**. Geliştirme yüzdesi IAM/ORG kaynak kayıtlarında **%42,5 → %42,5**; yeni genel 15/35/20/20/10 paydaları ratifiye değil, **HESAPLANAMADI**. Core 12/16, UI 21/40, MVP 0/11, IV 0/7, A bağımsız 0/8; ürün kabul artışı 0.

**Sıradaki iş:** G2/Authority ve G9/ORG dosya/sürüm sahipleri PR #19'da imza/kabul, ardından MI01 sahibi aynı adayın W8 kilitli bağımlılıkları ile tam fresh prepare/install/test/native browser; MI02/Security gerçek protected PostgreSQL ve bağımsız source custody-root/sink tasarımı ve negatif kabul. Yeni prototip oluşturma veya başka hattın W8/Memory işini tekrarlama. Her kanıt ayrı sürümlü bırakıldı.

Referanslar: `EVIDENCE.json`, `TECHNICAL_CATALOG.json`, `progress/MI04_G2_553_OWNER_COMPAT_20261120.json`, `progress/MASTER_INTEGRATION_CURRENT.json`.
