const assert=require('node:assert/strict');const {pairEscape,depthAt,cameraViewport}=require(process.argv[2]);let n=0;const test=(name,f)=>{f();console.log('PASS',name);n++};
const key=c=>c.join(',');const rect=(w,h)=>([x,y])=>Number.isInteger(x)&&Number.isInteger(y)&&x>=0&&y>=0&&x<w&&y<h;
function check(start,goals,steps,walk,fixed){assert(steps);const a=start.map(c=>[...c]);for(const {actor,to} of steps){assert(walk(to));assert(!fixed.has(key(to)));assert.notEqual(key(to),key(a[1-actor]));assert.equal(Math.abs(to[0]-a[actor][0])+Math.abs(to[1]-a[actor][1]),1);a[actor]=to;}assert.deepEqual(a,goals);}
test('opposite adjacent destinations resolved via side cell',()=>{const s=[[1,0],[2,0]],g=[[2,0],[1,0]],w=rect(4,2),f=new Set();check(s,g,pairEscape(s,g,w,f),w,f);});
test('single-width corridor cannot swap',()=>assert.equal(pairEscape([[1,0],[2,0]],[[2,0],[1,0]],rect(4,1),new Set()),null));
test('fixed third actor is never crossed',()=>{const s=[[1,0],[2,0]],g=[[2,0],[1,0]],w=rect(4,3),f=new Set(['1,1']);check(s,g,pairEscape(s,g,w,f),w,f);});
test('same goal rejected',()=>assert.equal(pairEscape([[0,0],[1,0]],[[2,0],[2,0]],rect(4,2),new Set()),null));
test('invalid start rejected',()=>assert.equal(pairEscape([[-1,0],[1,0]],[[2,0],[0,0]],rect(4,2),new Set()),null));
test('bounded state search',()=>assert.equal(pairEscape([[1,0],[2,0]],[[2,0],[1,0]],rect(4,2),new Set(),1),null));
test('deterministic escape',()=>{const args=[[[1,0],[2,0]],[[2,0],[1,0]],rect(4,2),new Set()];assert.deepEqual(pairEscape(...args),pairEscape(...args));});
test('depth orders front foot after back foot',()=>assert(depthAt(101,1,'furniture')>depthAt(100,1100,'actor')));
test('depth tie stable actor above furniture',()=>assert(depthAt(100,10,'actor')>depthAt(100,10,'furniture')));
test('zoom viewport center retained',()=>assert.deepEqual(cameraViewport(0,0,1100,720,2),{x:275,y:180,w:550,h:360}));
console.log(`${n}/${n} PASS`);
