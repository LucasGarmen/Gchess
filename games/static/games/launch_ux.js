document.addEventListener('DOMContentLoaded',()=>{
 const words=JSON.parse(document.getElementById('launch-ux-texts')?.textContent||'{}');
 const dialog=document.getElementById('feedback-dialog'),open=document.getElementById('feedback-open'),form=document.getElementById('feedback-form');
 const close=document.getElementById('feedback-close'),status=document.getElementById('feedback-status'),send=document.getElementById('feedback-send');
 open?.addEventListener('click',()=>{dialog.showModal();document.getElementById('feedback-message').focus();});
 close?.addEventListener('click',()=>dialog.close());dialog?.addEventListener('close',()=>open?.focus());
 let pending=false;
 form?.addEventListener('submit',async event=>{
  event.preventDefault();if(pending||!form.reportValidity())return;
  pending=true;send.disabled=true;status.textContent=words.sending;form.setAttribute('aria-busy','true');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
  try{
   const response=await fetch(form.action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({category:form.elements.category.value,message:form.elements.message.value,page:location.pathname}),signal:controller.signal});
   if(response.status===429){status.textContent=words.rate_limit;return;}if(!response.ok)throw new Error('send');const data=await response.json();if(!data.saved)throw new Error('save');
   form.elements.message.value='';status.textContent=words.thanks;
  }catch(_){status.textContent=words.error;}
  finally{clearTimeout(timer);pending=false;send.disabled=false;form.setAttribute('aria-busy','false');}
 });
 const log=document.getElementById('trainer-chat-log'),chatForm=document.getElementById('trainer-chat-form');
 if(log&&chatForm){
  const waiting=document.createElement('p');waiting.className='launch-waiting';waiting.setAttribute('role','status');waiting.textContent=words.thinking;chatForm.before(waiting);
  const sync=()=>{waiting.hidden=log.getAttribute('aria-busy')!=='true';};sync();new MutationObserver(sync).observe(log,{attributes:true,attributeFilter:['aria-busy']});
 }
 const turn=document.getElementById('turn-indicator'),board=document.getElementById('board');
 if(turn&&board){const sync=()=>{const busy=typeof botRequestLocked==='function'&&botRequestLocked();turn.classList.toggle('engine-working',busy);board.setAttribute('aria-busy',String(busy));};sync();new MutationObserver(sync).observe(turn,{childList:true,characterData:true,subtree:true});}
});
