# T01 — İcra öncesi karar zarfı / HOLD
Kaynak: v135 §07 L164–179, v131 L3628–3638; 0148 OPS148-01..04, 0150 OPS_T01. 0150 paket hash `3388007117708dcaabcb402be0b1cf3e0802812b2acab969d2a769c352fbc447`; D3 hash `c097f5d1291e16066813b55f4259d85d6e51cd41de1785d43997f27a9a700a04`. v135 §07 T01 CODE doğrudan; T02 REPO, T03/04 DEV, T09 TEST ayrıdır. T05/T06/T07/T08 etkilerine göre ayrıca değerlendirilir; hiçbir kapı iptal edilmez. Mevcut CODE=C REPO=C DEV=B koşullu; etkin 0/3. Kullanıcı “devamet” tasarım devamı; B seçim veya imza olarak kaydedilmedi.

| Alan | Önerilen değer | Gerçek kayıt |
|---|---|---|
| H01 yön kararı | B: PRE/POST normatif bootstrap incelemesi | NULL |
| İlk scope | UI-04/05, dört dosya, sentetik snapshot-only | NULL |
| Kaynak pin | D3 exact SHA + 0150 master | SHA doğrulandı, yetki değil |
| Yetkili kişi | H01 kapsamlı ayrı CODE grant | NULL |
| Bağımsız review | gerçek doğal kişi/rol, COI, SoD, custody, ilgili kural ve PRE/POST receipt | NULL |
| Süre / revoke | tek sınırlandırılmış oturum önerisi; stop, revoke | başlangıç/expiry NULL |
| Dış kapsam | REPO/DEV/build/TEST/PROD/spend/provider/mutation yok | NO_* yürürlükte |
| Kanonik veri | 16 owner receipt / 55 field ve layout normatif kabul | 0/16, 0/55; mismatch HOLD |

**İşlem sınıfı ayrımı:** T02 ve T03/04 gerçek repo/DEV önkoşulları ayrı değerlendirilir; C01–24'ü T01 için topluca önkoşul veya muafiyet ilan etme. PRE/POST çelişkilerinde mevcut normu yalnız yetkili normatif makam değiştirebilir; önce gerçek bağımsız makam belirlenmeli. T01 verilse bile ilgili bağımsız koşullar açıkken etkin değil. NO_CODE. T06 makamı AI, H01'in ikinci hesabı veya taklit imzacı olamaz.

H01 seçimi gereken konu (0149/0150'den açık): A mevcut HOLD; B bağımsız PRE/POST inceleme yönü (öneri); C mevcut tüm ilgili koşulların gerçek kanıtından sonra dar T01. B bir yön seçimi, grant değildir. Kullanıcının önceden verdiği seçimler tekrar istenmez. Gerçek bağımsız kişi yoksa güvenli bekleme. H01 B yönü seçerse sonraki ilk adım bağımsız normatif inceleme için kapsam ve gerçek kişi/receipt doğrulaması; mevcut kaynakların salt-okunur incelemesi dışında kod/repo/DEV/TEST yok. Başarılı bağımsız kabul ve ayrı T01 ile yalnız UI-04/05 kaynak çalışma kopyası; kapsam dışı STOP. D4/D5 kaynak eksikleri ve T1 fifth table runtime/merge için ayrı açık işler.
