# GATE-02 A mimari entegrasyon devir / güvenlik runbook'u
**Tarih 2026-11-20; A yönü seçildi; ürün kapıları HOLD.** [ADR](../../../decisions/ADR/ADR_D03_D04_OPTION_A_20261120.md).

## Gerçek durum ve kaynak referansı
- Kanonik `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`; ortak aday `integration/mi-common-source-review-01@4035d1a884362dae56a60d91358ea6e8e7dc0cdd`. D03/D04 özgün tasarım Git blob `85f61a0cbb4d3a3336a9bc9d3de8b00b995f0f24`.
- ORG/CORE özgün `PR #6` 10/10 D0 SQLite fiilen PASS, [run 44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705), ayrıca sonraki tekrarlarda aynı yöntemler PASS. Gerçek owner-issued role provenance ve product-dev source promotion YOK.
- GATE02 D0 79/79 seçili kanıt, **eski DB+eski pin birlikte restore edilince tekrar kabul kusuru yeniden üretilmiş**. Bu başarısız güvenlik senaryosu olumlu bir kontrol değildir.
- Özgün 0214 Memory–T1 10, G2 50, G9 7, strict PostgreSQL COMMIT, harici root/sink ve bağımsız IV hâlâ NOT_RUN/HOLD.

## Sahiplik ve iş sırası; çakışma önleme
1. **MI03/GATE02 ORG+IAM sahibi:** var olan `AssignmentPin`, `Request`, registry/seat/member/role gerçek owner prov. ile sürüm, principal, intent ve issuer bağlarının tamamını tarifler. `durable_ops.py` sürüm çakışması (G9 ve G8) için tek yazıcı kararı ister. PR6 kaynakları tekrar geliştirilmez.
2. **Security/IndependentAuthority sahibi:** ayrı restore/idari alan, konsensüs/quorum, log/checkpoint continuity ve bağımsız operatör/kök anahtar denetimi; provider ve KMS henüz seçilmez. `A-I01..` fail-closed anlaşmaları incelemede.
3. **MI04/T1 + MI02/DB sahibi:** bağımsız `consumeClaimOnce` ile orijinal T1 protected COMMIT süreci ve UNKNOWN karantinasının birleştirilmiş *tasarımını* gözden geçirir; PG owner ve bağımsız sink olmadan gerçek kullanım yok.
4. **EffectSink/ToolGateway sahibi:** doğrudan provider/effect bypass'ı engelleyecek kendi atomic fence/idempotency kabul sınırını ve ayrı kimlik/credential alanını tanımlar; ürün iddiası tek başına yetmez.
5. **Bağımsız IV/QA sahibi:** özgün 8 case + restore/partition/key rotation/effect loss senaryolarını ürünün güven kökünden bağımsız test eder; fixture PASS kabul edilmez.
6. **Merkezi entegrasyon koordinatörü:** kaynak pin/diff/catalog/queue ve kanıtları takip eder; owner izni olmadan dalları birleştirmez, gerçek grant/deploy/CI genişletme yapmaz.

## Arıza teşhisi
- `root absent/quorum unavailable/partition/epoch stale`: hiçbir otomatik fallback, yeni claim, effect ya da T1 yok — HOLD.
- `old DB+pin restored`: bağımsız root'la çapraz güncellik ve tüketilmiş claim doğrulaması olmadan önceki `ACCEPTED_D0` geçersiz; mevcut D0 kodu henüz bunu sağlamaz.
- `UNKNOWN_COMMIT/lost sink reply`: ayrı `effect_id` ve `transaction_ref` ile salt-okunur uzlaştırma ve karantina; eski isteği yeniden gönderme yok.
- `key rotation/lease expiration`: eski epoch/fence/revoked key geçersiz; consume geçmişi korunur.
- `sink misconfigured/direct bypass`: tüm gerçek etkiler durur; doğrudan erişim yolunu Security ve ToolGateway ayrı incelemeden açma.

## Bakım ve teslimat
- Teknik katalog: `docs/master-integration/GATE02-D03D04-OPTION-A-20261120/TECHNICAL_CATALOG.json`.
- Makinece denetlenebilir mimari kontrat: `docs/master-integration/GATE02-D03D04-OPTION-A-20261120/OPTION_A_INTERFACE_AND_TRUST_CONTRACT.json`.
- 8 özgün negatif senaryo: `docs/master-integration/GATE02-D03D04-OPTION-A-20261120/OPTION_A_INDEPENDENT_ACCEPTANCE_MATRIX.json`, **0/8 bağımsız PASS**.
- Karar: `decisions/ADR/ADR_D03_D04_OPTION_A_20261120.md`; merkezi kuyruk: `progress/MASTER_INTEGRATION_CURRENT.json`.
- Geri dönüş: yönetim commit'ini normal revert; gerçek ürün branch/DB/claims değişmedi.
- İlerleme: IAM/ORG tarihsel 42.5→42.5 (0 pp), genel geliştirme % HESAPLANAMADI, Core kabul 12/16, MVP 0/11, bağımsız IV 0/7. Bu tur yeni fonksiyonel test veya güvenlik kabulü üretmedi.
