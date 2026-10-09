(() => {
'use strict';
const notice=document.getElementById('game-finish-notice'),status=document.getElementById('game-status');if(!notice||!status)return;
const layout=notice.closest('.game-layout'),wrapper=notice.parentElement;

function refresh(){
 const finished=typeof gameOver!=='undefined'&&gameOver&&!(typeof analysisMode!=='undefined'&&analysisMode);
 notice.hidden=!finished;layout.classList.toggle('game-ended-visible',finished);
 const host=layout.classList.contains('blindfold-active')?layout.querySelector('.board-area'):wrapper;
 if(notice.parentElement!==host)host.prepend(notice);
 const mate=finished&&typeof isCheckmate==='function'&&typeof currentTurn!=='undefined'&&isCheckmate(currentTurn);
 const heading=notice.querySelector?.('strong');if(heading)heading.textContent=mate?notice.dataset.mate:notice.dataset.title;
 document.getElementById('game-finish-result').textContent=status.hidden?'':status.textContent;
 const undo=document.getElementById('undo-computer-move');if(undo&&finished)undo.disabled=true;
 const coach=document.getElementById('toggle-coach');if(coach)coach.disabled=finished;
}
new MutationObserver(refresh).observe(status,{attributes:true,childList:true,characterData:true,subtree:true});
new MutationObserver(refresh).observe(layout,{attributes:true,attributeFilter:['class']});
document.addEventListener('gchess:position-changed',refresh);
refresh();
})();