# 0162-B uygulama hazırlık sözleşmesi
R8 + 0162-A esas alınır. Kod değil; aday dosya kapsamı ve acceptance.
- UI: Dashboard tek floorId/selection/panel/detail/display sahibi. OfficePanel, AgentDetail, OperationPanel controlled props; floor/view/layout değişiminde reset; klavye erişimi ve static fixture fallback korunur. Canlı join/IO yok.
- Terminal: LogicalIntent, RoleObservation, RunObservation ve HeadReadback exact scope/attempt/expected_version ile bağlanır. before/after digest, tx/event/outbox/lease/budget disposition pinleri; expected+1 overflow check. Admitted terminal 8 rol; pre-admission stop ayrı kapsam, hayali lease/budget yok. Expired worker yazamaz; control-plane stop ayrı yetki. SUCCEEDED artifact/receipt gerektirir, release değildir. UNKNOWN dış etki ve terminal state ayrı.
- Reconciliation: exact scope/effect/idempotency/request/event/outbox/commit/claim generation/correlation. Historical vs current epoch ayrı; UNKNOWN/CONFLICT quarantine; confirmed applied no resend; confirmed not applied no automatic retry. Structural match proof değildir.
- Settlement: reservation ID != budget ID; company-period head != run scope; economic_event_id/digest, currency/minor-unit, CAS. Unknown exposure tutulur; duplicate same digest diagnostic, different digest conflict; overage HOLD, no clamping/FX/posting.
- IV: receipt shape != real signature; owner algorithm, trusted time, custody, revocation ve release CAS ayrı. No actual release.
- W2/W8: 20 partial field crosswalk, 30 documentary oracles, 65 existing tests NOT_RUN; 0/16 owner, 0/55 fields. No API/schema/dependency changes.
- Sıra: UI bağımsız; terminal/reconciliation ortak identity şartına, settlement outcome semantics'e bağlı; IV custody paralel. Kaynak scope yetkisi olmadan uygulama dosyası değişmez.
