# Bakım / teşhis / genişletme

- **reconciliation_review.py**: Correlation, effect/idempotency, epoch ve receipt farkını incele; sağlayıcıya yeniden gönderme yok.
- **terminal_review.py**: CAS, lease, mutation ve rol kimliklerini sırasıyla incele; fiziksel T1 ve kontrol düzlemi açık.
- **settlement_review.py**: Period, currency, outcome, duplicate ve CAS kontrolü; hiçbir posting/FX yok.
- **test_review_0162.py**: Yetkili test ortamı ve scope olmadan import/collect yok.
- **AgentDetail.tsx**: Eksik rol durumunda boş görünüm; gerçek ajan oluşturma yok.
- **OfficePanel.tsx**: Layout revision uyuşmazlığında join yok; geometri preview yerel seçimi gerçek ajan değil.
- **OperationPanel.tsx**: Panel owner Dashboard; hiçbir gerçek onay işlemi yok.
- **Dashboard.tsx**: Kat/view/layout reset; statik fallback; eski Dashboard blob ile geri dön.

Yeni alanlar önce owner/crosswalk ile; kanonik sözleşme veya reason code uydurma. Yeni kat gerçek floor graph ve viewer pin ile; UI karantina dışında değiştirilmez. Yeni settlement tipi reversal için ayrı economic event ve owner kararı gerektirir.
