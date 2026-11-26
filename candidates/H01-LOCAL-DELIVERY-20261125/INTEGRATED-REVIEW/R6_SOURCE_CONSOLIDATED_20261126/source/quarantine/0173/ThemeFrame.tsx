"use client";
import {useState,type ReactNode} from 'react';
import './eds.css';
export default function ThemeFrame({children}:{children:ReactNode}){
 const [theme,setTheme]=useState<'dark'|'light'>('dark');
 return <div className="eds-frame" data-eds-theme={theme}>
 <div className="eds-toolbar"><span>D0 · STATIC_ONLY</span><button type="button" aria-pressed={theme==='light'} onClick={()=>setTheme(t=>t==='dark'?'light':'dark')}>Açık tema</button></div>{children}</div>;
}
