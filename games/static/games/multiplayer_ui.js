document.addEventListener('DOMContentLoaded',()=>{
 const layout=document.querySelector('.online-game-layout'),board=document.getElementById('board');
 if(!layout||!board)return;
 const lang=document.documentElement.lang.slice(0,2);
 const words={es:['Jugadas','Movimiento preparado','Cancelar'],pt:['Lances','Lance preparado','Cancelar'],en:['Moves','Premove queued','Cancel']}[lang]||['Moves','Premove queued','Cancel'];
 const moves=layout.querySelector('.online-moves-panel');
 if(moves){moves.querySelector('summary').textContent=words[0]+' · PGN';moves.open=innerWidth>900;}
 const toolbar=layout.querySelector('.board-toolbar'),mobile=window.matchMedia('(max-width:900px)');
 const tools=document.createElement('details'),summary=document.createElement('summary'),toolBody=document.createElement('div');
 tools.className='online-board-tools';toolBody.className='online-board-tools-body';summary.textContent={es:'Controles',pt:'Controles',en:'Controls'}[lang]||'Controls';tools.append(summary,toolBody);
 const transfers=[];
 if(toolbar){
  [...toolbar.children].filter(el=>el.matches('button,input')&&!el.hidden&&el.id!=='mobile-nav-toggle'&&!el.classList.contains('focus-play-toggle')).forEach(el=>{const marker=document.createComment('online control');el.before(marker);transfers.push([el,marker]);});
  toolbar.append(tools);
 }
 function syncTools(){
  if(document.body.classList.contains('focus-playing'))return;
  tools.hidden=!mobile.matches;
  transfers.forEach(([el,marker])=>{if(mobile.matches)toolBody.append(el);else marker.after(el);});
 }
 mobile.addEventListener('change',syncTools);document.addEventListener('gchess:focus-mode-changed',syncTools);syncTools();
 tools.addEventListener('toggle',()=>window.dispatchEvent(new Event('resize')));
 const back=document.querySelector('.online-game-page-back');if(back)layout.querySelector('.online-side')?.append(back);
 const status=document.createElement('div'),text=document.createElement('span'),cancel=document.createElement('button');
 status.className='online-premove-status';status.hidden=true;text.setAttribute('role','status');cancel.type='button';cancel.textContent=words[2];status.append(text,cancel);
 layout.querySelector('.board-area')?.append(status);
 function update(){
  const origin=board.querySelector('.queued-move-origin'),target=board.querySelector('.queued-move-target');
  status.hidden=!origin||!target;
  if(!status.hidden)text.textContent=words[1]+': '+origin.dataset.coord+' → '+target.dataset.coord;
 }
 cancel.addEventListener('click',()=>{if(typeof clearQueuedMove==='function')clearQueuedMove();if(typeof clearSelection==='function')clearSelection();update();});
 new MutationObserver(update).observe(board,{subtree:true,attributes:true,attributeFilter:['class'],childList:true});update();
});
