# AI Company OS — PC'de gerçek test koşumu (20.11.2026)

Bu paket, mevcut `integration/product-dev` kaynağını **değiştirmez**. GitHub'dan iki tam kaynak checkout'u *ayrı klasörlerde*, kesin commit SHA ile indirir. G7 için özgün 7 testi güncel ürün `OperationsStore` sınıfıyla dener. W8 için yalnız kaynak denetimini ve **C04 (prepare: sabit npm lock + wheelhouse indirme ve inceleme envanteri)** aşamasını dener. Ayrıca PostgreSQL'in sadece 127.0.0.1:5432 portunda erişilebilirliğini kontrol eder; PostgreSQL veri/tablo/şema **değiştirmez**. Başarısız olan gruplar diğer testlerin devam etmesini engellemez.

Bu ChatGPT oturumunda yalnız ayrı bir Linux konteyneri ve GitHub bağlantısı var; **Windows PC üzerinde komut çalıştırma yeteneğim yok**. PC'nizde Python 3, Git, Node.js ve npm kurulu olmalı; GitHub deposuna `git clone` erişimi bulunmalı. Bağımlılık indirmeleri için internet gerekir. Bu paketin kodunu inceleyerek çalıştırın.

## Tek komut — PowerShell

ZIP'i örneğin `C:\AIOS\TEST_KIT` klasörüne çıkartın. PowerShell'de bu komutu çalıştırın:

```powershell
python -B 'C:\AIOS\TEST_KIT\aios_pc_runner.py' --mode allsafe --root 'C:\AIOS\TEST_RUN_20261120'
```

İsterseniz ZIP içindeki `run_example.ps1` aynı komutu çalıştırır. `git clone` izin hatası çıkarsa Windows'daki GitHub kimlik erişimini çözün; giriş bilgilerini bu sohbette paylaşmayın. Kaynak SHA uyuşmazlıklarında betik kendiliğinden durur, **hash/lock repin yapmaz**.

Kayıtlar: `C:\AIOS\TEST_RUN_20261120\PC_TEST_RESULTS.json` ve `logs\*.log`. **Sonuç JSON'unu ve log dosyalarını** bu sohbete yükleyin; güvenlik için içerisinde token, parola veya özel veri olmadığını siz de kontrol edin. `G7_RESULT.json` yalnız G7 gerçekten 7/7 çalışmışsa üretilir. W8 `locks\REVIEW.json` ancak C04 PASS olduysa oluşur. Başarılıysa C05 bağımsız sahip incelemesi yapılmadan W8 install/test/browser'a geçmeyiz.

## W8'in ikinci aşaması — yalnız C05 onayından sonra

Aşağıdaki parametrede, review dosyasının hash'i **sahip tarafından incelenmiş/onaylanmış** olmalıdır; dosyanın hash'inin bulunması tek başına onay değildir. Herhangi bir otomatik yetki/CI/PROD yoktur.

```powershell
python -B 'C:\AIOS\TEST_KIT\aios_pc_runner.py' --mode w8full --root 'C:\AIOS\TEST_RUN_20261120' --approved-review-sha '<ONAYLANAN_64_HEX_SHA256>' --chromium 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

Bu ikinci aşamada özgün W8 çalıştırıcısının sırasıyla `install → test/Next build → smoke/native Chromium` çağrıları kullanılır. Uygulamanın gerçek kaynak testleri çalışmadan hiçbir sonuç PASS sayılmaz. Mevcut sistemde C05 sahibi ve bağımsız güvenlik otoritesi HOLD olduğu için bu aşama **kendiliğinden başlatılmaz**.

## Kesin sürüm pinleri

- Kanonik ürün: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 dosya/552 manifest.
- MI-01 W8 PR #20: `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`; exact 553 ürün manifesti blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`.
- MI-04 özgün G7 test kaynağı PR #19: `93e6c84db1a061ee914aa2c1d543620404515c0b`; özgün testler tarihsel G7, ancak rapor yalnız **current product ORG sınıfı** yüklü olduğunda 7/7 sayılır.
- G7 mevcut doğrulayıcı: PR #24 `verify_current_org_g7.py` SHA256 `da4a644f3d6f189ac6a94fc8a645acde40df6489199f6a702aedf7f87a29a691`.

## Durum ve hata teşhisi

- **Preflight/HOLD**: GitHub erişimi yok, Git commit veya kaynak SHA eşleşmiyor, eksik Python/Git/Node/npm, kirli checkout.
- **C04/HOLD**: npm frozen lock/wheelhouse indirmesi veya metadata kontrolü başarısız; staging klasörünü aynı kaynak üzerine yeniden kullanmayın, yeni ayrı `--root` ile kanıtı koruyun.
- **G7/FAIL**: Özgün 7 metot gerçek güncel ORG ile çalışırken hata verdi; logdaki hatayı düzeltmek için orijinal pinleri değiştirmeyin.
- **PGProbe**: yalnız yerel `pg_isready` kontrolüdür, korumalı PostgreSQL `non-owner RLS/COMMIT/restore`, bağımsız issuer/claim custody/effect-sink/IV değildir. Bu alanlarda H O L D korunur.
- **Rollback**: yalnız oluşturulan `C:\AIOS\TEST_RUN_20261120` çalışma dizinini, loglar ve SHA delilleri arşivlendikten sonra silebilirsiniz. Mevcut proje klasörleri, GitHub PR sahipleri, `main`, yetkiler ve canlı DB etkilenmez.

## Kanıt sınırı

Bu paket üretildiği bu turda Python stdlib **12/12 yardımcı test PASS**, Windows gerçek çalıştırması **NOT_RUN**. PC'de çalıştırılıncaya kadar özgün W8 ve güncel ORG 7 testleri hâlâ NOT_RUN. Genel ağırlıklı geliştirme HESAPLANAMADI; Core 12/16, UI 21/40, MVP 0/11, bağımsız IV 0/7; kabul delta 0.
