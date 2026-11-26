"use client";
import type {SectionOption} from './sectionModel';
import styles from './SectionSwitcher.module.css';
export default function SectionSwitcher<T extends string>({label,options,current,onChange}:{label:string;options:readonly SectionOption<T>[];current:T;onChange:(id:T)=>void}){
 return <section className={styles.root} aria-label={label}>
  <div className={styles.options} role="group" aria-label={label+' seçimi'}>{options.map(option=><button type="button" key={option.id} aria-pressed={current===option.id} onClick={()=>onChange(option.id)}><strong>{option.label}</strong><small>{option.description}</small></button>)}</div>
  <p className={styles.note}>Bölüm değişince yerel seçimler, okumalar ve kaydedilmemiş taslaklar sıfırlanır. Canlı işlem başlatılmaz.</p>
 </section>;
}
