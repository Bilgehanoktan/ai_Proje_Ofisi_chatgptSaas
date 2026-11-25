const assert=require('node:assert/strict');
const {createTrafficSearch}=require(process.argv[2]);
const start=[[0,0],[1,0],[1,1],[0,1]],goal=[[1,0],[1,1],[0,1],[0,0]];
const walkable=c=>c[0]>=0&&c[0]<3&&c[1]>=0&&c[1]<3;
function solve(p){for(let i=0;i<20001;i++){const r=p.advance(1);if(r.status!=='SEARCHING')return r;}throw Error('SEARCH_LIMIT');}
const tests=[
 ['search result cannot terminate or corrupt internal search',()=>{const p=createTrafficSearch(start,goal,walkable);const r=p.advance(1);assert.equal(r.status,'SEARCHING');r.status='SOLVED';r.expanded=-999;r.steps.push({actor:0,to:[99,99]});assert.deepEqual(solve(p),solve(createTrafficSearch(start,goal,walkable)));}],
 ['solved steps and nested coordinates are isolated',()=>{const p=createTrafficSearch(start,goal,walkable);const r=solve(p);const expected=JSON.parse(JSON.stringify(r));assert.equal(r.status,'SOLVED');assert(r.steps.length>0);r.steps[0].to[0]=99;r.steps[0].actor=99;r.steps.splice(1);r.status='LIMIT';r.expanded=-1;assert.deepEqual(p.advance(),expected);}],
 ['invalid and limit terminal snapshots remain stable',()=>{for(const p of [createTrafficSearch([[0,0]],[[1,0]],walkable),createTrafficSearch(start,goal,walkable,new Set(),1)]){const r=p.advance();const expected=JSON.parse(JSON.stringify(r));assert(['NO_ROUTE','LIMIT'].includes(r.status));r.status='SEARCHING';r.steps.push({actor:0,to:[99,99]});r.expanded=-1;assert.deepEqual(p.advance(),expected);}}]
];
let pass=0;for(const [name,fn] of tests){try{fn();console.log('PASS',name);pass++;}catch(e){console.log('FAIL',name, e.message);}}console.log(`${pass}/${tests.length} PASS`);process.exitCode=pass===tests.length?0:1;
