document.addEventListener('DOMContentLoaded',()=>{
 const log=document.getElementById('game-chat-messages');
 const stage=document.querySelector('.online-game-layout .board-player-stage');
 const color=stage?.dataset.viewerColor;
 if(!log||!['white','black'].includes(color))return;
 const side=document.querySelector('.online-game-layout .online-side');
 const topSlot=document.createElement('div'),bottomSlot=document.createElement('div');topSlot.className=bottomSlot.className='online-speech-slot';
 if(side){side.prepend(topSlot);side.append(bottomSlot);}
 let latest=0,initialized=false;const bubbles=new Map(),timers=new Map();
 const closeLabel={es:'Cerrar mensaje',pt:'Fechar mensagem',en:'Close message'}[document.documentElement.lang.slice(0,2)]||'Close message';
 const position=()=>{
  let top=false,bottom=false;const desktop=innerWidth>900&&!stage.closest('.focus-play');
  const chatDock=document.getElementById('game-chat-panel');chatDock?.style.setProperty('--player-speech-offset','0px');
  const previous=stage.classList.contains('player-speech-top')+' '+stage.classList.contains('player-speech-bottom');
  bubbles.forEach((bubble,c)=>{const upper=c!==(stage.dataset.boardOrientation||'white');bubble.dataset.edge=upper?'top':'bottom';if(desktop&&side){
    const slot=upper?topSlot:bottomSlot;if(bubble.parentElement!==slot)slot.append(bubble);bubble.removeAttribute('style');bubble.dataset.speaker=stage.querySelector('[data-player-color="'+c+'"]')?.title||'';
   }else if(bubble.parentElement!==stage)stage.append(bubble);
   if(!bubble.hidden){
   if(desktop&&!side){
    const avatar=stage.querySelector('[data-player-color="'+c+'"]');
    if(avatar){const anchor=avatar.getBoundingClientRect(),width=Math.min(270,innerWidth-24);
     bubble.style.width=width+'px';const height=bubble.getBoundingClientRect().height;
     const x=Math.max(12,Math.min(anchor.right+8,innerWidth-width-12));let y=Math.max(12,Math.min(anchor.top,innerHeight-height-12));
     const dock=document.getElementById('game-chat-panel');if(dock&&!dock.hidden){const box=dock.getBoundingClientRect();if(x<box.right&&x+width>box.left&&y<box.bottom&&y+height>box.top){if(c===color){dock.style.setProperty('--player-speech-offset',Math.min(Math.max(0,box.bottom-y+8),Math.max(0,box.top-12))+'px');}else{y=Math.max(12,box.top-height-8);}}}
     bubble.style.left=x+'px';bubble.style.top=y+'px';}
   }else if(!desktop){bubble.removeAttribute('style');if(upper)top=true;else bottom=true;}
  }});
  stage.classList.toggle('player-speech-top',top);stage.classList.toggle('player-speech-bottom',bottom);
  if(previous!==top+' '+bottom)window.dispatchEvent(new Event('resize'));
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
 window.addEventListener('resize',position);document.addEventListener('scroll',position,{capture:true,passive:true});document.addEventListener('gchess:focus-mode-changed',position);
 new MutationObserver(position).observe(stage,{attributes:true,attributeFilter:['data-board-orientation']});
});
