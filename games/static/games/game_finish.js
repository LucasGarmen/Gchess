(() => {
'use strict';
const notice=document.getElementById('game-finish-notice'),status=document.getElementById('game-status');if(!notice||!status)return;
const words=JSON.parse(document.getElementById('game-result-words').textContent);
const layout=notice.closest('.game-layout'),wrapper=notice.parentElement;
const board=document.getElementById('board');let dismissed=false,finishKey=null,initial=true,previouslyFinished=false;const sounded=new Set();
const reopen=document.createElement('button');reopen.type='button';reopen.className='game-finish-reopen';reopen.textContent=words.view_result;reopen.hidden=true;
const text=(id,value)=>{const element=document.getElementById(id);if(element&&element.textContent!==String(value))element.textContent=value;};
function outcome(){
 const mate=typeof isCheckmate==='function'&&typeof currentTurn!=='undefined'&&isCheckmate(currentTurn);
 let winner=window.gchessGameResult|| (typeof GAME_RESULT!=='undefined'?GAME_RESULT:null);
 if(mate)winner=currentTurn==='white'?'black':'white';
 if(!['white','black','draw'].includes(winner)&&typeof isStalemate==='function'&&typeof hasInsufficientMaterial==='function'&&(isStalemate(currentTurn)||hasInsufficientMaterial()))winner='draw';
 const viewer=typeof GAME_PLAYER_COLOR!=='undefined'&&GAME_PLAYER_COLOR?GAME_PLAYER_COLOR:typeof isComputerMode==='function'&&isComputerMode()?playerColor():null;
 const kind=winner==='draw'?'draw':viewer&&['white','black'].includes(winner)?winner===viewer?'victory':'defeat':'finished';
 return {winner,kind,mate};
}
let rewardRequested=false;
async function loadReward(attempt=0){
 const target=document.getElementById('game-finish-xp');if(!target)return;
 try{const response=await fetch(target.dataset.url,{credentials:'same-origin',headers:{Accept:'application/json'}});if(!response.ok)return;const data=await response.json();
 if(data.pending&&attempt<4){setTimeout(()=>loadReward(attempt+1),500);return;}
 if(data.earned>0){target.textContent=`+${data.earned} ${target.dataset.label}`;target.hidden=false;}
 }catch(error){/* Result and rematch remain available if progress is unavailable. */}
}
function refresh(){
 const atEnd=typeof isViewingLatestPosition!=='function'||isViewingLatestPosition();
 const finished=typeof gameOver!=='undefined'&&gameOver&&atEnd&&!(typeof analysisMode!=='undefined'&&analysisMode);
 const focus=document.querySelector('.focus-play');
 if(layout.classList.contains('game-ended-visible')!==finished)layout.classList.toggle('game-ended-visible',finished);
 if(focus&&focus.classList.contains('game-ended-visible')!==finished)focus.classList.toggle('game-ended-visible',finished);
 const host=focus?(focus.querySelector('.board-player-stage')||focus.querySelector('.focus-play-board')):layout.classList.contains('blindfold-active')?layout.querySelector('.board-area'):board?.closest('.board-player-stage')||wrapper;
 if(notice.parentElement!==host)host.prepend(notice);if(reopen.parentElement!==host)host.append(reopen);
 if(finished){
  if(!rewardRequested){rewardRequested=true;loadReward();}
  const result=outcome(),count=typeof SAVED_MOVES!=='undefined'?SAVED_MOVES.length:0;
  const key=`${count}:${result.winner}`;
  if(finishKey!==key){dismissed=false;finishKey=key;notice.dataset.outcome=result.kind;}
  text('game-finish-title',words[result.kind]);
  const winnerText=result.winner==='white'?words.white_wins:result.winner==='black'?words.black_wins:result.winner==='draw'?words.draw:status.textContent;
  text('game-finish-result',(result.mate?words.mate+' · ':'')+winnerText);
  text('game-finish-note',words[result.kind+'_note']);text('game-finish-tip',words[result.kind+'_tip']);
  text('game-finish-moves',count);
  const advice=notice.querySelector('.game-finish-advice'),analyze=notice.querySelector('.game-finish-secondary');
  if(advice)advice.hidden=count===0;if(analyze)analyze.hidden=count===0;
  const occupied=board?.querySelectorAll('.square[data-type]:not([data-type=""])').length;
  text('game-finish-captures',occupied===undefined?'—':Math.max(0,32-occupied));
  if(!initial&&!previouslyFinished&&!sounded.has(key))window.GchessExperience?.tone(result.kind);
  sounded.add(key);
 }else {dismissed=false;finishKey=null;if(typeof SAVED_MOVES!=='undefined'&&SAVED_MOVES.length===0)sounded.clear();}
 notice.hidden=!finished||dismissed;reopen.hidden=!finished||!dismissed;
 previouslyFinished=finished;initial=false;
 const undo=document.getElementById('undo-computer-move');if(undo&&finished)undo.disabled=true;
 const coach=document.getElementById('toggle-coach');if(coach)coach.disabled=finished;
 if(!layout.classList.contains('game-result-enhanced'))layout.classList.add('game-result-enhanced');
}
function dismiss(){dismissed=true;notice.hidden=true;reopen.hidden=false;reopen.focus();}
for(const id of ['game-finish-dismiss','game-finish-view-board'])document.getElementById(id)?.addEventListener('click',dismiss);
reopen.addEventListener('click',()=>{dismissed=false;refresh();document.getElementById('game-finish-dismiss')?.focus();});
document.getElementById('game-finish-again')?.addEventListener('click',()=>{resetComputerGame(false);refresh();board?.focus();});
document.getElementById('game-finish-analyze')?.addEventListener('click',()=>{window.GchessFocus?.exit();const form=document.getElementById('analyze-game-form'),button=document.getElementById('analyze-game-button');form?.requestSubmit(button||undefined);});
notice.addEventListener('click',event=>{if(event.target.closest('a'))window.GchessFocus?.exit();});
document.getElementById('game-finish-rematch')?.addEventListener('submit',event=>{window.GchessFocus?.exit();const button=event.target.querySelector('button');button.disabled=true;});
new MutationObserver(refresh).observe(status,{attributes:true,childList:true,characterData:true,subtree:true});
new MutationObserver(refresh).observe(layout,{attributes:true,attributeFilter:['class']});
for(const name of ['gchess:position-changed','gchess:focus-mode-changed'])document.addEventListener(name,refresh);
refresh();
})();
