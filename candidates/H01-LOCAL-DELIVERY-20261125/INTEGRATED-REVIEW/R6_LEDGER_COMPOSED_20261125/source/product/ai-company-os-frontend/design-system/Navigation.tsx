"use client";
import {useEffect,useId,useRef,useState} from 'react';
import Link from 'next/link';
import {groupNavigation,type NavItem} from './navigationModel';
import styles from './Navigation.module.css';
export type {NavItem} from './navigationModel';
const isMobile=()=>window.matchMedia('(max-width:680px)').matches;
export default function Navigation({items,current,onNavigate}:{items:readonly NavItem[];current:string;onNavigate:(name:string)=>void}){
 const [query,setQuery]=useState(''),[compact,setCompact]=useState(false),[mobileOpen,setMobileOpen]=useState(false);
 const search=useRef<HTMLInputElement>(null),focusPending=useRef(false),mobileToggle=useRef<HTMLButtonElement>(null);
 const inputId=useId(),navId=useId(),panelId=useId();
 const grouped=groupNavigation(items,query),count=grouped.reduce((n,g)=>n+g.items.length,0);
 useEffect(()=>{if(!compact&&focusPending.current){focusPending.current=false;search.current?.focus();}},[compact,mobileOpen]);
 useEffect(()=>{
  const shortcut=(e:KeyboardEvent)=>{
   if(e.defaultPrevented||e.isComposing||e.repeat||!(e.ctrlKey||e.metaKey)||e.altKey||e.shiftKey||e.key.toLowerCase()!=='k')return;
   const target=e.target;
   if(target instanceof HTMLElement&&target!==search.current&&(target.isContentEditable||target.closest('input,textarea,select,[contenteditable="true"]')))return;
   e.preventDefault();
   if(isMobile()&&!mobileOpen){focusPending.current=true;setCompact(false);setMobileOpen(true);}else if(compact){focusPending.current=true;setCompact(false);}else search.current?.focus();
  };
  window.addEventListener('keydown',shortcut);return()=>window.removeEventListener('keydown',shortcut);
 },[compact,mobileOpen]);
 function toggleCompact(){setQuery('');setCompact(v=>!v);}
 function clearSearch(){setQuery('');search.current?.focus();}
 function closeMobile(restoreFocus:boolean){setMobileOpen(false);setQuery('');if(restoreFocus)mobileToggle.current?.focus();}
 function toggleMobile(){if(mobileOpen)closeMobile(true);else{setCompact(false);setMobileOpen(true);}}
 function select(name:string){onNavigate(name);if(isMobile())closeMobile(false);document.getElementById('main-content')?.focus();}
 return <div className={styles.root} data-compact={compact?'true':'false'} data-mobile-open={mobileOpen?'true':'false'} onKeyDown={e=>{if(e.key==='Escape'&&!e.defaultPrevented&&isMobile()&&mobileOpen){e.preventDefault();closeMobile(true);}}}>
  <button ref={mobileToggle} type="button" className={styles.mobileToggle} aria-label="Menü" aria-expanded={mobileOpen} aria-controls={panelId} onClick={toggleMobile}><span aria-hidden="true">☰</span><span>Menü</span><span className={styles.mobileCurrent}>{current}</span><span aria-hidden="true">{mobileOpen?'▴':'▾'}</span></button>
  <div id={panelId} className={styles.panel}>
  <div className={styles.tools}><button type="button" className={styles.toggle} onClick={toggleCompact} aria-pressed={compact} aria-controls={navId} aria-label={compact?'Geniş menüye geç':'Kompakt menüye geç'} title={compact?'Genişlet':'Daralt'}><span aria-hidden="true">{compact?'»':'«'}</span>{!compact&&<span>Daralt</span>}</button>{!compact&&<kbd className={styles.shortcut}>Ctrl / ⌘ K</kbd>}</div>
  {!compact&&<div className={styles.search}><label htmlFor={inputId}>Menü ara</label><div className={styles.searchRow}><input id={inputId} ref={search} type="search" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Escape'&&query){e.preventDefault();clearSearch();}}} placeholder="Görev, finans, ofis…" autoComplete="off"/><button type="button" disabled={!query} onClick={clearSearch} aria-label="Aramayı temizle" title="Temizle">×</button></div><small role="status">{count}/{items.length} menü</small></div>}
  <nav id={navId} aria-label="Ana navigasyon" className={`eds-nav ${styles.nav}`}>{grouped.map(group=><section key={group.label} className={styles.group} aria-label={group.label}><h3 className={styles.groupLabel}>{group.label}</h3>{group.items.map(([name,icon])=>name==='Sanal Ofis'?<Link key={name} href="/office" className={`nav-link ${styles.item}`} aria-current={current===name?'page':undefined} aria-label={name} title={name}><span className="navicon" aria-hidden="true">{icon}</span><span className={styles.itemLabel}>{name}</span></Link>:<button type="button" key={name} className={styles.item} aria-pressed={current===name} aria-label={name} title={name} onClick={()=>select(name)}><span className="navicon" aria-hidden="true">{icon}</span><span className={styles.itemLabel}>{name}</span></button>)}</section>)}</nav>
  {!count&&<p className={styles.empty}>Eşleşen menü yok. Aramayı temizleyebilirsiniz.</p>}
  <span style={{position:'absolute',width:1,height:1,padding:0,margin:-1,overflow:'hidden',clip:'rect(0,0,0,0)',whiteSpace:'nowrap',border:0}} role="status" aria-live="polite">Görüntülenen bölüm: {current}</span>
  </div>
 </div>;
}
