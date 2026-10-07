(() => {
 'use strict';
 document.querySelectorAll('[data-weekly-deadline]').forEach(node=>{
  const date=new Date(node.dateTime);if(!Number.isNaN(date.getTime()))node.textContent=new Intl.DateTimeFormat(document.documentElement.lang,{dateStyle:'short',timeStyle:'short'}).format(date);
 });
 document.addEventListener('gchess:training-state',event=>{
  const score=document.getElementById('weekly-score'),attempts=document.getElementById('weekly-attempts');
  const mode=document.getElementById('weekly-mode');if(mode&&(event.detail.practice||!event.detail.scoring_open))mode.textContent=mode.dataset.practiceLabel;
  if(score)score.textContent=event.detail.score;if(attempts)attempts.textContent=event.detail.attempted;
 });
})();
