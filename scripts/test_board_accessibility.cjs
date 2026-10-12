const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('games/static/games/board_accessibility.js','utf8');
function boot(lang='pt'){
 const events={},docEvents={};let focus=null;
 const cells=Array.from({length:64},(_,i)=>({dataset:{coord:'abcdefgh'[i%8]+(8-Math.floor(i/8)),type:i===0?'rook':'',color:i===0?'black':''},style:{order:String(i)},attrs:{},classList:{contains:()=>false},setAttribute(k,v){this.attrs[k]=v;},closest(){return this;},focus(){focus=this;},click(){this.clicked=(this.clicked||0)+1;}}));
 const board={dataset:{},attrs:{},setAttribute(k,v){this.attrs[k]=v;},querySelectorAll:()=>cells,contains:c=>cells.includes(c),addEventListener(k,fn){events[k]=fn;}};
 const document={documentElement:{lang},readyState:'complete',getElementById:()=>board,addEventListener(k,fn){docEvents[k]=fn;}};
 vm.runInNewContext(source,{document,window:{requestAnimationFrame:fn=>fn()},MutationObserver:class{observe(){}}});
 function key(cell,key){let prevented=false;events.keydown({target:cell,key,preventDefault(){prevented=true;}});return prevented;}
 return {cells,board,key,docEvents,focus:()=>focus};
}
for(const lang of ['pt','es','en']){
 const a=boot(lang);assert.equal(a.cells.filter(c=>c.tabIndex===0).length,1);assert(a.board.attrs['aria-label']);assert(a.cells[0].attrs['aria-label'].startsWith('a8'));
 a.key(a.cells[0],'ArrowRight');assert.equal(a.focus(),a.cells[1]);assert.equal(a.cells.filter(c=>c.tabIndex===0).length,1);
 a.key(a.cells[7],'ArrowRight');assert.equal(a.focus(),a.cells[1],'Cannot wrap from the right edge');
 a.key(a.cells[0],'ArrowDown');assert.equal(a.focus(),a.cells[8]);
 a.key(a.cells[8],'Enter');a.key(a.cells[8],' ');assert.equal(a.cells[8].clicked,2);
 a.cells.forEach((cell,i)=>cell.style.order=String(63-i));a.key(a.cells[63],'ArrowRight');assert.equal(a.focus(),a.cells[62],'Arrows follow the flipped visual board');
 a.cells[0].dataset.type='queen';a.docEvents['gchess:position-changed']();assert.equal(a.cells[0].attrs.role,'button');assert(!a.cells[0].attrs['aria-label'].includes('rook'));
 assert.equal(a.key(a.cells[0],'x'),false);
}
console.log('Board keyboard: one Tab stop, arrows, edges, flip, Enter/space and translated live labels passed.');
