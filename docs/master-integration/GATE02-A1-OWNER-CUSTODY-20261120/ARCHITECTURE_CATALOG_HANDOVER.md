# GATE-02 — A1 bağımsız yetki kaynağı: sahiplik, sınırlar ve devir
Tarih: 2026-11-20 · **İnceleme adayı; A1 imzası yok; GATE-02 HOLD.**

## Mevcut mimari / önceki karar
Normatif yön [ADR D-03/D-04 Seçenek A](../../../decisions/ADR/ADR_D03_D04_OPTION_A_20261120.md). Seçim yeniden açılmadı. Root ve tüketilmiş claim defteri uygulamadan **hem idari hem geri yükleme bakımından bağımsız**, lineer tutarlı uzlaşı otoritesinde; harici etki alıcısı ayrı fence/idempotency denetçisi olacak. Consensus sağlayıcısı, quorum sayısı, KMS, issuer ve sink seçilmedi.

Kanonik `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` **değişmedi**. PR #6 özgün Core–OperationsStore sentetik D0 `10/10 PASS` koşumu (CI `44620141705`) bu turda tekrar yapılmadı; gerçek yetkilendirme veya PG kanıtı değildir. D0 eski veritabanı+eski authority+pin restore sonrası tekrar kabul kusuru **doğrulanmış açıklıktır**. Özgün G2 50, G9 7, Memory–T1 0214 10, strict PG, sink ve IV açık.

## A1 izinli çıktısı
Bu tur, önceki 12/12 statik denetimi ve özgün Git blob'larını **sahiplere karar verebilecekleri on maddelik kapanış matrisine** dönüştürür; gerçek owner imzası üretmez. Makinece okunur [A1_OWNER_BOUNDARY_MATRIX.json](A1_OWNER_BOUNDARY_MATRIX.json) kayıtlarında A1-01..A1-10 her biri `PENDING_OWNER`. Bağımsız güvenlik 0/8.

## Sınır çizimi
```text
Core / ORG / D4 / G2 (owner-issued evidence) -- untrusted client -->
  IndependentAuthority [separate admin + restore + KMS, linearizable root/consumeClaimOnce]
     -- consumed-claim proof (before T1) --> Protected T1 PostgreSQL (commit-time recheck)
     -- stable effect_id --> independent EffectSink
           [fresh epoch/fence + atomic effect-ID dedup + no direct bypass]
              --> reconcile by claim/transaction/effect or UNKNOWN_HOLD
Independent IV independently tests security/restore/quorum and alone may issue independent acceptance.
```
Bu veri akışı **hedef tasarımdır, çalışan entegrasyon değildir**. T1 ile harici sink arasında tek fiziksel transaction yoktur. Tüketim sonrası çökme veya kayıp ACK, otomatik yeni claim/retry değil `UNKNOWN_HOLD` ve bağımsız uzlaştırma gerektirir.

## Dosya/sembol/API/DB/event ve bağımlılık kataloğu
- D4 `identity_binding.py::{Request,review_binding,review_boundary}` — çağıranın sunduğu kimlik/rol gözlemlerini karşılaştırır; issuer değildir (blob `e1e97788`).
- Core `intent_identity.py::derive_request` — Member/intent kapsamı bağlar, gerçek oturum kaynağı değildir (blob `472b2a5f`).
- ORG `assignment_lifecycle.py::{AssignmentPin,ApprovalObservation}` — issuer/custody değerleri sentetiktir; `commit_allowed=False` (blob `9f259e89`).
- G2 `iam_session.py::{D0SessionResolver,SessionClaimCheck}` — D0 kayıtları ve oturum claim incelemesi; gerçek bağımsız role issuer değildir (blob `f3c37428`).
- T1 `fenced_transition.py::D0IntentJournal` — uygulama-içi fence/journal; harici root veya gerçek etki alıcısı değildir (blob `b43a8d11`).
- Çakışma 1: `intent_authority.py` G9 `fa47acd3…` / G2 `b28788f4…`. G2 korumalı wrapper'ın `claim_and_fence()` çağrısında `session_check` iletimi yok; sahip kontrollü ayrı giriş gerekir. **Otomatik repin/merge yapılmaz.**
- Çakışma 2: `durable_ops.py` özgün G9 `43ed448c…` / ORG eki `619fe224…`; ORG/Core sahip incelemesi beklenir.
- Tasarlanan, **mevcut olmayan** ara yüzler: `IndependentRootSnapshotV1`, `ConsumedIntentClaimV1`, `SinkFenceAcceptanceV1`. Öngörülen `rootRead`, `consumeClaimOnce`, `sinkAcceptEffectOnce`; gerçek API, SQL DDL, olay yayıncısı, sağlayıcı, dependency veya credential eklenmedi.
- Mantıksal olay tasarımı: `CLAIM_CONSUMED`, `EFFECT_ACCEPTED`, `OUTCOME_UNKNOWN_QUARANTINE`; çalışan event stream yok.

## A1 sahip incelemesinin çıkış ölçütü
1. Güvenlik/IndependentAuthority sahibi ayrı admin, restore ve audit sahiplerini; üretim/tenant kimlikleri ile ortak yetki bulunmadığını; quorum kaybında fail-closed davranışını onaylamalı.
2. IAM, Core, ORG sahipleri güncel owner-issued registry, session, membership ve assignment/role zincirini referans hash/revizyon + iptal/güncellik test planıyla bağlamalı; sentetik `ApprovalObservation` grant sayılmamalı.
3. T1/DB ve EffectSink sahipleri root/consume-before-T1, COMMIT yenileme, bağımsız fence ve atomik effect-ID dedup sınırlarını, doğrudan effect bypass'ın nasıl engelleneceğini tanımlamalı.
4. IV, restore/partition/key-rotation/lost-ACK dahil mevcut **A-AT01..08** bağımsız kabul protokolünü ve yürütme yetkisi gerekliliğini onaylamalı. **Burada hiçbir onay elde edilmedi.**
5. ORG/G9/G2 tek-yazıcı dosya sahipleri sürüm farklarını ve değişmeden korunacak özgün regresyon pinlerini uzlaştırmalı. Böylece ileride hazırlanacak A2 kaynak sözleşmesi yeni bir ikinci IAM motoru üretmez.

## Test / ilerleme / bakım / geri dönüş
- Bu tur **0 yeni fonksiyonel test**, **0 güvenlik testi**, 0 ürün/API/SQL/event/CI değişikliği. Ayrı A1 gözden geçirme 0/10 `PENDING_OWNER`; bu **geliştirme %si veya ürün kabulü değildir**.
- IAM/ORG tarihsel ağırlıklı geliştirme %42,50 → %42,50 (Δ 0); Core 12/16, MVP 0/11, bağımsız güvenlik 0/7. Genel ağırlıklı geliştirme: **HESAPLANAMADI** (onaylı toplam payda eksik).
- Arıza sınıfları: root unavailable/partition, stale epoch/fence, expired/revoked session, old DB/pin restore, lost COMMIT/sink ACK, direct effect endpoint. Tümünde `HOLD`; eski makbuz/yerel imza veya otomatik retry güven oluşturmaz.
- Geri dönüş: yalnız bu inceleme dalındaki belge/ilerleme önerilerini normal revert etmek ya da taslak PR'ı kapatmak. `product-dev`, `main`, owner dalları ve önceki ADR/kanıtlar korunur. İlerideki gerçek consumed-claim'ler **asla** geri dönüşle sıfırlanmaz.

**Sonraki işlem:** sahipler A1-01..10 kararlarını ve kaynak-diff sahipliğini gözden geçirir; imzalar ve izinli kapsama alınmış A2 kaynak planı olmadan gerçek authority, effect, protected PG veya bağımsız kabul başlatılmaz.
