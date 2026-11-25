const assert=require('node:assert/strict'),{createTrafficSearch}=require(process.argv[2]);let count=0;
const test=(name,f)=>{f();console.log('PASS',name);count++;};
const grid=(w,h)=>c=>c[0]>=0&&c[0]<w&&c[1]>=0&&c[1]<h;
const run=(s,g,w,f=new Set(),limit=20000,budget=96)=>{const p=createTrafficSearch(s,g,w,f,limit);let r;do{r=p.advance(budget)}while(r.status==='SEARCHING');return r;};
function replay(s,g,w,r,f=new Set()){assert.equal(r.status,'SOLVED');const a=s.map(c=>c.slice());for(const {actor,to} of r.steps){assert(w(to));assert(!f.has(to.join(',')));assert.equal(Math.abs(a[actor][0]-to[0])+Math.abs(a[actor][1]-to[1]),1);assert(!a.some((c,i)=>i!==actor&&c.join(',')===to.join(',')));a[actor]=to;}assert.deepEqual(a,g);}
const s3=[[0,0],[1,0],[2,0]],g3=[[1,0],[2,0],[0,0]],s4=[[0,0],[1,0],[1,1],[0,1]],g4=[[1,0],[1,1],[0,1],[0,0]];
test('three actor cyclic deadlock',()=>replay(s3,g3,grid(3,2),run(s3,g3,grid(3,2))));
test('four actor cyclic deadlock',()=>replay(s4,g4,grid(3,3),run(s4,g4,grid(3,3))));
test('fully occupied cycle cannot swap',()=>assert.equal(run(s4,g4,grid(2,2)).status,'NO_ROUTE'));
test('fixed obstacle never traversed',()=>{const f=new Set(['2,1']);replay(s3,g3,grid(3,2),run(s3,g3,grid(3,2),f),f);});
test('search is incremental with bounded expansions',()=>{const p=createTrafficSearch(s4,g4,grid(3,3));let prev=0,r;do{r=p.advance(1);assert(r.expanded-prev<=1);prev=r.expanded;}while(r.status==='SEARCHING');replay(s4,g4,grid(3,3),r);});
test('hard search state limit',()=>assert.equal(run(s4,g4,grid(3,3),new Set(),1).status,'LIMIT'));
test('deterministic across slice sizes',()=>assert.deepEqual(run(s4,g4,grid(3,3),new Set(),20000,1),run(s4,g4,grid(3,3))));
test('duplicate starts/goals fail closed',()=>{assert.equal(run([[0,0],[0,0]],[[0,0],[1,0]],grid(3,3)).status,'NO_ROUTE');assert.equal(run(s3,[[1,0],[1,0],[0,0]],grid(3,3)).status,'NO_ROUTE');});
test('invalid budget rejected',()=>assert.throws(()=>createTrafficSearch(s3,g3,grid(3,3)).advance(257),/BUDGET/));
test('invalid limits and unsupported actor count',()=>{assert.equal(run(s3,g3,grid(3,3),new Set(),20001).status,'NO_ROUTE');assert.equal(run([[0,0]],[[0,1]],grid(3,3)).status,'NO_ROUTE');});
test('already at goal is empty plan',()=>assert.deepEqual(run(s3,s3,grid(3,3)).steps,[]));
test('inputs copied to avoid mutation',()=>{const s=s3.map(c=>c.slice()),g=g3.map(c=>c.slice()),p=createTrafficSearch(s,g,grid(3,2));s[0][0]=99;g[0][0]=99;let r;do{r=p.advance()}while(r.status==='SEARCHING');replay(s3,g3,grid(3,2),r);});
console.log(`${count}/${count} PASS`);
