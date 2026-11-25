import Link from 'next/link';
import SharedSnapshotPanel from '../../../../features/data/SharedSnapshotPanel';
import UnifiedOfficePreview from '../../../../office/components/UnifiedOfficePreview';
export const metadata={title:'Unified Office Candidate | AI Company OS'};
export default function UnifiedOfficePage(){
 return <main style={{maxWidth:1600,margin:'0 auto',padding:'20px 16px'}}>
  <header className="topline"><div><div className="eyebrow">U1 / CONTROLLED INTEGRATION</div><h1>Birleşik ofis adayı</h1></div><Link className="action-link" href="/office/premium">Premium laboratuvar</Link></header>
  <SharedSnapshotPanel office/>
  <UnifiedOfficePreview/>
 </main>;
}
