(function(){
 'use strict';
 var input=document.getElementById('pgn-file'),text=document.getElementById('pgn'),status=document.getElementById('pgn-file-status'),generation=0;
 if(!input||!text||!status)return;
 input.addEventListener('change',async function(){
  var file=input.files[0],request=++generation;if(!file)return;
  status.hidden=false;
  if(!/\.(pgn|txt)$/i.test(file.name)||file.size>80*1024){status.textContent=status.dataset.error;input.value='';return;}
  try{var contents=await file.text();if(request!==generation)return;text.value=contents;status.textContent=status.dataset.loaded+file.name;text.focus();}
  catch(_){if(request===generation)status.textContent=status.dataset.error;}
  input.value='';
 });
})();
