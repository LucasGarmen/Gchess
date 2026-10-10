(function(){
 function portrait(){
  var avatars=document.querySelector('[data-coach-player]');
  if(!avatars)return;
  var svg=Array.from(avatars.querySelectorAll('svg')).find(function(el){return !el.closest('[hidden]');});
  if(!svg)return;
  var image='url("data:image/svg+xml,'+encodeURIComponent(new XMLSerializer().serializeToString(svg))+'")';
  document.documentElement.style.setProperty('--coach-chat-portrait',image);
 }
 document.addEventListener('DOMContentLoaded',function(){portrait();var avatars=document.querySelector('[data-coach-player]');if(avatars)new MutationObserver(portrait).observe(avatars,{attributes:true,subtree:true,attributeFilter:['hidden']});});
})();
