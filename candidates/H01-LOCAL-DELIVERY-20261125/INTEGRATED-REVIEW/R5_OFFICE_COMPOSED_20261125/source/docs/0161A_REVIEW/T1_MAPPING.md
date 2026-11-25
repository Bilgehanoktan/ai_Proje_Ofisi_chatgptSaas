# W4 — R03/R01/R02: T1 ve runtime eşleme tasarımı

## Tarihsel sayıları koru
`docs/0158/R03_T1_PHYSICAL_MAPPING_0157.md` dört fiziksel tabloyu, beş eş-tutarlı readback'in beşinci adının UNKNOWN olduğunu ve D4 yedi mantıksal varlığını ayrı soyutlama olarak tanımlar. 0157/0160 `review.py` ise 6 temel rol, lease/budget ile 8 ve admission ile 9 rol gözlemi içerir. Sayılar birbirinin yerine kullanılamaz.

| 0160 mantıksal rol | D0 fiziksel aday bağ | Otorite / açık nokta |
|---|---|---|
| HEAD | UNKNOWN; state_mutations geçmişi aday bağ, head satırı bilinmiyor | D15/DBA; CAS için lock edilen otoritatif head gerekiyor |
| MUTATION | state_mutations | D15; expected/new version, before/after digest |
| FENCE | idempotency_fences | D15/D14; scope + effect identity unique, epoch kontrolü |
| EVENT | UNKNOWN; outbox içindeki payload veya ayrı event kaydı seçenek | D15; committed event kimliği ve payload kaydı ayrı doğrulanmalı |
| OUTBOX | transactional_outbox | D15; T1 commit ve fence referansı, claim ayrı işlem |
| AUDIT | audit_ledger | D15/D14; audit ve event semantiği ayrılır |
| ADMISSION | UNKNOWN | D07; scope/grant/lease/budget bağları |
| LEASE | UNKNOWN | D07/D14; lease owner/fence/expiry/epoch |
| BUDGET | UNKNOWN | D17; rezervasyon ve rezervasyon head'i |

Dört tablo adı tarihsel kaynak; rol→tablo bağları bu turda öneri. **Beşinci readback UNKNOWN kalır.** Head/admission/lease/budget için yeni tablo adı, event-outbox fiziksel birleşimi veya ek tablo sayısı seçilmedi. 7 mantıksal varlık ile rol seti birebir eşleştirilmedi. DBA/Runtime/Security/Finance sahipleri henüz yok.

## İşlem bazlı aday küme
| İşlem | Mevcut D0 required_roles | Ek tasarım yükü |
|---|---|---|
| ADMISSION | HEAD MUTATION FENCE EVENT OUTBOX AUDIT ADMISSION LEASE BUDGET | reserve ve lease edinimi aynı transaction; mevcut taze lease şartı ile ilk lease edinimi ayrıştırılmalı |
| STATE_MUTATION | 6 temel rol, lease/budget değişirse 8 | transition+CAS, mevcut lease ve scope, budget etkisi varsa aynı işlem |
| TERMINAL | 6 temel + LEASE BUDGET | terminal sürüm, lease kapatma, kesinleşen rezervasyon settlement; UNKNOWN ise rezervasyon hold |
| RENEWAL | mevcut enumda yok | beklenen lease sürümü/fence/epoch, authoritative clock, eski sahibi fencing; yazma kümesi onaysız |
| OUTBOX_CLAIM | mevcut enumda yok | commit/fence/claim generation, atomik claim CAS; egress ayrı PEP |
| RECONCILE | mevcut enumda yok | gerçek readback/receipt, effect key; unknown marker'ı yalnız kanıtla temizle |

Admission ilk lease edinimi ile mevcut lease gözlem kontrolü arasındaki gerilim açık bir **tasarım sorusu**, çalışan hata iddiası değil. `RoleObservation.record_id` tüm roller için benzersizlik şartı koyuyor; fiziksel eşlemede tek fiziksel kayıt birden fazla mantıksal rolü kanıtlıyorsa, rol kimliği ile satır kimliği ayrımı şart. Kaynak değiştirilmedi.

## Transaction yürütme sırası (gelecekte, izinli)
1. Exact scope ve grant/effect binding kontrolü; taze W-A ve policy epoch, authority readback.
2. Transaction aç; aday lock sırası: tenant/aggregate head, budget head, lease/fence, mutation/event/outbox/audit. DBA deadlock incelemesi gerektirir; henüz normatif değil.
3. Expected version CAS, idempotency identity/digest, rezervasyon limiti ve lease fence yeniden doğrula. Yeni/önceki durum ile mutation digest bağla.
4. Eksik rol, yanlış epoch, yarış veya kısıt ihlalinde tüm yerel değişiklikleri rollback et. Aynı ACID sınırında gerekli state/lease/budget/event/audit/outbox kayıtlarını bağla. Dış sağlayıcı çağrısı transaction dışıdır ve mevcut F3'te kapalıdır.
5. Commit sonrası aynı tutarlı readback view'da write-set doğrula. Tek transaction_ref string'i commit kanıtı değildir. Readback tanımları ve otoritesi (özellikle beşinci) HOLD. ACK kaybı → UNKNOWN, tekrar eylem yok.

## Şema karar seçenekleri (yeni karar gerekirse)
A: head/admission/lease/budget ayrı fiziksel kayıtlar; B: aynı aggregate altında bazı kayıtlar birleşik, açık rol eşlemesi; C: önce özgün v112/v122 readback hükmü ve DBA incelemesi. **Öneri C**, A/B'yi bugün seçmek yok. Farklı şema alternatifleri 4/5/7 tarihsel metni kendiliğinden değiştirmez.

## Arıza teşhis ve rollback
CAS mismatch: authoritative head + expected version + scope → plan yeniden değerlendir; kör retry yok. Fence mismatch: lease generation/epoch + W-A custody. Bütçe açığı: reservation evidence/ledger; bilinmeyen sonucu geri serbest bırakma. Readback uyumsuzluğu: transaction id, commit log, fence/outbox/audit bağları; quarantine. Rollback kaynak dalı değişimidir, eski lease/grant/outbox canlandırılmaz. DB migration/revert yok.
