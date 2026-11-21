"use client";
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
type Theme='dark'|'light';
const THEME_PREFERENCE_KEY='ai-company-os:ui-theme';
const ThemeContext=createContext<{theme:Theme;toggle:()=>void}|null>(null);
export function ThemeToggle(){
 const ctx=useContext(ThemeContext);
 if(!ctx)return null;
 return <button type="button" aria-label="Açık tema" aria-pressed={ctx.theme==='light'} onClick={ctx.toggle}>Tema: {ctx.theme==='light'?'Açık':'Koyu'}</button>;
}
export default function ThemeFrame({children}:{children:ReactNode}){
 const [theme,setTheme]=useState<Theme>('dark');
 useEffect(()=>{
  try{
   const stored=window.localStorage.getItem(THEME_PREFERENCE_KEY);
   if(stored==='dark'||stored==='light')setTheme(stored);
  }catch{/* Local preference must never prevent the readonly shell from rendering. */}
 },[]);
 function toggle(){
  const next:Theme=theme==='dark'?'light':'dark';
  setTheme(next);
  try{window.localStorage.setItem(THEME_PREFERENCE_KEY,next);}catch{/* Keep the in-memory choice if storage is unavailable. */}
 }
 return <ThemeContext.Provider value={{theme,toggle}}><div className="eds-frame" data-eds-theme={theme}>{children}</div></ThemeContext.Provider>;
}
