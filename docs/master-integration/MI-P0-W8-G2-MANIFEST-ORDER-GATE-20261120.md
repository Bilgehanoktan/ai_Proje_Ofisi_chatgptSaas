# MI-P0 — W8 ↔ G2 sürüm sırası; 553→556 entegrasyon kapısı (2026-11-20)

**Gerçek GitHub commit ve blob okuma; yeni ürün kodu, test, CI, onay veya otomatik merge yok.**

## 1. Diğer hatlarda gerçek iş durumu
- `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`: 553 product dosyası, 552 manifest kaydı, manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`; source-review PR15 zaten **merged**.
- [PR #19](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19) G2/Authority owner 553 üzerine *izole* 556-dosyalık kaynak adayı: kaynak `e241fb8f486bfbabbead55f5c5e12d47e76407f4`, **555 manifest** girişi, yeni manifest blob `72944260c569ff35c4b7a4c2f7cd9d42e6db5486`. Orijinal G2 50 + ORG 15 birleşik D0 CI [44699083111](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44699083111) 65/65 PASS, ama G2 yetki kararı ve root/issuer/sink güvenliği HOLD.
- [PR #20](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20) MI-01/W8 owner `6678a7fd3aa50842b70b2b8a922c02b002884397`: tarihi npm lock `4cd33f437df85d7e74c7946a0999f76adf2e31fe` bayt-byte aynen alınıyor, helper 15/15 **sentetik** PASS; W8 özgün full C04/C05/C06/C07/C08 hâlâ NOT_RUN/HOLD. PR20'de `product/SOURCE_MANIFEST.json` halen **552 giriş** ve blob `27b4eb...`.
- Özgün owner G2 **50/50**, G9 **7/7** ayrı sabit kaynak CI [44697437051](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44697437051) başarı. Orijinal 0214 **10/10** D0 [44695937454](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44695937454) başarı. Tekrar koşulmadı, security acceptance değil.

## 2. Bulunan deterministik entegrasyon çatışması
- PR20 `tests/integration/w8_unified_u3.py` Git blob `b4043035e75c5a18b7b19a9f18eecfef8e8fe677`, `MANIFEST = '27b4eb5816265d4e6e6d2458acb6220db7dd0c76'`.
- PR19 556 ürün adayının manifesti `72944260c569ff35c4b7a4c2f7cd9d42e6db5486`. İki blob **eşit değil**; W8 U3 `extend(w)` `w.MANIFEST_BLOB != MANIFEST` ise **`U3_MANIFEST_HOLD`** ile fail-closed davranıyor.
- PR20'nin npm helper `verify_frozen_npm_inputs` kaynak `package.json` için blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3` bekliyor; PR19 frontend `package.json` blobu **aynı**. Yani tespit edilen çakışma **npm root package değil, ürün manifesti / W8 çalışma kapsamı**.
- Bireysel PR'ların kendi hedefleriyle `mergeable_state=clean` olması **birbirlerinin birleşik kaynağında W8 PASS olacağı anlamına gelmez**. Bu kontrol bir Git tree/manifest source-pin kıyasıdır, iki dalı gerçekten birleştirme veya tam W8 çalıştırma değildir.

## 3. Çakışmayan ve yetkili görev dizisi
1. **MI-01 W8 sahibi:** Şimdilik 553 ürün/552 manifest bazını sabit tut. PR20 15 helper testini orijinal W8 diye sayma. Onaylı kilidi ve 553 W8 özgün tam `prepare` (C04) / dependency provenance sahibi kabulü (C05) / `install` C06 / `test` C07 / Chromium `smoke` C08 üzerinde uygun izinli çevrimiçi/Windows ortamında gerçekten yürüt. Sonuçları log/source SHA/REVIEW fingerprint ile kaydet.
2. **MI-04 G2/Authority sahibi:** PR19 bağımsız kaynak varyantı yalnız inceleme. G2 `intent_authority.py` `b28788...` vs mevcut `fa47acd...`, IAM `iam_session.py` vb., gerçek root/issuer/claim/sink ve restore-replay izinleri bağımsız güvenlik sahibiyle karara bağlanmadan `product-dev` değiştirilmesin. 65/65 sentetik uyumluluk kabul değildir.
3. **Şartlı 556 transferi:** G2 kaynak sahibi daha sonra **yazılı kararla** PR19'u entegrasyona alırsa manifest Git SHA `72944260...` ve kaynak kapsamı için MI-01 sahibi W8 adapter pinini *yalnız owner-reviewed exact source* üzerinden yeniden sabitlesin; `prepare/install/test/smoke` ve native Chromium kanıtı yeni 556 sürüm için yeniden üretilecek. W8 pinlerini dinamik veya gevşek doğrulamayla ikame etme.
4. **Bağımsız güvenlik/PG/IV:** Gerçek nonowner RLS/PG COMMIT, anti-rollback + root/claim/sink ve A-AT01..08 bağımsız negatif testler bitene kadar PROD/release/gerçek yetki **HOLD**.

## 4. Yapılan işlem, bakım, rollback, devir
- Bu tur yalnız gerçek GitHub blob/readback incelemesi, [PR19 yorum #7034065059](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/19#issuecomment-7034065059), [PR20 yorum #7034065801](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/20#issuecomment-7034065801) ve governance/görev kaydıdır.
- Dosya, class/fonksiyon, API, DB, event ve package değişikliği **0**. Yeni fonksiyonel test **0**. CI, main, product-dev, grants, deploy, provider, PROD değişiklik **0**. Bu rapor mevcut PR sahibinin özgün modüllerini değiştirmez.
- `U3_MANIFEST_HOLD`: önce yürütülen ürün manifesti SHA ve runner `MANIFEST` SHA karşılaştır. `W8_IMMUTABLE_NPM_*_HOLD`: npm lock bytes/Git SHA/root package blob/owner onayı kontrol et. PASS elde etmek için otomatik yeniden pinleme yapılmaz.
- Geri dönüş yalnız bu governance dosyasını normal revert; PR19/20 source ve product-dev kaynakları korunur. Yeni PR head/ürün SHA gelirse kıyas yeniden yapılır; hashleri eski sürümlerden otomatik güncelleme.

## 5. Kanıt bazlı ilerleme
- İlgili görevde **çakışma/bağımlılık kararı** iki PR sahibine iletildi; önceden raporlanmayan potansiyel entegrasyon STOP tespit edildi. Test/build/ürün kabul **Δ0**.
- W8 operasyonel **3/8→3/8**, IAM/ORG geliştirme %42,5→%42,5 (kriterlerin aynı kapsamı), kanonik Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**. Bağımsız A negatifleri **0/8**. Genel ağırlıklı geliştirme 15/35/20/20/10 **HESAPLANAMADI**, sabit genel denominator yok.
- Sonraki merkez görevi yeni prototip değil, W8 bağımlılık sahibinin 553 özgün tam chain kanıtı ve G2 korumalı kaynak sahibi kararı sonrası **tek writer** transfer/readback.
