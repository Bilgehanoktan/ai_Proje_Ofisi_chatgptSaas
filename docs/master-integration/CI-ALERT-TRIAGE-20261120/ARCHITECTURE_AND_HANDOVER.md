# AI Company OS — GitHub başarısızlık e-postası uzlaştırması / devir

20.11.2026 · Kullanıcının beş ekran görüntüsünde MI-03/PR #6 için üç başarısız koşum, MI-10/PR #4 için de kaynak ve T1 başarılı iken tarayıcı işi başarısız olan koşum var.

## Kesin kanıt — hangi hata daha sonra düzeltildi?

| Hat | Önceki başarısız koşum | Asıl aşama | Son başarılı koşum | Sonuç |
|---|---|---|---|---|
| MI-03 / PR #6 | 44619326736, 44619523838, 44619843185 | Python bootstrap, cryptography ve cffi ortam kurulumu | [44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705), yeniden [44623379375](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44623379375) | 10/10 özgün kaynak Core+OperationsStore sentetik SQLite PASS (tekrar koşum 10 yeni test değildir) |
| MI-10 / PR #4 | 44620487661 | Node QA `vm.runInNewContext` dizilerinin farklı realm prototipleri `deepStrictEqual` sorunu, ürün testinden önce | [44620987573](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620987573) | 3/3 job, 17/17 taze SSE negatif QA, tanısal gerçek Chromium PASS |

Bu satırlar gerçek GitHub Actions run ve job logları üzerinde doğrulandı. GitHub e-posta uyarılarının geçmişte kalması, sistemin bütün kabul kapılarının geçtiği anlamına **gelmez**. İlk PR6 hataları Core uygulama testlerinin başarısızlığını kanıtlamaz; ortam kurulumu başarısızdı. MI10 eski tarayıcı işinde Next build PASS olsa da yeni Node QA assertion başarısızdı.

## Kalan engeller ve öncelikli iş
1. **MI-01/Unified:** W8 `prepare` ile yeni geçici Python wheelhouse, tam `python.lock`, `locks/REVIEW.json` üretmek. Npm özgün sabit lock kopyalanacak, regenerasyon yapılmayacak.
2. **Bağımlılık kaynak sahibi:** wheel SHA256, paket METADATA, transitif sürümler/registry provenance, platform/ABI, güvenlik, lisans ve `REVIEW.json` fingerprint'ini incelemeli. **Onay verilmediği sürece** `install/test/smoke` HOLD.
3. **MI-03/04 sahipleri:** Registry/üye/rol/gerçek issuer ve protected PostgreSQL; eski DB+pin restore zaafı ve IV ayrı engeller.
4. **Orijinal tarayıcı:** native Chromium CDP `Response.text` hatası sürer; geçici SSE per-request uyumluluk testi resmi byte-exact U3 testi değildir.

## Kaynak, katalog ve güvenlik
Bu tur yalnız merkezi durum, kanıt ve devir uzlaştırmasıdır. Ürün dosyası/sınıf/fonksiyon/API/DB/bağımlılık/CI workflow değişimi **0**. Kanonik `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` korundu; PR4/PR6 taslaklar otomatik birleştirilmedi. Dar kapsamlı PR4 ve ayrı açık onaylı PR6 test izinleri genişletilmedi. Genel 15/35/20/20/10 gelişim paydaları dondurulmadığı için ürün geneli gelişim yüzdesi **HESAPLANAMADI**, kabul deltası **0 puan**, W8 işleme hazırlığı **3/8** olarak ayrı izlenir.

## Arıza teşhisi ve geri dönüş
- Aynı isimde yeni başarısız bildirim gelirse, e-posta yerine ilgili commit head ve run ID ile job'ın en son `conclusion` alanını denetle. Eski kırmızı uyarı sıfırlanmaz; yeşil sonraki koşumla uzlaştırılır.
- Test import/setup/registry hatası için doğrulanmış test sonucu yazılmaz. CI test kodunun VM realm hatası için orijinal ürün failure sayılmaz.
- Görevi sahibinden alıp yeni prototip üretme veya başarısız logları geçmişten silme. Geri dönüş: yalnız bu governance notunu normal revert.
- Kaynak: [EVIDENCE.json](./EVIDENCE.json) · [MI01 W8 P0 kapı durumu](../MI01-W8-P0-PROGRESS-20261120/GATE_REGISTER.json).
