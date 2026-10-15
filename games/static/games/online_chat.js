document.addEventListener('DOMContentLoaded', () => {
 'use strict';
 const form=document.getElementById('game-chat-form'),input=document.getElementById('game-chat-input'),panel=document.getElementById('game-chat-panel');
 if(!form||!input||!panel)return;
 const lang=document.documentElement.lang.slice(0,2);
 const words={es:['No se pudo enviar. Tu mensaje está guardado; intentá de nuevo.','Sesión vencida. Volvé a entrar para enviar.','Enviando…'],pt:['Não foi possível enviar. Sua mensagem foi preservada; tente novamente.','Sessão expirada. Entre novamente para enviar.','Enviando…'],en:['Could not send. Your message is preserved; try again.','Session expired. Sign in again to send.','Sending…']}[lang]||['Could not send. Your message is preserved; try again.','Session expired. Sign in again to send.','Sending…'];
 const status=document.createElement('p');status.className='online-chat-status';status.setAttribute('role','status');status.hidden=true;form.before(status);
 const button=form.querySelector('button[type="submit"]');const label=button?.textContent;let pending=false;
 const toggle=document.getElementById('game-chat-toggle'),toolbar=document.querySelector('.online-game-layout .board-toolbar');
 if(toolbar&&toggle)toolbar.append(toggle);
 panel.classList.add('online-chat-dock');
 const side=document.querySelector('.online-game-layout .online-side');
 (side||document.body).append(panel);
 const handle=document.createElement('div');handle.className='online-chat-handle';handle.textContent={es:'Chat con el rival ⠿',pt:'Chat com o adversário ⠿',en:'Opponent chat ⠿'}[lang]||'Opponent chat ⠿';panel.prepend(handle);window.GchessChatDock?.bind(panel,handle);
 // The composer is ready on entry, without opening the mobile keyboard.
 panel.hidden=false;
 if(typeof gameChatOpen!=='undefined')gameChatOpen=true;
 if(toggle)toggle.hidden=true;
 const close=document.getElementById('game-chat-close');if(close)close.hidden=true;

 const emojiPanel=document.getElementById('game-chat-emoji-panel'),emojiButton=document.getElementById('game-chat-emoji-toggle');
 function positionEmojis(){
  if(!emojiPanel||!emojiButton)return;
  if(window.innerWidth>900){emojiPanel.style.removeProperty('top');emojiPanel.style.removeProperty('left');return;}
  if(emojiPanel.hidden)return;
  const viewport=window.visualViewport,edge=(viewport?.offsetTop||0)+8;
  const rect=emojiButton.getBoundingClientRect(),popup=emojiPanel.getBoundingClientRect();
  emojiPanel.style.setProperty('top',Math.max(edge,Math.min(rect.top,input.getBoundingClientRect().top)-popup.height-8)+'px','important');
  emojiPanel.style.setProperty('left',Math.max(8,Math.min(rect.right-popup.width,window.innerWidth-popup.width-8))+'px','important');
 }
 if(emojiPanel)new MutationObserver(positionEmojis).observe(emojiPanel,{attributes:true,attributeFilter:['hidden']});
 window.addEventListener('resize',positionEmojis);window.visualViewport?.addEventListener('resize',positionEmojis);window.visualViewport?.addEventListener('scroll',positionEmojis);
 const log=document.getElementById('game-chat-messages');
 if(log){const history=document.createElement('details'),summary=document.createElement('summary');history.className='online-chat-history';summary.textContent={es:'Conversación',pt:'Conversa',en:'Conversation'}[lang]||'Conversation';history.append(summary,log);panel.insertBefore(history,form);}

 // Capture replaces the legacy socket fire-and-forget submit. HTTP confirms
 // persistence, while sockets and polling still deliver incoming messages.
 form.addEventListener('submit',async event=>{
  event.preventDefault();event.stopImmediatePropagation();
  const text=input.value.trim();if(!text||pending)return;
  const game=typeof GAME_ID!=='undefined'?GAME_ID:null;if(!game)return;
  pending=true;status.hidden=true;form.setAttribute('aria-busy','true');if(button){button.disabled=true;button.textContent=words[2];}
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
  try{
   const csrf=document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith('csrftoken='))?.slice(10)||'';
   const response=await fetch(`/games/${game}/chat/?mark_read=1`,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify({text}),signal:controller.signal});
   if(response.redirected||response.status===401||response.status===403)throw new Error(words[1]);
   if(!response.ok)throw new Error(words[0]);
   const data=await response.json();
   if(typeof renderGameChat==='function')renderGameChat(data);
   if(input.value.trim()===text)input.value='';
  }catch(error){status.textContent=error.message===words[1]?words[1]:words[0];status.hidden=false;}
  finally{clearTimeout(timeout);pending=false;form.setAttribute('aria-busy','false');if(button){button.disabled=false;button.textContent=label;}}
 },true);
});
