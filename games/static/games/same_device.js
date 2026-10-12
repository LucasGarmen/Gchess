(()=>{'use strict';const words=JSON.parse(document.getElementById('same-device-words').textContent);const rotate=document.getElementById('local-auto-flip');
function save(){window.GchessSameDevice.save(SAVED_MOVES);if(rotate.checked&&isViewingLatestPosition()&&!gameOver){boardOrientation=currentTurn;updateBoardOrientation();}}
function restart(ask=true){if(SAVED_MOVES.length&&ask&&!confirm(words.confirm))return;window.GchessExperience?.reset();window.gchessGameResult=null;SAVED_MOVES.splice(0);gameOver=false;finishedGameSynced=false;hideGameStatus();loadPositionUntil(0);renderSavedMoveList();save();document.getElementById('board').focus();}
document.addEventListener('gchess:local-move',save);document.getElementById('local-new-game').addEventListener('click',()=>restart());document.getElementById('game-finish-local-again')?.addEventListener('click',()=>restart(false));rotate.addEventListener('change',save);window.GchessSameDevice.restart=restart;
})();
