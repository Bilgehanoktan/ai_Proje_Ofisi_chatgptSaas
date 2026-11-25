// D0 visual-only entry. No snapshot, runtime, storage, or authority crosses the frame.
import {premiumOfficeHtml} from '../../../office/assets/premiumOfficeHtml';
import Link from 'next/link';
export const metadata = { title: 'Premium Office | AI Company OS' };
export default function PremiumOfficePage() {
  return <main style={{maxWidth:1600,margin:'0 auto',padding:'20px 16px'}}>
    <header className="topline"><div><div className="eyebrow">OFFICE-01 / PREMIUM LAB</div><h1>Premium Office Studio</h1></div><a className="action-link" href="/office">← Mevcut ofis / Phaser</a></header>
    <p className="chips"><a className="action-link" href="/office/premium/native">Native Phaser Studio · D0 ↗</a><a className="action-link" href="/office/premium/hybrid">Hybrid Phaser Studio · D0 ↗</a><Link className="action-link" href="/office/premium/unified">Birleşik ofis adayı · D0 ↗</Link></p>
    <p className="notice" role="status">D0 · Dekoratif rol şablonları; gerçek ajan, görev, konum veya yetki yok. JOIN_HOLD. Kat ve kamera durumu bağımsızdır.</p>
    <iframe title="Premium ofis görsel prototipi" srcDoc={premiumOfficeHtml} sandbox="allow-scripts" referrerPolicy="no-referrer" style={{display:'block',width:'100%',height:'85vh',minHeight:560,border:'1px solid #344154',borderRadius:12,background:'#101522'}} />
    <p className="sub">Görsel laboratuvar · gerçek geometri ve OfficeV0 bağlanmadı. Orijinal ofis ve istasyon listesi korunur.</p>
  </main>;
}
