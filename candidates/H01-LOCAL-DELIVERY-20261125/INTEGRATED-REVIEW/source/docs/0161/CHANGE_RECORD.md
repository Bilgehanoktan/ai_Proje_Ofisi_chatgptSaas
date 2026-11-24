# 0161 değişiklik kaydı
Neden: R03/R11/R07 ve görünüm freshness kanıt boşluklarını daraltmak. Nasıl: 8 ek Python dosyası, mevcut 114 kayıt byte-exact. Yeni API, DB, paket bağımlılığı, fiziksel tablo veya etkin CI yok. Kaynak katalog v1.20.
- W4: core/transaction/readback_review.py; head/admission/lease/budget binding; fiziksel mapping HOLD.
- W7: engines/budget_engine/reservation_review.py; observability/finance_projection.py; sentetik kapasite ile gerçek finans ayrımı.
- W6: core/policy/receipt_review.py; byte/readback ve signer/root/validity/tombstone.
- W1: engines/office_engine/freshness.py; canlı join DENY, mevcut UI değişmez.
- W2: contracts/OWNER_REVIEW_0161.json; 16 hash eşleşti, owner kabul yok.
- W8: tests/test_review_0161.py; 17 aday NOT_RUN.
Bakım: önce scope/epoch ve expected reference, sonra CAS/digest/transaction/currency/limit, IV byte pin ve revocation; yanlış değerlerde HOLD. Geri dönüş: önceki 0160 commit/ZIP'e dön; manifest ve katalog birlikte geri alınır, force push yok.
Geçici tercihler: pozitif minor-unit rezervasyon, üç harfli para birimi yalnız şekil, 1 MiB sentetik IV byte sınırı, supplied tick. Bunlar owner kararları veya gerçek yetki değildir.
