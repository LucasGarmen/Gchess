document.addEventListener('DOMContentLoaded',()=>{
 const stage=document.querySelector('.online-game-layout .board-player-stage'),turn=document.getElementById('turn-indicator');
 const color=stage?.dataset.viewerColor;if(!stage||!turn||!['white','black'].includes(color))return;
 const lang=document.documentElement.lang.slice(0,2),words={es:['Tu turno','Adversario','Conectado','Sin conexión','Comprobando conexión'],pt:['Sua vez','Adversário','Conectado','Desconectado','Verificando conexão'],en:['Your turn','Opponent','Connected','Disconnected','Checking connection']}[lang]||['Your turn','Opponent','Connected','Disconnected','Checking connection'];
 const statusBar=document.querySelector('.online-match-status')||document.querySelector('.online-game-layout .board-toolbar');
 statusBar?.append(turn);turn.setAttribute('role','status');turn.setAttribute('aria-live','polite');
 const badges=new Map();stage.querySelectorAll('[data-player-color]').forEach(avatar=>{const badge=document.createElement('span');badge.className='player-connection';badge.dataset.state='unknown';badge.title=words[4];badge.setAttribute('aria-label',words[4]);avatar.append(badge);badges.set(avatar.dataset.playerColor,badge);});
 const connection=document.createElement('span');connection.className='opponent-connection';connection.dataset.state='unknown';connection.setAttribute('role','status');
 const connectionLabel=state=>{connection.dataset.state=state;connection.textContent=words[state==='online'?2:state==='offline'?3:4];};
 connectionLabel('unknown');statusBar?.append(connection);
 const originalTitle=document.title||'Gchess';let titleTimer=null;
 function titleTurn(mine){
  if(mine&&titleTimer===null){let showTurn=true;document.title=words[0];titleTimer=setInterval(()=>{showTurn=!showTurn;document.title=showTurn?words[0]:'Gchess';},1200);}
  else if(!mine&&titleTimer!==null){clearInterval(titleTimer);titleTimer=null;document.title=originalTitle;}
 }
 let lastCount=null;
 function updateTurn(){
  const live=typeof isViewingLatestPosition==='function'&&isViewingLatestPosition()&&!analysisMode&&!gameOver;
  turn.classList.toggle('online-turn-mine',live&&currentTurn===color);turn.classList.toggle('online-turn-rival',live&&currentTurn!==color);
  stage.querySelectorAll('[data-player-color]').forEach(avatar=>avatar.classList.toggle('player-to-move',live&&avatar.dataset.playerColor===currentTurn));
  titleTurn(live&&currentTurn===color);
  if(!live)return;
  const count=SAVED_MOVES.length,mine=currentTurn===color,label=words[mine?0:1];
  if(turn.textContent!==label)turn.textContent=label;
  if(lastCount!==null&&count>lastCount&&mine)window.GchessExperience?.tone('ui_open');
  lastCount=count;
 }
 new MutationObserver(updateTurn).observe(turn,{childList:true,characterData:true,subtree:true});updateTurn();
 let busy=false,stopped=false,offline=false;
 async function presence(){
  if(busy||stopped||offline)return;busy=true;
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),7000);
  try{
   const response=await fetch(`/games/${GAME_ID}/presence/`,{method:'POST',headers:{'X-CSRFToken':getCSRFToken()},signal:controller.signal,cache:'no-store'});
   if(response.redirected||[401,403,404].includes(response.status)){stopped=true;throw new Error('unavailable');}
   if(!response.ok)throw new Error('network');const data=await response.json();
   // A response started before network loss must not restore a stale green status.
   if(offline)return;
   badges.forEach((badge,c)=>{const connected=data[c]===true;badge.dataset.state=connected?'online':'offline';badge.title=words[connected?2:3];badge.setAttribute('aria-label',badge.title);if(c!==color)connectionLabel(connected?'online':'offline');});
  }catch(_){connectionLabel('unknown');badges.forEach(badge=>{badge.dataset.state='unknown';badge.title=words[4];badge.setAttribute('aria-label',words[4]);});}
  finally{clearTimeout(timeout);busy=false;}
 }
 window.addEventListener('offline',()=>{offline=true;connectionLabel('unknown');badges.forEach(badge=>{badge.dataset.state='unknown';badge.title=words[4];badge.setAttribute('aria-label',words[4]);});});
 window.addEventListener('online',()=>{offline=false;presence();});
 presence();const timer=setInterval(presence,8000);window.addEventListener('pagehide',()=>{stopped=true;clearInterval(timer);titleTurn(false);});
});
