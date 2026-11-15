"use client";
import Link from 'next/link';
export type NavItem=readonly [name:string,icon:string];
export default function Navigation({items,current,onNavigate}:{items:readonly NavItem[];current:string;onNavigate:(name:string)=>void}){
 return <nav aria-label="Ana navigasyon" className="eds-nav">{items.map(([name,icon])=>name==='Sanal Ofis'?<Link key={name} href="/office" className="nav-link" aria-current={current===name?'page':undefined}><span className="navicon" aria-hidden="true">{icon}</span>{name}</Link>:<button type="button" key={name} aria-pressed={current===name} onClick={()=>onNavigate(name)}><span className="navicon" aria-hidden="true">{icon}</span>{name}</button>)}</nav>;
}
