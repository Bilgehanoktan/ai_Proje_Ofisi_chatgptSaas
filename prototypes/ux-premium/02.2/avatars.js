/* UX-PREMIUM-02.2: original, decorative, non-authoritative SVG character rig. */
const cast=[
 {id:'orch',name:'Orchestrator',role:'Koordinasyon',skin:'#d49a73',shade:'#a96b4f',hair:'#292633',jacket:'#34496b',light:'#647c9e',shirt:'#e2e8ef',pants:'#263449',x:200,y:105,seat:[187,95]},
 {id:'research',name:'Research',role:'Araştırma',skin:'#a96f50',shade:'#79462f',hair:'#292024',jacket:'#27796e',light:'#64b4a0',shirt:'#e0d9c7',pants:'#293c43',x:65,y:363,seat:[57,336]},
 {id:'engineer',name:'Engineer',role:'Mühendislik',skin:'#efc49c',shade:'#b98666',hair:'#674433',jacket:'#735aa0',light:'#aa92d5',shirt:'#eee7de',pants:'#323449',x:190,y:365,seat:[181,336]},
 {id:'qa',name:'QA',role:'Kalite',skin:'#c88d65',shade:'#945c43',hair:'#342c27',jacket:'#98613e',light:'#d29b64',shirt:'#e6e4dc',pants:'#343e4b',x:385,y:415,seat:[340,388]}
];
let chosen=cast[0].id,pose='standing';
const ink='#252c39';
function character(a,p){const sit=p==='seated',hip=sit?-24:-31,shoulder=sit?-50:-59,head=shoulder-15;return `<g stroke="${ink}" stroke-width="1.1" stroke-linejoin="round" stroke-linecap="round">
 <ellipse cx="1" cy="2" rx="16" ry="5" fill="#17202e" opacity=".28" stroke="none"/>
 <path d="M-9 ${hip} L-2 ${hip+1} L${sit?7:-3} -13 L${sit?9:-4} -2 L-12 -2 L${sit?-9:-12} -17 Z" fill="${a.pants}"/><path d="M1 ${hip} L10 ${hip} L${sit?17:12} -13 L${sit?19:13} -2 L5 -2 L${sit?7:2} -16 Z" fill="${a.pants}"/>
 <path d="M-12 -4 Q-4 -6 1 -1 L1 2 L-15 2 Q-17 0 -12 -4 M5 -4 Q13 -6 17 -1 L17 2 L3 2 Q1 0 5 -4" fill="#202733"/>
 <path d="M-13 ${shoulder+3} Q0 ${shoulder-6} 13 ${shoulder+3} L11 ${hip} Q0 ${hip+5} -11 ${hip} Z" fill="${a.jacket}"/>
 <path d="M-5 ${shoulder} L0 ${shoulder+19} L7 ${shoulder} L3 ${shoulder-3} L-3 ${shoulder-3} Z" fill="${a.shirt}" stroke="none"/><path d="M-13 ${shoulder+4} L-7 ${shoulder+1} L-3 ${shoulder+16} M13 ${shoulder+4} L8 ${shoulder+1} L3 ${shoulder+16}" fill="none" stroke="${a.light}" stroke-width="2"/>
 <path d="M-12 ${shoulder+5} Q-20 ${shoulder+15} -17 ${shoulder+24} L${sit?-3:-12} ${sit?shoulder+26:hip+1}" stroke="${a.jacket}" stroke-width="8" fill="none"/><path d="M13 ${shoulder+5} Q21 ${shoulder+14} 17 ${shoulder+24} L${sit?25:13} ${sit?shoulder+22:hip+1}" stroke="${a.light}" stroke-width="7" fill="none"/>
 <circle cx="${sit?-3:-12}" cy="${sit?shoulder+26:hip+1}" r="3.5" fill="${a.skin}"/><circle cx="${sit?25:13}" cy="${sit?shoulder+22:hip+1}" r="3.5" fill="${a.skin}"/>
 <path d="M-5 ${head+11} L-5 ${shoulder} Q0 ${shoulder+4} 5 ${shoulder} L5 ${head+11}" fill="${a.shade}"/>
 <path d="M-12 ${head-4} Q-11 ${head-16} 0 ${head-16} Q13 ${head-15} 13 ${head-2} L10 ${head+8} Q4 ${head+15} -3 ${head+12} L-10 ${head+6} Z" fill="${a.skin}"/>
 <path d="M-12 ${head+2} Q-19 ${head-13} -7 ${head-18} Q5 ${head-23} 13 ${head-13} L15 ${head-5} L7 ${head-8} L2 ${head-13} L-7 ${head-6} L-10 ${head+3} Z" fill="${a.hair}"/>
 ${a.id==='research'?`<path d="M-13 ${head-9} Q-20 ${head+3} -14 ${head+15} L-8 ${head+10}" fill="${a.hair}"/>`:''}
 <ellipse cx="-4" cy="${head-1}" rx="1.2" ry="1.6" fill="${ink}" stroke="none"/><ellipse cx="6" cy="${head-1}" rx="1.2" ry="1.6" fill="${ink}" stroke="none"/>
 <path d="M2 ${head} L4 ${head+4} L1 ${head+5} M-2 ${head+8} Q2 ${head+10} 6 ${head+7}" fill="none" stroke="${a.shade}"/>
 ${a.id==='engineer'?`<g fill="none" stroke="#34465b"><rect x="-8" y="${head-4}" width="8" height="6" rx="2"/><rect x="2" y="${head-4}" width="8" height="6" rx="2"/><path d="M0 ${head-1} H2"/></g>`:''}
 <rect x="5" y="${shoulder+10}" width="5" height="3" rx="1" fill="#e8e4dd" stroke="none"/>
 </g>`;}
function avatarLayer(){if(floor!==1)return;const layer=cast.map(a=>{const p=a.id===chosen?pose:'standing',xy=p==='seated'?a.seat:[a.x,a.y],pos=P(...xy);return `<g data-avatar="${a.id}" data-pose="${p}" role="button" tabindex="0" aria-label="${a.name} karakteri" transform="translate(${pos.join(' ')}) scale(.65)">${a.id===chosen?'<ellipse cy="2" rx="21" ry="8" fill="none" stroke="#e4cbff" stroke-width="2"/>':''}${character(a,p)}</g>`}).join('');scene.insertAdjacentHTML('beforeend',`<g id="avatarLayer">${layer}</g>`);}
const originalDraw=draw;draw=function(){originalDraw();avatarLayer()};
const originalPanel=panel;panel=function(){originalPanel();renderCast()};
const castPanel=document.createElement('div');castPanel.id='castPanel';castPanel.className='cast-panel';castPanel.setAttribute('aria-label','Karakter tasarım laboratuvarı');document.querySelector('main').append(castPanel);
function renderCast(){const a=cast.find(c=>c.id===chosen);castPanel.innerHTML=`<div class="bar"><div><div class="over">CHARACTER LAB / 02.2</div><h2>Çekirdek ekip · dekoratif karakterler</h2><small>Rol şablonları; gerçek çalışan, atama veya faaliyet değildir.</small></div><div class="controls"><button data-pose-choice="standing" aria-pressed="${pose==='standing'}">Ayakta</button><button data-pose-choice="seated" aria-pressed="${pose==='seated'}">Oturur</button></div></div><div class="cast-grid">${cast.map(c=>`<button class="cast-card" data-cast="${c.id}" aria-pressed="${c.id===chosen}"><svg viewBox="-48 -106 96 116" aria-hidden="true">${character(c,c.id===chosen?pose:'standing')}</svg><strong>${c.name}</strong><small>${c.role}</small></button>`).join('')}</div><p class="cast-note" aria-live="polite">${a.name} · ${pose==='seated'?'oturur':'ayakta'} poz önizlemesi · ${floor===1?'Kat 01 dekor sahnesi':'Kat 02 pasif; karakter gösterilmez.'} · D0 / HOLD</p>`;}
function changeCharacter(id,p,focusSelector){if(!cast.some(a=>a.id===id)||!['standing','seated'].includes(p))return;chosen=id;pose=p;draw();renderCast();if(focusSelector)document.querySelector(focusSelector)?.focus();}
castPanel.addEventListener('click',e=>{const b=e.target.closest('[data-cast],[data-pose-choice]');if(!b)return;if(b.dataset.cast)changeCharacter(b.dataset.cast,pose,`[data-cast="${b.dataset.cast}"]`);else changeCharacter(chosen,b.dataset.poseChoice,`[data-pose-choice="${b.dataset.poseChoice}"]`);});
scene.addEventListener('click',e=>{const b=e.target.closest('[data-avatar]');if(b&&floor===1)changeCharacter(b.dataset.avatar,pose,`[data-avatar="${b.dataset.avatar}"]`);});
scene.addEventListener('keydown',e=>{if(e.target.dataset.avatar&&['Enter',' '].includes(e.key)){e.preventDefault();changeCharacter(e.target.dataset.avatar,pose,`[data-avatar="${e.target.dataset.avatar}"]`);}});
draw();renderCast();
