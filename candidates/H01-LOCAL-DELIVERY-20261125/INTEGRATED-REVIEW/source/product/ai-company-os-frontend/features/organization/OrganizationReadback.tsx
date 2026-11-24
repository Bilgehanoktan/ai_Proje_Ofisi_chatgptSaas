'use client';
import {useProjectionRead} from '../data/useProjectionRead';
/** Separate historical panel; never joins role templates to runtime identity. */
export default function OrganizationReadback(){
 const {state,data,read,reset}=useProjectionRead('organization');
 return <section className="panel" aria-label="Kalıcı organizasyon kayıtları">
  <div className="bar"><div><h3>Kalıcı organizasyon kayıtları</h3><small>Sentetik tarihsel okuma · gerçek görev ataması değil</small></div><span className="pill">HOLD</span></div>
  <button type="button" onClick={()=>void read()} disabled={state.phase==='loading'}>Organizasyonu oku</button> <button type="button" onClick={reset}>Temizle</button>
  {state.phase==='loading'&&<p role="status">Okunuyor…</p>}
  {state.phase==='hold'&&<p role="status">Organizasyon bağlantısı doğrulanamadı · HOLD</p>}
  {state.phase==='idle'&&<p role="status">Kalıcı kayıt henüz okunmadı.</p>}
  {data&&<><p role="status">Tarihsel revizyon {data.sequence} · {data.units.filter(u=>u.kind==='department').length} departman · {data.positions.length} pozisyon</p>
   <small>Revizyon: {data.revision}</small><div className="sectiongrid">{data.units.map(u=><article className="item" key={u.id}><h3>{u.id}</h3><small>{u.kind} · üst birim: {u.parent??'—'}</small></article>)}</div>
   <table><caption>Organizasyon pozisyonları · doluluk kaydı, aktif ajan değil</caption><thead><tr><th>Pozisyon</th><th>Birim</th><th>Rol</th><th>Yönetici</th><th>Doluluk</th></tr></thead><tbody>{data.positions.map(p=><tr key={p.id}><td>{p.id}</td><td>{p.unit}</td><td>{p.role}</td><td>{p.reports_to??'—'}</td><td>{p.occupied?'Dolu':'Boş'}</td></tr>)}</tbody></table></>}
 </section>;
}
