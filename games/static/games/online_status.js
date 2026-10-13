document.addEventListener('DOMContentLoaded',()=>{
 const stage=document.querySelector('.online-game-layout .board-player-stage'),turn=document.getElementById('turn-indicator');
 const color=stage?.dataset.viewerColor;if(!stage||!turn||!['white','black'].includes(color))return;
 const lang=document.documentElement.lang.slice(0,2),words={es:['Tu turno','Turno del rival','Conectado','Sin conexión','Comprobando conexión'],pt:['Sua vez','Vez do adversário','Conectado','Desconectado','Verificando conexão'],en:['Your turn','Opponent’s turn','Connected','Disconnected','Checking connection']}[lang]||['Your turn','Opponent’s turn','Connected','Disconnected','Checking connection'];
 document.querySelector('.online-game-layout .board-toolbar')?.append(turn);turn.setAttribute('role','status');turn.setAttribute('aria-live','polite');
 const badges=new Map();stage.querySelectorAll('[data-player-color]').forEach(avatar=>{const badge=document.createElement('span');badge.className='player-connection';badge.dataset.state='unknown';badge.title=words[4];badge.setAttribute('aria-label',words[4]);avatar.append(badge);badges.set(avatar.dataset.playerColor,badge);});
 const connection=document.createElement('span');connection.className='opponent-connection';connection.dataset.state='unknown';connection.setAttribute('role','status');
 const rivalName={es:'Rival',pt:'Adversário',en:'Opponent'}[lang]||'Opponent';
 const connectionLabel=state=>{connection.dataset.state=state;connection.textContent=rivalName+': '+words[state==='online'?2:state==='offline'?3:4];};
 connectionLabel('unknown');document.querySelector('.online-game-layout .board-toolbar')?.append(connection);
 let lastCount=null;
 function updateTurn(){
  const live=typeof isViewingLatestPosition==='function'&&isViewingLatestPosition()&&!analysisMode&&!gameOver;
  turn.classList.toggle('online-turn-mine',live&&currentTurn===color);turn.classList.toggle('online-turn-rival',live&&currentTurn!==color);
  stage.querySelectorAll('[data-player-color]').forEach(avatar=>avatar.classList.toggle('player-to-move',live&&avatar.dataset.playerColor===currentTurn));
  if(!live)return;
  const count=SAVED_MOVES.length,mine=currentTurn===color,label=words[mine?0:1];
  if(turn.textContent!==label)turn.textContent=label;
  if(lastCount!==null&&count>lastCount&&mine)window.GchessExperience?.tone('ui_open');
  lastCount=count;
 }
 new MutationObserver(updateTurn).observe(turn,{childList:true,characterData:true,subtree:true});updateTurn();
 let busy=false,stopped=false;
 async function presence(){
  if(busy||stopped)return;busy=true;
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),7000);
  try{
   const response=await fetch(`/games/${GAME_ID}/presence/`,{method:'POST',headers:{'X-CSRFToken':getCSRFToken()},signal:controller.signal,cache:'no-store'});
   if(response.redirected||[401,403,404].includes(response.status)){stopped=true;throw new Error('unavailable');}
   if(!response.ok)throw new Error('network');const data=await response.json();
   badges.forEach((badge,c)=>{const connected=data[c]===true;badge.dataset.state=connected?'online':'offline';badge.title=words[connected?2:3];badge.setAttribute('aria-label',badge.title);if(c!==color)connectionLabel(connected?'online':'offline');});
  }catch(_){connectionLabel('unknown');badges.forEach(badge=>{badge.dataset.state='unknown';badge.title=words[4];badge.setAttribute('aria-label',words[4]);});}
  finally{clearTimeout(timeout);busy=false;}
 }
 presence();const timer=setInterval(presence,8000);window.addEventListener('pagehide',()=>{stopped=true;clearInterval(timer);});
});
