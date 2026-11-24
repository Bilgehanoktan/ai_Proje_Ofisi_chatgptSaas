# DOC-REV-0162-C — karantina kaynak adayı eki
14.11.2026 · Kaynak: R8 `da669e9ca4db6b87cc7f598c5eab767888c30e83`, 0162-B `f799a69f93be27040b16ee6f33358c9a8f7e8bd8`. Tam master yerine geçmez. [Mimari indeks](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/f799a69f93be27040b16ee6f33358c9a8f7e8bd8/docs/architecture/DESIGN_MASTER.md); [0162-A](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/f799a69f93be27040b16ee6f33358c9a8f7e8bd8/docs/0162A/ARCHITECTURE_ADDENDUM.md); [0162-B](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/f799a69f93be27040b16ee6f33358c9a8f7e8bd8/docs/0162B/IMPLEMENTATION_CONTRACT.md).

Kullanıcının mevcut mesajı çalıştırılmayan adaylar için yön talimatıdır; normatif P02/P03/P04/P05/P07 açık. Product/ altındaki 123 Git blob kaydı 0161 ile 0162-B arasında aynı. IV receipt_review.py değişmedi. R8 ürünü, ana dal, API, DB, schema ve dependencies değişmedi. Karantina dosyaları ayrı aday; import/run/build/test/CI yok.

## D07/D15 — Terminal
Admitted terminal 8 mantıksal rol; başlık CAS expected+1, attempt, scope, admission, lease/fence, mutation hash ve event/outbox kimlikleri eşleştirilir. Pre-admission stop ayrı HOLD. Control-plane stop ayrı authority/trusted time gerektirir ve erken HOLD döner. Worker expiry/revoke kontrolü sentetik. Başarı artifact ve receipt digest şekli ister; hiçbir state yazılmaz. UNKNOWN/CONFLICT halinde başarı ve exposure kapanışı yok. R8 AdmissionPin budget ID'yi tutar; reservation ID otoritatif bağ ve fiziksel 4/5/7 eşlemesi açık.

## D15/D16/D21 — reconciliation
Receipt şekli scope/effect/idempotency/request/event/outbox/commit/claim/correlation ve tarihsel epoch ile eşleşir. Güncel epoch ayrı; eski tarihsel delil yetki değildir. Confirmed applied/not applied yalnız claim; independent proof, issuer, zaman, cursor ve causal persistence açık. No resend, no auto retry, no release.

## D17 — Settlement
Budget head company-period, reservation run-scoped; ID ayrımı, minor unit, CAS, outcome receipt bağlama, economic event duplicate/conflict; tutar yoksa exposure korunur. Overage HOLD. Reversal, tax/FX, gerçek ledger, muhasebe ve ödeme bu tur dışı. Reservation sahibi ve ekonomik event authoritative lookup açık.

## D13 — UI
Dashboard tek snapshot seçim sahibi; controlled üç panel, kat/görünüm/layout reset, statik asset ve klavye butonları. OfficeScene kendi bağımsız sentetik geometri seçimini tutar; gerçek snapshot/agent selection ile birleştirilmez. Canlı SSE, gap recovery, authenticated viewer pin, asset rights, browser/a11y acceptance yok. `STATIC_ONLY`, `JOIN_HOLD`, `LIVE_UNAUTHORIZED` yalnız görünüm etiketleri.

## D11 / W2
IV dosyası değişmedi; gerçek signature algoritması, anahtar custody, trust time, revocation, release CAS açık. 20 kısmi alan eşlemesi, 0/16 owner, 0/55 field, 30 documentary oracle korunur. 65 önceki test ve 24 yeni test NOT_RUN. C8 reason strings, extra local pin models, stop lane ve UI reset davranışı normatif olmayan tasarım tercihidir. No merge.
