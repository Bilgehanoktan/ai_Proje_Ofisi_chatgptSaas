# MI04 / G2 50 + G9 7 — Gerçek özgün kaynak testi kapanışı
20 Kasım 2026. [GitHub CI 44697437051](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44697437051) **2/2 jobs SUCCESS**.

## Yapılanlar ve neden
Başka sohbetlerin işi mükerrer yürütülmedi: PR #15 üzerinden **553 dosyalık product-dev aktarımı zaten MERGED**; tam W8 MI-01/Unified tarafından yürütülüyor. MI-04 kapsamında kaynak sahibi dallarında **G2 50 özgün test** ve **G9/G7 7 özgün test** `NOT_RUN` idi. Özgün test ve yürütücüleri yeniden yazmadan, kendi immutable Git commit'leri üzerinden iki bağımsız CI job çalıştırıldı.

G2 owner `9ca667e816dac269084ef8f62051da5fe458eb12`, orijinal `run_regression.py`: 395 manifest, 240 backend dosyası, 3 DDL, 7 pin doğrulandı; `test_intent_authority_t1_0212`, `test_authority_fullchain_0214`, `test_iam_session_d5g1`, `test_iam_authority_d5g2` **50/50 PASS**, 0 fail/skip.
G9 owner `68ec99c673cceadffecf1d192371c10c328caa74`, özgün `run_exact_checkout.py` ve `candidates/D5-G7/test_checkout.py`: 403 manifest, 248 backend, 56 pin doğrulandı; yedi `ActualReadbackTests` **7/7 PASS**, 0 fail/skip. Python 3.13.5, cryptography 46.0.4, cffi 2.0.0, pycparser 3.0.

## Teknik envanter / kaynak çakışması
**Kanonik ürün farklıdır**: `integration/product-dev@9a3571d6a06537ba718bafc45398c309bf3dc9b1` 553 dosyadır. Bu tur test edilen G2 `app/core/transaction/intent_authority.py` blob `b28788f46a39c282d79d29c4abd817ed5fc9de99`; kanonik aynı yol blob `fa47acd32adb309896f762ec50e47bf26641adbb`. Ayrıca G2 owner `app/core/iam_session.py` blob `f3c37428acd475e09c228bce47d534d6584cd944` kanonik kaynakta **yok**. G9/G7 checkout tarihi kaynak dalında kök `durable_ops.py` bulunmuyor; kanonik ORG kök `durable_ops.py` blob `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` ayrı sözleşmedir. Bu nedenle **G2/G9 owner 57 PASS, kanonik 553 üzerinde G2/G9 57 PASS iddiası değildir**.

Özgün modüller ve API: `D0SessionResolver`, `SessionRecord`, `SessionClaimCheck`, `D0IntentAuthority`, `RootPin`, `ActualReadbackTests`, `read_current_org_reference`, `inspect_core_org_session_reference`. Yeni HTTP API, DB migration, dış etkili event, runtime grant ve ürün dependency eklentisi **0**. Sadece geçici CI'nin ihtiyaç duyduğu sürümlü Ed25519 bağımlılıkları kullanıldı.

## Güvenlik ve bakım
`test_full_restore_residual_reproduced_not_security_pass` G2'nin 50 testine dahildir; daha önceki [0214 ayrı 10/10 CI](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44695937454) aynı test yöntemini içeren önceki gerçek kanıttır, **iki defa ürün kabulüne yazılmaz**. Eski ürün DB + intent journal + yerel authority birlikte geri alınırsa replay halen açık. A mimarisinde gerçek bağımsız custody root/consumed claims ve sink fence henüz uygulanmadı; strict PG, 8 bağımsız negatif senaryo ve IV **HOLD**.

Arıza kontrolü: test source SHA, manifest blob ve runner pin mismatch => HOLD. Başka ürün sürümüne bu 57 PASS taşınamaz. D0 SQL gerçek DB'ye uygulanmaz, claim geçmişi sıfırlanmaz, otomatik fail-open retry yapılmaz. CI için açılan [PR #17](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/17) **birleştirilmeden kapatıldı**, hiçbir ortak ürün veya owner kaynak dosyası değiştirilmedi. Geri dönüş belge commit'inin normal revert'i; test kanıtlarını silme.

## İlerleme ve sıradaki ürün işi
Özgün owner G2: **0/50 NOT_RUN → 50/50 gerçek test**, özgün G9/G7: **0/7 NOT_RUN → 7/7 gerçek test**. **57 test yürütme**, 57 yeni test yöntemi veya 57 ürün kabul kriteri değildir. Mevcut IAM/ORG kriter ağırlığıyla %42,5 → %42,5 (0 pp), global geliştirme **HESAPLANAMADI**, Core 12/16, MVP 0/11, IV 0/7, A 0/8; kanonik kabul farkı 0.

Sahiplikte sıradaki kritik iş: **G2/IAM owner** ile `iam_session.py` eksik dosya ve `intent_authority.py` varyantı için karar ve kaynak-API sözleşmesi; **ORG/G9 owner** gerçek kanonik `durable_ops.py` kapsamı ve G7 readback bağlanması; **MI-01/Unified** 553 W8 full build; **Security/MI02** bağımsız root, PG COMMIT/restore ve negatif kabul. Bunların hiçbirine onaysız source overwrite yapılmadı.

Makine kanıtı `EVIDENCE.json`, teknik katalog `TECHNICAL_CATALOG.json`; süreklilik merkezi `progress/MASTER_INTEGRATION_CURRENT.json`.
