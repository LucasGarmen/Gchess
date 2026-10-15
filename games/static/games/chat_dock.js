(() => {
 'use strict';
 const viewport=window.visualViewport;
 function keyboardInset(){
  const inset=viewport?Math.max(0,window.innerHeight-viewport.height-viewport.offsetTop):0;
  document.documentElement.style.setProperty('--chat-keyboard-inset',inset+'px');
  document.documentElement.style.setProperty('--chat-visible-height',(viewport?.height||window.innerHeight)+'px');
 }
 window.addEventListener('resize',keyboardInset);
 viewport?.addEventListener('resize',keyboardInset);viewport?.addEventListener('scroll',keyboardInset);
 keyboardInset();
 window.GchessChatDock={bind(dock,handle){
  let drag=null,position=null;
  const desktop=()=>window.innerWidth>900&&!dock.closest('.focus-play');
  function place(x,y){
   const rect=dock.getBoundingClientRect();
   position={x:Math.max(8,Math.min(x,window.innerWidth-rect.width-8)),y:Math.max(8,Math.min(y,window.innerHeight-rect.height-8))};
   for(const [name,value] of Object.entries({left:position.x+'px',top:position.y+'px',right:'auto',bottom:'auto'}))dock.style.setProperty(name,value,'important');
  }
  function resize(){
   if(!desktop()){for(const name of ['left','top','right','bottom'])dock.style.removeProperty(name);}
   else if(position)place(position.x,position.y);
  }
  handle.classList.add('chat-drag-handle');
  handle.addEventListener('pointerdown',event=>{
   if(!desktop()||event.button!==0||event.isPrimary===false)return;
   event.preventDefault();
   const rect=dock.getBoundingClientRect();
   drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};
   handle.setPointerCapture(event.pointerId);handle.classList.add('is-dragging');
  });
  handle.addEventListener('pointermove',event=>{
   if(!drag||event.pointerId!==drag.id)return;
   event.preventDefault();dock.classList.add('is-detached');place(drag.left+event.clientX-drag.x,drag.top+event.clientY-drag.y);
  });
  const end=event=>{if(drag?.id!==event.pointerId)return;drag=null;handle.classList.remove('is-dragging');if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);};
  for(const name of ['pointerup','pointercancel','lostpointercapture'])handle.addEventListener(name,end);
  window.addEventListener('resize',resize);document.addEventListener('gchess:focus-mode-changed',resize);
 }};
})();
