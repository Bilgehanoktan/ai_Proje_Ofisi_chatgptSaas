"use client";
import {createContext,useContext,useState,type ReactNode} from 'react';
type Theme='dark'|'light';
const ThemeContext=createContext<{theme:Theme;toggle:()=>void}|null>(null);
export function ThemeToggle(){
 const ctx=useContext(ThemeContext);
 if(!ctx)return null;
 return <button type="button" aria-label="Açık tema" aria-pressed={ctx.theme==='light'} onClick={ctx.toggle}>Tema: {ctx.theme==='light'?'Açık':'Koyu'}</button>;
}
export default function ThemeFrame({children}:{children:ReactNode}){
 const [theme,setTheme]=useState<Theme>('dark');
 return <ThemeContext.Provider value={{theme,toggle:()=>setTheme(t=>t==='dark'?'light':'dark')}}><div className="eds-frame" data-eds-theme={theme}>{children}</div></ThemeContext.Provider>;
}
