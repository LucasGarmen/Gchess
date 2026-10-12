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
 panel.classList.add('online-chat-dock');document.body.append(panel);
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
