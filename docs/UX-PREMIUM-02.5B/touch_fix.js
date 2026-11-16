// D0 nested-frame floor controls: trusted touch end selects its original button.
(()=>{let start=null;const button=e=>e.target instanceof Element?e.target.closest('button[data-floor]'):null;
 document.addEventListener('touchstart',e=>{const b=button(e);if(!b||e.touches.length!==1){start=null;return;}const t=e.touches[0];start={b,id:t.identifier,x:t.clientX,y:t.clientY};},{capture:true,passive:true});
 document.addEventListener('touchmove',e=>{if(start&&(e.touches.length!==1||Math.hypot(e.touches[0].clientX-start.x,e.touches[0].clientY-start.y)>8))start=null;},{capture:true,passive:true});
 document.addEventListener('touchcancel',()=>{start=null;},true);
 document.addEventListener('touchend',e=>{const s=start;start=null;if(!s||e.touches.length||button(e)!==s.b||s.b.disabled)return;const t=Array.from(e.changedTouches).find(t=>t.identifier===s.id);if(!t||Math.hypot(t.clientX-s.x,t.clientY-s.y)>8)return;e.preventDefault();s.b.click();},{capture:true,passive:false});
})();
