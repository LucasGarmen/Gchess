(() => {
'use strict';
const counter=document.getElementById('analyzer-position-counter');if(!counter)return;
const buttons=['last-move','prev-move','next-move','toggle-analysis-mode','flip-board'].map(id=>document.getElementById(id)).filter(Boolean);
let starting=true;
function update(){counter.textContent=historyIndex+' / '+SAVED_MOVES.length;}
document.addEventListener('gchess:position-changed',()=>{update();if(starting)buttons.forEach(button=>button.disabled=true);});
loadPositionUntil(0);update();buttons.forEach(button=>button.disabled=true);
requestAnimationFrame(()=>requestAnimationFrame(async()=>{
 try{if(SAVED_MOVES.length){await applyMoveWithoutSaving(SAVED_MOVES[0],true);loadPositionUntil(1);}}
 finally{starting=false;buttons.forEach(button=>button.disabled=false);updateHistoryControls();update();}
}));
})();