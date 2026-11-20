# MI-05 — Canonical 553 Projection Read yeniden regresyonu
**20.11.2026 · Mevcut kaynak, gerçek yerel sentetik D0 test · Güvenlik/MVP kabulü değil**

## Kaynak, neden ve yapılan işlem
Açık MI-05 frontend projection işindeki mevcut `readProjection` salt okunur geri okuma fonksiyonunu güncel `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` üzerinde doğruladım. PR20 (MI-01/W8), PR19 (MI04/G2/ORG), PR10 (A1) başka sahiplerde açık; hiçbirine kaynak değişikliği yapılmadı. GitHub üzerinde MI-05 için yeni açık PR tespit edilmedi.

**Test edilen özgün üç Git blob** ve teknik katalog:
- `product/ai-company-os-frontend/features/data/projectionRead.ts` — `fc7ab9b7fb55c871fc2d82a701db89e0945e7aed`; `readProjection`, `createProjectionReader`, `readStatus`; fixed D0 GET, no-store, no redirect, response byte cap, abort, timeout, fail-closed HOLD.
- `product/ai-company-os-frontend/features/organization/organizationProjection.ts` — `cb824d03aa76b45aae3f7f11237f4f6fa82fd96f`; `organizationCap`, `parseOrganization`; D0 only, no dispatch authority.
- `product/ai-company-os-frontend/tests/projection-read.test.cjs` — `226e0e9721677235184547b8d79e91b2e6c541fb`; değiştirilmemiş 12 özgün Node test vakası.

Her kaynak kopyasının `git hash-object` değerini gerçek GitHub blob kimliğiyle karşılaştırdım: **3/3 exact**. Yerel Node `v22.16.0`, global TypeScript `v5.8.3` ile `tsc --target ES2022 --lib ESNext,DOM --strict --module commonjs` **PASS**, ardından gerçek `node tests/projection-read.test.cjs .../build/data/projectionRead.js` **12/12 PASS, 0 fail, 0 skip**. Kapsam: GET/endpoint, HTTP/media/JSON/UTF8, authority spoof, byte limiti, stale response, cancel, timeout HOLD.

**Çift sayım engeli:** Eski `MI-COMMON-03-SELECTED-REGRESSION` kanıtında `projectionRead 12/12` zaten var. Bu, **güncel 553 kaynakta özgün 12 yöntemin tekrar koşumudur**, 12 yeni özgün test veya yeni ürün kabulü değildir. TAP SHA-256 `48983e93c970df32fd5b59aab3cfb4f0ad7635b2df14220fc6a8059180f1042d`. Ayrıntılı source hash ve kanıt [EVIDENCE.json](EVIDENCE.json) içindedir.

## Sınır ve açık entegrasyon
Proje frontend'inin pinli TypeScript'i `5.9.3`; yereldeki `5.8.3` onun yerine tam build kabulü vermez. Tam 553 checkout, npm lock/kurulum, backend, gerçek U3 Chromium ve Office–Runtime aynı-oturum projection doğrulaması **NOT_RUN/HOLD**. API, sınıf sözleşmesi, veri tabanı, event, bağımlılık, manifest, yetki, CI, frontend/backend üretim kaynakları bu tur **değişmedi**.

**Sonraki görev (MI-05/06 sahibi):** MI-01'in mevcut W8 kilit/kurulum hazırlığı tamamlandığında aynı pinned 553 source üzerinde tam frontend+backend+native U3 browser/snapshot kontrolü. MI-02 strict PostgreSQL, GATE-02 bağımsız issuer/root/sink/IV ayrıca HOLD. Yeni prototip açma ve eski testleri yeniden yazma.

**İlerleme:** Geliştirme %15/35/20/20/10 için onaylı global kriter paydaları yok → önceki/güncel **HESAPLANAMADI**. Core 12/16=%75, UI 21/40=%52,5, MVP 0/11=%0, IV 0/7; önceki/güncel aynı, delta **0**. Geri dönüş yalnız governance belge revert'idir; `product-dev`, `main` ve diğer sahip dalları korunur.

## Ek — özgün ham test dosyaları GitHub'a aktarıldı

- [TAP test logu](MI05_553_projection_read_tap.log) — **1624 byte**, Git blob `10e2ba5ef2ba7cbb40c3890419ad42aae10146a2`, SHA-256 `48983e93c970df32fd5b59aab3cfb4f0ad7635b2df14220fc6a8059180f1042d`.
- [JSON özgün test raporu](MI05_553_projection_read_evidence.json) — **3648 byte**, Git blob `f6b9537c83df0bfa66f556e7f3af1917f38e6fee`, SHA-256 `37ad0f1deba8367af3866c2b7ec6d3779a85f146474666fdea408cba27e6a906`.
- Ham dosyalar yerel kaynaklarıyla **Git blob düzeyinde birebir** geri doğrulandı. Bu aktarım yeni test koşumu veya kabul artışı değildir; önceden kanıtlanan **12/12 gerçek yerel D0 regresyonu** destekler. **Tam 553 frontend Next build, U3 browser, bağımsız PG/security kabulü HOLD**.
