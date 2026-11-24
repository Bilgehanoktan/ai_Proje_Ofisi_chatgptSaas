# Önerilen 0162-D — aday kaynak ve otorite uzlaştırması
| Sıra | İş | Önkoşul | Çıktı / STOP |
|---|---|---|---|
| 1 | W8 statik diff ve katalog incelemesi | 0162-C manifest + R8 pin | Bağımsız reviewer kimliği ve scope; yetki eksikse HOLD |
| 2 | W2 R06 alan sahipleri | 20 crosswalk / 55 alan | canonical mapping + owner receipts; aksi HOLD |
| 3 | W3/W4 terminal/UNKNOWN | R01/R03/R02; W2 owner | physical readback/stop authority/fence binding; 4/5/7 HOLD |
| 4 | W7 settlement | outcome evidence semantiği | reservation/economic event otoritatif kimlik; no posting |
| 5 | W6 IV | ayrı makam | custody, algorithm, trusted time, revocation, release CAS; no signing |
| 6 | W1 UI-04/05 | dar scope + PRE/T01 | kontrollü 4 dosya patch ve POST inceleme; browser test ayrı |

Kritik yol: NO_CODE uzlaştırması + gerçek bağımsız makam/PRE + T01 → izinli entegrasyon → POST; TEST/DEV/CI ayrı. UI bağımsız, W6 custody paralel. H01 C yönü tekrar sorulmaz; eksik bağımsız kararlar AI tarafından üretilmez.
