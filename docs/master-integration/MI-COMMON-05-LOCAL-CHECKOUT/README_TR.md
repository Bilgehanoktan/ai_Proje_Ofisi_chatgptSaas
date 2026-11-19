# AI Company OS — MI-COMMON-05 | Doğrulanmış yerel kaynak aktarımı

**Çalışma:** Yalnızca izinli kaynak arşivini indirir ve doğrular. Paket kurulumu, gerçek servis, test, build, tarayıcı, veritabanı, COMMIT, yetki değişimi, CI veya ürün kabulü gerçekleştirmez.

## Başlangıç

1. `AIOS_MI05_YEREL_AKTARIM.zip` paketini Windows `Downloads` klasörüne kaydedin. Dosyanın adını değiştirmeyin.
2. **Windows PowerShell 5.1** açın. **Yönetici yetkisi gerekmez.** `POWERSHELL_KOPYALA_YAPISTIR.txt` içindeki kodu bir bütün olarak PowerShell penceresine yapıştırın. İsterseniz yanıtın içinde verilen aynı kodu kullanabilirsiniz. Bu yöntem yürütme ilkesini (ExecutionPolicy) değiştirmez.
3. Komut `C:\AIOS\MI05_YYYYMMDD_HHMMSS\` altında yeni klasör açar. C: diskinde yaklaşık 130 MB boş alan yoksa betikteki `$ana = 'C:\AIOS'` satırını `D:\AIOS` gibi uygun bir diskle değiştirin.
4. En az Python 3.10 ve `py` launcher gerekir. 344 testin sonraki koşumu ayrıca özgün Python 3.13.5/SQLite 3.46.1/cryptography 46.0.4 ortamını gerektirir; kaynak aktarımı için bu sürümlerin tümü gerekmez.
5. Başarılı aktarım `verified\TRANSFER_REPORT.json` oluşturur. Bu dosyayı sohbetimize yükleyin. Hata çıkarsa `verified.partial\TRANSFER_HOLD.json` ve terminal hata metnini paylaşın. Token/şifre göndermeyin.

## Kaynak ve doğrulama

- GitHub ZIP: `https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/87272b6aebd1ce4b26d3a789b2ea75e4310cf60a.zip`
- **Beklenen özgün Git ağaç kimliği:** `187f652f1b1ff8604981833f634c4531a33f8a47`
- Dosya sayısı: 1.953. Sıkıştırılmamış kaynak toplamı: 22.342.956 bayt.
- Ürün manifesti Git blob: `03af243e8683f92c5d9c0b24e90b70d2bd6af29f` (538 girdi, 539 ürün dosyası).
- Model/Memory pin dokümanı: `fb1a73c86eda928409c371359056e79ef43665e4` — 114 dosya.
- Tarihsel Core pin dokümanı: `223f6fbd28cf4c428c07eb60dda4a36f644fa58c` — 55 dosya.
- Özgün kurtarma yardımcısı Git blob: `70c9c0970632834a2c4ba9cd4e4d718bfc14c2b4`.

Arşiv ZIP'i otomatik indirilir. GitHub erişimi kimlik doğrulaması istiyor ve indirme başarısızsa, tarayıcıda giriş yaparak **yalnızca aynı commit URL'sinden** ZIP'i indirip arşivi yerel diske kaydedin; Python aracını `--archive "C:\...\kaynak.zip" --output "C:\AIOS\yeni_klasor"` seçenekleriyle çalıştırın. SHA eşleşmeyen kaynaklar reddedilir.

## Oluşan klasörler

- `verified/full_checkout/`: gerçek ortak kaynak commit'inin tüm dosyaları; bütün Git ağaç SHA'sı tekrar hesaplanarak doğrulanır.
- `verified/pinned_regression_stage/model/`: ayrı, 114 dosyalı özgün Model/Memory test kaynağı ve çalıştırıcısı.
- `verified/pinned_regression_stage/core/`: ayrı, 55 dosyalı tarihsel Core kaynağı ve çalıştırıcısı. İki tarihsel dosya güncel ürünün üzerine yazılmaz.
- `verified/git_blob_cache/`: hash içerik adreslemeli kaynak önbelleği.
- `verified/source_commit.zip`: indirilen özgün arşiv; SHA-256 raporda saklanır.
- `verified/TRANSFER_REPORT.json`: kontrol kanıtları ve **testlerin NOT_RUN** durumu.

## Güvenlik ve geri dönüş

Özgün güvenlik/yürütme izinleri aynen korunur. Arşiv doğrulama başarısızsa tamamlanmış klasör oluşturulmaz; `.partial` ve hata raporu incelenmek üzere kalır. Eski `C:\AIOS` klasörleri değiştirilmez. Geri dönüş, yalnızca bu turda oluşturulan ve incelenen `MI05_...` klasörünün kaldırılmasıdır. `integration/product-dev`, `main` ve özgün repo değişmez. Model/Memory 344, tarihsel Core 29, W8 build/browser ve korumalı COMMIT tamamlanmış sayılmaz.

## Bağımsız yerel test kanıtı

Paketin Python arşiv doğrulayıcısı 12/12 sentetik yerel testten geçti (Python 3.13.5, 2026-11-19). Testlerde kaynak ZIP'i **sentetiktir**; 1.953 dosyalık gerçek GitHub arşivi bu sohbet ortamında indirilemedi. Testler gerçek ürünün 344/29 regresyonları değildir.
