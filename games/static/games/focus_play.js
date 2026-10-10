document.addEventListener('DOMContentLoaded', () => {
 const board = document.getElementById('board');
 const layout = document.querySelector('.home-computer-layout, .online-game-layout');
 const toolbar = layout?.querySelector('.board-toolbar');
 if (!board || !toolbar) return;
 const lang=document.documentElement.lang.slice(0,2);
 const words={es:['Pantalla completa','Salir de pantalla completa'],pt:['Tela cheia','Sair da tela cheia'],en:['Fullscreen','Exit fullscreen']}[lang]||['Fullscreen','Exit fullscreen'];
 const button=document.createElement('button'); button.type='button'; button.className='focus-play-toggle'; button.title=words[0]; button.setAttribute('aria-label',words[0]); button.textContent='\u26f6'; toolbar.append(button);
 let overlay=null, moved=[], priorFocus=null;
 const move=(element,target)=>{if(!element)return; const mark=document.createComment('focus-play');element.before(mark);moved.push([element,mark]);target.append(element);};
 const size=()=>{if(!overlay)return; const mobile=innerWidth<=900; const availableWidth=innerWidth-(mobile?16:340);const speech=document.querySelector('.focus-play .board-player-stage');const extra=(speech?.classList.contains('player-speech-top')?44:0)+(speech?.classList.contains('player-speech-bottom')?44:0);const availableHeight=innerHeight-(mobile?264:190)-extra;const n=Math.floor(Math.max(120,Math.min(availableWidth,availableHeight)));overlay.style.setProperty('--square-size',n/8+'px');overlay.style.setProperty('--mobile-board-size',n+'px');overlay.style.setProperty('--mobile-square-size',n/8+'px');overlay.style.setProperty('--focus-board-size',n+'px');};
 const exit=()=>{if(!overlay)return; moved.reverse().forEach(([element,mark])=>{mark.replaceWith(element);});moved=[];overlay.remove();overlay=null;document.body.classList.remove('focus-playing');if(document.fullscreenElement)document.exitFullscreen?.().catch(()=>{});window.dispatchEvent(new Event('resize'));priorFocus?.focus();};
 const enter=()=>{
  if(overlay)return; priorFocus=document.activeElement;
  overlay=document.createElement('section');overlay.className='focus-play';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label',words[0]);
  const close=document.createElement('button');close.type='button';close.className='focus-play-exit';close.textContent='\u00d7';close.title=words[1];close.setAttribute('aria-label',words[1]);close.addEventListener('click',exit);
  const play=document.createElement('div');play.className='focus-play-board';const chat=document.createElement('div');chat.className='focus-play-chat';overlay.append(close,play,chat);document.body.append(overlay);document.body.classList.add('focus-playing');
  move(board.closest('.board-player-stage')||board,play);
  const coach=document.querySelector('.coach-chat-dock');
  if(coach)move(coach,chat);else{const panel=document.getElementById('game-chat-panel');if(panel?.hidden)document.getElementById('game-chat-toggle')?.click();move(panel,chat);}
  move(document.getElementById('turn-indicator'),play);move(document.querySelector('.game-clock'),play);
  size();close.focus();overlay.requestFullscreen?.().catch(()=>{});
 };
 button.addEventListener('click',enter);
 document.addEventListener('keydown',e=>{if(!overlay)return;if(e.key==='Escape'){e.preventDefault();exit();}if(e.key==='Tab'){const focusable=[...overlay.querySelectorAll('button,input,a,textarea,summary')].filter(x=>!x.disabled&&x.getClientRects().length);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}});
 document.addEventListener('fullscreenchange',()=>{if(overlay&&!document.fullscreenElement&&overlay.dataset.native==='yes')exit();else if(overlay&&document.fullscreenElement)overlay.dataset.native='yes';size();});
 addEventListener('resize',size);window.visualViewport?.addEventListener('resize',size);
});
