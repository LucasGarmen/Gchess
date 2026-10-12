const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const words={victory:'Victory!',defeat:'Defeat',draw:'Draw',finished:'Finished',view_result:'View result',mate:'Checkmate',white_wins:'White wins',black_wins:'Black wins'};
for(const kind of ['victory','defeat','draw','finished']){words[kind+'_note']=kind+' note';words[kind+'_tip']=kind+' tip';}
const make=(extra={})=>Object.assign({hidden:false,dataset:{},textContent:'',events:{},classList:{flags:new Set(),contains(k){return this.flags.has(k);},add(k){this.flags.add(k);},toggle(k,on){on?this.flags.add(k):this.flags.delete(k);}},addEventListener(k,fn){this.events[k]=fn;},focus(){this.focused=true;},prepend(el){el.parentElement=this;},append(el){el.parentElement=this;}},extra);
const events={},wrapper=make(),stage=make(),layout=make(),ids={};
for(const id of ['game-finish-notice','game-status','game-finish-title','game-finish-result','game-finish-note','game-finish-tip','game-finish-moves','game-finish-captures','undo-computer-move','toggle-coach','game-finish-dismiss','game-finish-view-board','game-finish-again','game-finish-analyze','analyze-game-form','analyze-game-button'])ids[id]=make();
const advice=make(),analyzeAction=make();ids['game-finish-notice'].querySelector=selector=>selector==='.game-finish-advice'?advice:selector==='.game-finish-secondary'?analyzeAction:null;
ids['game-finish-notice'].parentElement=wrapper;ids['game-finish-notice'].closest=()=>layout;
ids['game-result-words']={textContent:JSON.stringify(words)};
let focused=null,atEnd=true,played=[],resetArgs=[],submit=0,exits=0,mate=false,stalemate=false;
ids.board=make({closest:()=>stage,querySelectorAll:()=>({length:31})});
ids['analyze-game-form'].requestSubmit=()=>submit++;
let reopen;
const ctx={gameOver:false,analysisMode:false,currentTurn:'black',GAME_PLAYER_COLOR:'white',GAME_RESULT:'unknown',SAVED_MOVES:[{},{},{},{}],Set,window:{GchessExperience:{tone:kind=>played.push(kind)},GchessFocus:{exit:()=>exits++}},isCheckmate:()=>mate,isStalemate:()=>stalemate,hasInsufficientMaterial:()=>false,isViewingLatestPosition:()=>atEnd,resetComputerGame:arg=>resetArgs.push(arg),document:{getElementById:id=>ids[id]||null,createElement(){return reopen=make();},querySelector:()=>focused,addEventListener(name,fn){events[name]=fn;}},MutationObserver:class{observe(){}}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('games/static/games/game_finish.js','utf8'),ctx);
const refresh=events['gchess:position-changed'];assert.equal(ids['game-finish-notice'].hidden,true);
ctx.gameOver=true;mate=true;refresh();assert.equal(ids['game-finish-title'].textContent,'Victory!');assert.equal(ids['game-finish-result'].textContent,'Checkmate · White wins');assert.equal(ids['game-finish-moves'].textContent,4);assert.equal(ids['game-finish-captures'].textContent,1);assert.deepEqual(played,['victory']);refresh();assert.deepEqual(played,['victory']);
ids['game-finish-dismiss'].events.click();assert.equal(ids['game-finish-notice'].hidden,true);assert.equal(reopen.hidden,false);refresh();assert.equal(ids['game-finish-notice'].hidden,true);
reopen.events.click();assert.equal(ids['game-finish-notice'].hidden,false);
focused=make({querySelector:()=>stage});events['gchess:focus-mode-changed']();assert.equal(ids['game-finish-notice'].parentElement,stage);assert(focused.classList.contains('game-ended-visible'));
atEnd=false;refresh();assert.equal(ids['game-finish-notice'].hidden,true);atEnd=true;refresh();assert.deepEqual(played,['victory'],'Reviewing the end does not repeat the result sound');
ctx.currentTurn='white';refresh();assert.equal(ids['game-finish-title'].textContent,'Defeat');
mate=false;ctx.window.gchessGameResult='draw';refresh();assert.equal(ids['game-finish-title'].textContent,'Draw');
ctx.window.gchessGameResult='black';refresh();assert.equal(ids['game-finish-title'].textContent,'Defeat','Server resignations and timeouts use the actual winner');
ids['game-finish-again'].events.click();assert.deepEqual(resetArgs,[false]);ids['game-finish-analyze'].events.click();assert.equal(submit,1);assert.equal(exits,1);
focused=null;refresh();assert.equal(ids['game-finish-notice'].parentElement,stage);
ctx.analysisMode=true;refresh();assert.equal(ids['game-finish-notice'].hidden,true);assert.equal(reopen.hidden,true);
console.log('Result panel: perspective, draws, server results, actual stats, dismiss/reopen, fullscreen, replay sound deduplication, analysis and play again passed.');

ctx.analysisMode=false;ctx.SAVED_MOVES=[];refresh();assert.equal(advice.hidden,true);assert.equal(analyzeAction.hidden,true,'A game with no moves must not offer an empty analysis');

(async()=>{
 const source=fs.readFileSync('games/static/games/game_finish.js','utf8');
 async function rewardCase(responses, expected, failing=false){
  const target=make({hidden:true,dataset:{url:'/rewards/progress/?game=1',label:'XP earned'}});
  ids['game-finish-xp']=target;let calls=0;const timers=[];
  ctx.fetch=async()=>{calls++;if(failing)throw new Error('offline');return {ok:true,json:async()=>responses[Math.min(calls-1,responses.length-1)]};};
  ctx.setTimeout=fn=>timers.push(fn);ctx.gameOver=true;ctx.analysisMode=false;
  vm.runInContext(source,ctx);
  for(let i=0;i<8;i++){await new Promise(resolve=>setImmediate(resolve));if(timers.length)timers.shift()();}
  assert.equal(target.hidden,expected===0);
  if(expected)assert.equal(target.textContent,`+${expected} XP earned`);
  assert.equal(ids['game-finish-notice'].hidden,false,'Progress failures cannot hide the result');
  events['gchess:position-changed']();await new Promise(resolve=>setImmediate(resolve));
  return calls;
 }
 assert.equal(await rewardCase([{earned:5,pending:false}],5),1);
 assert.equal(await rewardCase([{earned:0,pending:false}],0),1);
 assert.equal(await rewardCase([{earned:0,pending:true},{earned:5,pending:false}],5),2);
 assert.equal(await rewardCase([],0,true),1);
 assert.equal(await rewardCase([{earned:0,pending:true}],0),5,'Pending reward retries are bounded');
 console.log('Result XP: authoritative values, zero reward, bounded pending retries and network failure verified.');
})().catch(error=>{console.error(error);process.exitCode=1;});
