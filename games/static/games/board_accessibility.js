(() => {
'use strict';
function setup(){
 const board=document.getElementById('board');if(!board||board.dataset.keyboardReady)return;
 board.dataset.keyboardReady='yes';
 const lang=document.documentElement.lang.slice(0,2);
 const words={pt:{board:'Tabuleiro. Use as setas para navegar e Enter ou espaço para escolher uma peça e seu destino.',empty:'vazia',white:'brancas',black:'pretas',pawn:'peão',horse:'cavalo',knight:'cavalo',bishop:'bispo',rook:'torre',queen:'rainha',king:'rei'},es:{board:'Tablero. Usá las flechas para navegar y Enter o espacio para elegir una pieza y su destino.',empty:'vacía',white:'blancas',black:'negras',pawn:'peón',horse:'caballo',knight:'caballo',bishop:'alfil',rook:'torre',queen:'dama',king:'rey'},en:{board:'Board. Use arrow keys to navigate and Enter or space to select a piece and its destination.',empty:'empty',white:'white',black:'black',pawn:'pawn',horse:'knight',knight:'knight',bishop:'bishop',rook:'rook',queen:'queen',king:'king'}}[lang]||{board:'Chess board',empty:'empty'};
 board.setAttribute('role','group');board.setAttribute('aria-label',words.board);
 let selectedCoord=null;
 const squares=()=>Array.from(board.querySelectorAll('.square[data-coord]'));
 function sync(){const cells=squares();if(!cells.length)return;if(!cells.some(c=>c.dataset.coord===selectedCoord))selectedCoord=cells[0].dataset.coord;
  for(const cell of cells){cell.tabIndex=cell.dataset.coord===selectedCoord?0:-1;cell.setAttribute('role','button');cell.setAttribute('aria-label',cell.dataset.coord+' · '+(cell.dataset.type?(words[cell.dataset.color]||cell.dataset.color)+' '+(words[cell.dataset.type]||cell.dataset.type):words.empty));cell.setAttribute('aria-pressed',String(cell.classList.contains('selected')));}
 }
 board.addEventListener('focusin',event=>{const cell=event.target.closest('.square[data-coord]');if(cell&&board.contains(cell)){selectedCoord=cell.dataset.coord;sync();}});
 board.addEventListener('keydown',event=>{
  const cell=event.target.closest('.square[data-coord]');if(!cell||!board.contains(cell))return;
  if(event.key==='Enter'||event.key===' '){event.preventDefault();cell.click();sync();return;}
  const delta={ArrowLeft:-1,ArrowRight:1,ArrowUp:-8,ArrowDown:8}[event.key];if(!delta)return;
  event.preventDefault();const cells=squares().sort((a,b)=>(Number(a.style.order)||0)-(Number(b.style.order)||0));const index=cells.indexOf(cell);
  if((event.key==='ArrowLeft'&&index%8===0)||(event.key==='ArrowRight'&&index%8===7))return;
  const next=cells[index+delta];if(next){selectedCoord=next.dataset.coord;sync();next.focus();}
 });
 document.addEventListener('gchess:position-changed',sync);
 let queued=false;
 const schedule=()=>{if(queued)return;queued=true;(window.requestAnimationFrame||setTimeout)(()=>{queued=false;sync();});};
 new MutationObserver(schedule).observe(board,{childList:true,subtree:true,attributes:true,attributeFilter:['data-type','data-color','class']});sync();
}
document.addEventListener('DOMContentLoaded',setup);if(document.readyState!=='loading')setup();
})();
