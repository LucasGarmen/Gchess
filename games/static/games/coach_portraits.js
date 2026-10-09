(function(){
 'use strict';
 function update(){
  var coach=document.querySelector('[data-coach-player]'),human=document.querySelector('[data-human-player]'),level=document.getElementById('computer-elo');
  if(!coach||!human||!level)return;
  coach.dataset.playerColor=human.dataset.playerColor==='black'?'white':'black';
  var value=level.value,selected=coach.querySelector('[data-coach-level="'+value+'"]');
  if(!selected)value='500';
  coach.querySelectorAll('[data-coach-level]').forEach(function(portrait){portrait.hidden=portrait.dataset.coachLevel!==value;});
  coach.title='Coach · '+level.options[level.selectedIndex].textContent;
 }
 window.GchessCoachPortraits={update:update};
 document.addEventListener('DOMContentLoaded',function(){update();var level=document.getElementById('computer-elo');if(level)level.addEventListener('change',update);});
})();
