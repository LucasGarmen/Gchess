const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const storage=new Map();const ctx={window:{},sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('games/static/games/same_device_state.js','utf8'),ctx);const state=ctx.window.GchessSameDevice;
assert.equal(state.read().length,0);const moves=[{move_number:1,from:'e2',to:'e4',piece_type:'pawn',piece_color:'white'}];state.save(moves);assert.equal(state.read()[0].to,'e4');assert(!state.key.includes('computer'));
state.save([{...moves[0],to:'z4'}]);assert.equal(state.read().length,0);state.save([{...moves[0],piece_color:'black'}]);assert.equal(state.read().length,0);storage.set(state.key,'broken');assert.equal(state.read().length,0);ctx.sessionStorage.getItem=()=>{throw new Error('disabled')};assert.equal(state.read().length,0);
for(const file of ['board.js','board.min.js']){
 const source=fs.readFileSync('games/static/games/'+file,'utf8');const sandbox={LOCAL_PLAY_MODE:true,COMPUTER_MODE:false,MULTIPLAYER_MODE:false,GAME_PLAYER_COLOR:null,PLAYER_COLOR:'white',currentTurn:'white',analysisMode:false,gameOver:false,isEngineThinking:false,computerThinking:false,fetch(){throw new Error('Local game must not contact game server')},finishedGameSynced:false};vm.createContext(sandbox);
 for(const name of ['isLocalPlayMode','isComputerMode','isMultiplayerMode','playerColor','botRequestLocked','canPlayerMoveFrom','saveMoveToDatabase','syncFinishedGame']){
  const re=new RegExp('function '+name+'\\([^)]*\\)\\s*\\{');const match=re.exec(source);assert(match,name);let depth=1,index=match.index+match[0].length;while(depth&&index<source.length){if(source[index]==='{')depth++;if(source[index]==='}')depth--;index++;}vm.runInContext(source.slice(match.index,index),sandbox);
 }
 sandbox.isViewingLatestPosition=()=>true;sandbox.squareColor=s=>s.color;
 assert.equal(sandbox.canPlayerMoveFrom({color:'white'}),true);sandbox.currentTurn='black';assert.equal(sandbox.canPlayerMoveFrom({color:'black'}),true);assert.equal(sandbox.canPlayerMoveFrom({color:'white'}),false);
 sandbox.saveMoveToDatabase({});sandbox.syncFinishedGame('white');assert.equal(sandbox.finishedGameSynced,false);sandbox.gameOver=true;assert.equal(sandbox.canPlayerMoveFrom({color:'black'}),false);
}
console.log('Same-device state: restore, malformed/disabled storage, both turns and no game-server writes verified in source and shipped JS.');
