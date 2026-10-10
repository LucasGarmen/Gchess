document.addEventListener('DOMContentLoaded',()=>{
 const log=document.getElementById('game-chat-messages');
 const stage=document.querySelector('.online-game-layout .board-player-stage');
 const color=stage?.dataset.viewerColor;
 if(!log||!['white','black'].includes(color))return;
 let latest=0,initialized=false;const bubbles=new Map(),timers=new Map();
 const closeLabel={es:'Cerrar mensaje',pt:'Fechar mensagem',en:'Close message'}[document.documentElement.lang.slice(0,2)]||'Close message';
 const position=()=>{
  let top=false,bottom=false;
  bubbles.forEach((bubble,c)=>{const upper=c!==(stage.dataset.boardOrientation||'white');bubble.dataset.edge=upper?'top':'bottom';if(!bubble.hidden){if(upper)top=true;else bottom=true;}});
  stage.classList.toggle('player-speech-top',top);stage.classList.toggle('player-speech-bottom',bottom);
  window.dispatchEvent(new Event('resize'));
 };
 const show=(c,text)=>{
  let bubble=bubbles.get(c);
  if(!bubble){bubble=document.createElement('aside');bubble.className='player-speech';bubble.dataset.playerColor=c;const content=document.createElement('p');content.setAttribute('role','status');const close=document.createElement('button');close.type='button';close.textContent='\u00d7';close.setAttribute('aria-label',closeLabel);close.addEventListener('click',()=>{bubble.hidden=true;position();});bubble.append(content,close);stage.append(bubble);bubbles.set(c,bubble);}
  bubble.querySelector('p').textContent=text;bubble.hidden=false;clearTimeout(timers.get(c));timers.set(c,setTimeout(()=>{bubble.hidden=true;position();},16000));position();
 };
 const update=()=>{
  const messages=[...log.querySelectorAll('[data-message-id]')];
  if(!initialized){if(!messages.length&&!log.querySelector('.game-chat-empty'))return;latest=Math.max(0,...messages.map(x=>Number(x.dataset.messageId)||0));initialized=true;return;}
  messages.forEach(item=>{const id=Number(item.dataset.messageId);if(id<=latest)return;latest=id;const mine=item.classList.contains('game-chat-message-mine');const c=mine?color:(color==='white'?'black':'white');show(c,item.querySelector('p')?.textContent||'');});
 };
 update();new MutationObserver(update).observe(log,{childList:true,subtree:true});
 new MutationObserver(position).observe(stage,{attributes:true,attributeFilter:['data-board-orientation']});
});
