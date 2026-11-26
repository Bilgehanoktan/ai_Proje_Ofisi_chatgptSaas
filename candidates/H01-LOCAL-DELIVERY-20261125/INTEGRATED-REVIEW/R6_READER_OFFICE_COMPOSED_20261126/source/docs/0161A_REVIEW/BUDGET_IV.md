# W7 — R11 bütçe ve telemetri; W6 — R07 bağımsız IV

## Budget domain (A0 öneri)
Kaynak bağlantısı: transaction/review.py `LogicalIntent.budget_ref`, `required_roles`; `port.py` CommitIntent; D17 ve NS-C7 FinancialLedgerEntry; disabled model gateway. `budget_ref` bir string'dir, rezervasyon kanıtı değildir.

| Aday nesne | Sahiplik önerisi | Alanlar (normatif değil) |
|---|---|---|
| BudgetLimit | D17 / Finance | tenant/company, currency, period, limit, version, policy pin |
| BudgetReservation | D17 + T1 | reservation_id, scope, run/effect/idempotency key, ceiling decimal, currency, tariff revision, state, CAS version, epochs |
| UsageObservation | Model gateway/telemetry | run/effect ref, provider/model pin, units in/out, estimated cost, observed cost nullable, source evidence, observation time |
| Settlement | D17 | reservation ref, economic_event id, amount/currency, evidence digest, expected budget/reservation version, state |
| FinancialLedgerEntry | D17 (NS-C7 pin korunur) | mevcut şema; gerçek ekonomik olay ve yetkili posting gerekir |

Tutarlar float yerine decimal/string kanonik gösterim; para birimi farklıysa otomatik toplama yok. Tarifeler sürümlü, token/usage tahmini harcama değildir. Available = limit - settled spend - unresolved active reservations (aynı dönem/para birimi, ayrık kayıt kümeleri). Reversal/adjustment ayrı olay; eksi bakiye için otomatik izin yok. Rezervasyonun tek etkide iki kez tüketilmesini scope+effect idempotency fence önler. Egress sırasında canlı bütçe/lease/policy doğrulanır; provider disabled kalır.

Aday geçiş: PROPOSED → RESERVED (T1 admission) → USAGE_PENDING → SETTLEMENT_PENDING → SETTLED; kesin kullanılmadığı yetkili kanıtla RELEASED; belirsiz provider sonucu UNKNOWN_HOLD. Retry/release/settlement, authoritative evidence ve ayrı T1 olmadan yok. Ödeme/tahsilat/billing dış mutasyonları ayrı yetki; F3 sıfır dış yazma. Hiçbir gerçek para hareketi, reservation, ledger post veya provider çağrısı yok.

Arıza teşhis: currency/tariff revision → reservation fence → authoritative usage readback → ledger evidence. Eşleşmeyen tenant, duplicate economic event, yanlış dönem veya stale epoch HOLD/DENY. Finansal düzeltme silme değil, yetkili ve izlenebilir telafi olayı.

## IV trust ve receipt (A0 öneri)
Kaynak: `core/policy/iv_review.py` `TrustPlane`, `ArtifactPin`, `IVObservation`, `inspect_iv`. KS-C3 EvidenceReceipt, KS-C5 ArtifactVersion, NS-C5 ArtifactMetadata, D11.

Aday receipt body: receipt_id, schema/version, tenant/company/environment + task/run/plan scope, artifact_id + exact hash + canonical revision, readback hash + source ref, worktype version, policy/witness epoch, issuer principal + trust domain + key ID, verification rule/version + evidence digest, issued_at/expiry, verdict. Signature envelope: algorithm/key pin, canonical body digest, signature bytes/ref, revocation status. Format/algoritma/key yönetimi kararı bağımsız Security/IV onayı bekler. Mevcut KS/NS şemalarına ek alan yazılmaz; versiyonlanmış mapping tasarımı gerekir.

Sıra: QA observations → ayrı readback → IV bağımsız root/admin/recovery doğrulaması → exact canonical payload imza kontrolü → güncel artifact/policy/WA readback → release issuer ayrı CAS. QA PASS ≠ IV PASS ≠ RELEASED. İmza kimliğini gören QA kendi receipt'ini üretemez; shared credential, shared admin/recovery, aynı trust root kabul edilmez. Farklı string ID gerçek bağımsızlık kanıtı değildir. Mevcut `IVReview` INCONCLUSIVE, receipt_issued=false, release_ready=false olarak korunur.

Bakım/arıza: hash/revision mismatch → artifact yeniden doğrulama; receipt expired/revoked → HOLD; root collision → INCONCLUSIVE; CAS conflict → eski receipt yeni artifact'i yayınlatmaz. Rollback eski receipt/grant'ı canlandırmaz; root rotation ayrı protokol.
