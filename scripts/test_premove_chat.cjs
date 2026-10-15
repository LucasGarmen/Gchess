const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const name of ['board.js','board.min.js']){
 const source=fs.readFileSync('games/static/games/'+name,'utf8');
 const snippet=name==='board.js'?source.match(/document.addEventListener\('pointerdown', function \(event\) \{[\s\S]*?\n\}, true\);/)[0]:source.match(/document.addEventListener\("pointerdown",function\(e\)\{[^}]+\},!0\)/)[0];
 let handler,cleared=0,markers=0;const square={},chat={},toolbar={};
 vm.runInNewContext(snippet,{document:{addEventListener(type,fn){handler=fn;}},board:{contains:x=>x===square},clearQueuedMove(){cleared++;},clearRightClickMarker(){markers++;}});
 handler({target:chat,button:0});handler({target:toolbar,button:0});assert.equal(cleared,0,'Typing or using controls preserves premove');
 handler({target:square,button:0});assert.equal(cleared,1,'A board click still cancels the premove');
 handler({target:square,button:2});assert.equal(cleared,2);assert.equal(markers,3,'Right-click marking is preserved');
}
console.log('Premove survives chat/toolbar input; board cancellation preserved in source and shipped JS.');
