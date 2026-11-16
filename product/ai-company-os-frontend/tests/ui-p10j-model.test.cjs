const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const {draftOverview}=require(path.join(process.env.P10D_MODEL,'features/workflow/draftOverview.js'));
test('empty overview is zero',()=>assert.deepEqual(draftOverview([],0,0),{taskCount:0,waveCount:0,largestWave:0,baseEdgeCount:0,addedEdgeCount:0}));
test('counts uneven waves without equating width to runtime capacity',()=>assert.deepEqual(draftOverview([['a'],['b','c'],['d']],3,1),{taskCount:4,waveCount:3,largestWave:2,baseEdgeCount:3,addedEdgeCount:1}));
test('does not mutate frozen waves',()=>{const waves=Object.freeze([Object.freeze(['a','b'])]);assert.equal(draftOverview(waves,0,0).taskCount,2);assert.deepEqual(waves,[['a','b']]);});
