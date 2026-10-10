const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
for(const file of ['board.js','board.min.js']){
 const source=fs.readFileSync('games/static/games/'+file,'utf8');
 const snippet=source.slice(source.indexOf('function pieceMotionSurface('),source.indexOf('async function playMove('));
 for(const mode of ['normal','overlay','native']){
  const children=[],surface={appendChild(piece){children.push(piece);}};
  const body={appendChild(){assert.equal(mode,'normal');}},classes=new Set();
  let finish;const animation=new Promise(resolve=>finish=resolve);
  const clone={style:{},classList:{add(){}},animate(frames){assert.match(frames[1].transform,/100/);return {finished:animation};},remove(){this.removed=true;}};
  const piece={animate(){},cloneNode(){return clone;},getBoundingClientRect(){return {left:10,top:20,width:47,height:47};}};
  const from={firstElementChild:piece,closest(){return mode==='overlay'?surface:null;},getBoundingClientRect(){return {left:10,top:20};},classList:{add(c){classes.add(c);},remove(c){classes.delete(c);}}};
  const to={getBoundingClientRect(){return {left:110,top:120};}};
  const context={document:{body,fullscreenElement:mode==='native'?surface:null},Promise};vm.createContext(context);vm.runInContext(snippet,context);
  const pending=context.animateMove(from,to);
  assert.ok(classes.has('drag-origin'));
  if(mode!=='normal')assert.equal(children[0],clone,'animated piece must be inside fullscreen surface');
  finish();await pending;assert.equal(clone.removed,true);assert.equal(classes.size,0);
 }
}
console.log('Fullscreen motion verified for source and shipped JS: normal, overlay and native fullscreen; cleanup after animation.');
})().catch(error=>{console.error(error);process.exit(1);});
