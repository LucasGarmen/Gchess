document.addEventListener('DOMContentLoaded',()=>{
 const dock=document.getElementById('game-chat-panel'),layout=document.querySelector('.online-game-layout');if(!dock||!layout)return;
 const lang=document.documentElement.lang.slice(0,2),w={es:['Solicitar deshacer','El rival pide deshacer la última jugada.','Solicitud enviada. Esperando al rival.','Aceptar','Rechazar','No se pudo completar. La partida puede haber cambiado.'],pt:['Pedir para desfazer','O adversário pede para desfazer o último lance.','Pedido enviado. Aguardando o adversário.','Aceitar','Recusar','Não foi possível concluir. A partida pode ter mudado.'],en:['Request takeback','Your opponent asks to undo the last move.','Request sent. Waiting for your opponent.','Accept','Decline','Could not complete. The game may have changed.']}[lang]||['Request takeback','Your opponent asks to undo the last move.','Request sent. Waiting for your opponent.','Accept','Decline','Could not complete. The game may have changed.'];
 const request=document.createElement('button');request.type='button';request.id='request-takeback';request.className='takeback-request';request.textContent=w[0];
 const actions=layout.querySelector('.game-actions')||layout.querySelector('.pgn-panel');actions?.append(request);
 const panel=document.createElement('div');panel.className='takeback-panel';panel.hidden=true;panel.setAttribute('role','status');const text=document.createElement('p'),buttons=document.createElement('div');
 const accept=document.createElement('button'),reject=document.createElement('button');accept.type=reject.type='button';accept.textContent=w[3];reject.textContent=w[4];buttons.append(accept,reject);panel.append(text,buttons);dock.prepend(panel);
 let busy=false,offer=null;
 function render(data){offer=data;request.disabled=busy||!data.can_request;panel.hidden=!data.pending&&!data.rejected;text.textContent=data.rejected?({es:'El rival rechazó la solicitud.',pt:'O adversário recusou o pedido.',en:'Your opponent declined the request.'}[lang]||'Your opponent declined the request.'):w[data.mine?2:1];buttons.hidden=data.mine||!data.pending;}
 async function call(action){if(busy)return;busy=true;request.disabled=true;accept.disabled=reject.disabled=true;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
  try{const options={cache:'no-store',signal:controller.signal};if(action){Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':getCSRFToken()},body:JSON.stringify({action,move_id:action==='request'?SAVED_MOVES.at(-1)?.id:offer?.move_id})});}
   const response=await fetch(`/games/${GAME_ID}/takeback/`,options);if(!response.ok)throw new Error();const data=await response.json();render(data);
   if(data.state){clearQueuedMove();clearSelection();await applyGameStateFromServer(data.state);}else if(data.move_count<SAVED_MOVES.length){clearQueuedMove();clearSelection();await syncMovesFromServer();}
  }catch(_){if(action){panel.hidden=false;text.textContent=w[5];buttons.hidden=true;}}
  finally{clearTimeout(timeout);busy=false;accept.disabled=reject.disabled=false;request.disabled=!offer?.can_request;}
 }
 request.addEventListener('click',()=>call('request'));accept.addEventListener('click',()=>call('accept'));reject.addEventListener('click',()=>call('reject'));
 call();const timer=setInterval(()=>{if(!document.hidden)call();},4000);window.addEventListener('pagehide',()=>clearInterval(timer));
});
