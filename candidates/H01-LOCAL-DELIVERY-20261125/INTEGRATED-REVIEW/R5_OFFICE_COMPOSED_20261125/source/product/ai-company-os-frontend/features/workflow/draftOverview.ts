/** Presentation only: counts from an already validated draft review. */
export function draftOverview(waves:readonly (readonly string[])[], baseEdgeCount:number, addedEdgeCount:number){
 return {taskCount:waves.reduce((n,w)=>n+w.length,0),waveCount:waves.length,largestWave:waves.reduce((n,w)=>Math.max(n,w.length),0),baseEdgeCount,addedEdgeCount};
}
