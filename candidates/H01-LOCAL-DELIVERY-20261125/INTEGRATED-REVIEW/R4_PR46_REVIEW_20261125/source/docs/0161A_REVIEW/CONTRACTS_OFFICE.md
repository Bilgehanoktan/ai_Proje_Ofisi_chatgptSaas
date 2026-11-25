# W2 R06 sözleşme sahipliği ve W1 ofis entegrasyonu

## R06 — 16 sözleşme, 0/16 gerçek sahip
Kaynak: `docs/0158/R06_SCHEMA_CUSTODY_0149.json`, `contracts/PIN_REGISTRY_0159B.json`, `docs/architecture/OWNERSHIP_MAP_0160.md`. Aşağıdaki owner'lar domain rol önerisidir; atama ya da imza değildir.

| Pin | Nesne | Aday owner | Tüketici / review |
|---|---|---|---|
| KS-C1 | IdentityScope | D12 | D14/D07 |
| NS-C1 | EventEnvelope | D15 | D07/D14 |
| KS-C2 | GrantDecision | D14 | D07/D12 |
| NS-C2 | TaskExecution | D07 | D14/D15/D17 |
| KS-C3 | EvidenceReceipt | D11 | D14/D18 |
| NS-C3 | StateMutation | D15 | D07/D14 |
| KS-C4 | CausalEvent | D15 | D07/D13 |
| NS-C4 | AuditEvent | D15 | D14/D16 |
| KS-C5 | ArtifactVersion | D15 | D10/D11 |
| NS-C5 | ArtifactMetadata | D15 | D10/D11 |
| KS-C6 | TimeContext | D15 aday; D10 time semantics | D10/D07 |
| NS-C6 | ApprovalTicket | D06 | D18/D14 |
| KS-C7 | IdempotencyFence | D15 | D14/D21 |
| NS-C7 | FinancialLedgerEntry | D17 | D15/D20 |
| KS-C8 | DecisionResult | D14 aday | D18/D15 |
| NS-C8 | IdentityCapabilityToken | D14 | D12/D07 |

16/16 owner önerisi, 0/16 owner kabulü. 55 canonical alanın özgün mapping sicili tam olarak yeniden doğrulanmadı; 0/55 kabul korunur. Tüm 16 orijinal pin/hash ve dokuz D0 FE/BE pin çifti değişmeden kalır. KS-C6/KS-C8 önerileri özellikle sahiplik review gerektirir. Mevcut backend contracts/source → frontend contracts/generated tek yönlü kopya; kök registry yalnız indeks. Yeni version, schema hash, field-level source mapping ve backward compatibility kararı olmadan değişiklik yok. ID, digest veya schema valid olması grant değildir.

## W1 — canonical layout ve freshness
Gözlem: iki fixture aynı floor-1/floor-2 ve dört station-orchestrator/research/engineer/qa ID'sini içerir; snapshot `draft-hybrid-floor-1`, core `layout-d3-demo`. Bu eşleşme tek başına fiziksel koordinat/semantic scope kanıtı değildir. Snapshot şemasında tenant_id, world_id, environment_id, snapshot_seq, layout_revision, as_of, data_status, policy_epoch, wa_epoch mevcut; company_id ve layout_digest üst düzeyde mevcut değil. Core preview layout'ta revision, width, height, floors vardır. Eksik bağlar için yeni aday sözleşme gerekir; mevcut fixture değiştirilmez.

Önerilen tek yönlü kanonik join: `(tenant_id, company_id, environment_id, world_id, layout_revision, layout_digest)` eşleşmesi → snapshot sequence/epoch/freshness kontrolü → room/station/role referans kontrolü → render. floor/station/room ID scope'u açık olmalı; cross-floor duplicate, orphan station, yanlış role, reserved floor aktivasyonu reddedilir. Mevcut TS `validateDemoLayout` iki kat, global station uniqueness, kat2 reserve, integer cells ve renk doğrular; Python `validate_layout` daha dar bir kontrol seti kullanır. İki doğrulayıcı için aynı oracle fixture ve hata anlamları tasarlanmalı; bu turda eşdeğerlik kanıtlanmadı.

Freshness durum adayları: UNKNOWN/STALE/RECONNECTING/CURRENT; sequence gap, epoch mismatch, expired snapshot, missing digest, layout mismatch → HOLD, animasyon durur, görünüm son doğrulanmış snapshot'ı açık uyarıyla gösterebilir; canonical run state değişmez. Sentetik demo hareketleri canlı telemetri gibi sunulmaz. Replay ve duplicate sequence ayrı, projection source event id bağlanmalı. UI karar kutusu yalnız gösterim; grant, state, approval, release yazmaz. Aktif floor/selection değişince bağlam sıfırlanmalı (mevcut changeFloor davranışı korunur).

Aday UI ayrıştırma: `Dashboard.tsx` state/navigation sahipliği; `OfficePanel`, `StationList`, `AgentDetail`, `OperationPanel` salt-okunur props; ortak selection controller; `SnapshotStrip` ve `MetricsStrip` mevcut. Footer release metadata tek kaynak önerisi; route ve CSS mevcut davranış korunmalı. Yeni Phaser migration, fiziksel ofis aktivasyonu veya API bağlama bu turda yok.

Arıza: join mismatch → revision/digest + scope; yanlış avatar → snapshot_seq/epoch ve role binding; floor navigation → selection/reset; geometry divergence → iki validator oracle. Geri dönüş 0160 dosya pinleri; facade importlar ve existing fixture'lar korunur.
