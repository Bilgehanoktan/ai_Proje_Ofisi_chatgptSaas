# EDS teknik katalog — 0167A

Tasarım eşlemesi; aşağıdaki ürün dosyaları değiştirilmedi.

| R11 yolu (frontend altında) | Önerilen değişiklik | Faz |
|---|---|---|
| `app/globals.css` | Merkezi tokenlar, tema, grid, odak, motion | EDS-02 |
| `app/layout.tsx` | Tema sağlayıcı ve kök semantik kabuk; server/client sınırı korunur | EDS-03 |
| `features/ceo-dashboard/Dashboard.tsx` | Mevcut state, 13 menü, rol ve kat seçimi korunarak yeni kabuk | EDS-03/04 |
| `components/dashboard/MetricsStrip.tsx` | Null KPI → —; kaynak tazeliği ayrı | EDS-04 |
| `components/dashboard/SnapshotStrip.tsx` | Tenant/world/seq/layout/as_of/epoch/source görünür | EDS-04 |
| `components/dashboard/OfficePanel.tsx` | Kat seçimi, liste, sahne, geometri fallback; JOIN_HOLD korunur | EDS-05 |
| `components/dashboard/AgentDetail.tsx` | Rol/instance ayrımı; mevcut yedi sekme korunur | EDS-05 |
| `components/dashboard/OperationPanel.tsx` | Kadro, olay, karar ve seçili bağlam görünümü | EDS-04 |
| `features/core-review/CorePreview.tsx` | Kanonik plan projeksiyonu; görsel katman dispatch etmez | EDS-07 |
| `office/scenes/OfficeScene.tsx` | Phaser sahnesi; görsel rota/marker ve reduced motion korunur | EDS-05 |
| `office/engine/geometry.ts` | Kanonik olmayan geometri; davranış değişikliği yok | EDS-05 |
| `features/uiCatalog.json` | 13 menü / 4 rol sabit; veri biçimi değişmez | EDS-03 |
| `fixtures/office.snapshot.json` | Null KPI, dört rezerv istasyon, boş ikinci kat ve otorite bayrakları | EDS-04/05 |
| `package.json` | Next/React/Phaser pinleri korunur; yeni bağımlılıklar review sonrası | EDS-01 |

## Arıza teşhisi / bakım
- Tema/kontrast: EDS_TOKENS.json ve globals.css.
- Yanlış KPI: MetricsStrip, snapshot kaynağı; null asla 0’a dönüştürülmez.
- Kat/istasyon: OfficePanel, OfficeScene, layout pinleri; mismatch → JOIN_HOLD.
- Rol durumu: Dashboard selection, AgentDetail; şablon instance değildir.
- Görev grafı: CorePreview, planProjection; kanonik backend planı tek otorite.
- Geri dönüş: önizleme kaldırılabilir; ürün kaynağı değişmedi. İleride commit düzeyinde revert; pin/manifest yeniden denetlenir.
