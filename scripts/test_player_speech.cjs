const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.hidden=false;this.style={};this.events={};this.className='';this.title='';this.classList={contains:k=>this.className.split(' ').includes(k),toggle:(k,on)=>{const set=new Set(this.className.split(' ').filter(Boolean));on?set.add(k):set.delete(k);this.className=[...set].join(' ');}};}
 append(...items){for(const item of items){if(item.parentElement)item.parentElement.children=item.parentElement.children.filter(x=>x!==item);item.parentElement=this;this.children.push(item);}}
 prepend(item){this.append(item);this.children=[item,...this.children.filter(x=>x!==item)];}
 setAttribute(){} removeAttribute(name){if(name==='style')this.style={};}
 remove(){this.parentElement.children=this.parentElement.children.filter(x=>x!==this);this.parentElement=null;}
 getBoundingClientRect(){return this.rect||{top:100,bottom:160,left:900,right:960,height:60};}
 addEventListener(name,fn){this.events[name]=fn;}
 querySelector(selector){return this.children.find(x=>x.tag===selector)||null;}
}
const stage=new El(),side=new El(),log=new El(),white=new El(),black=new El();stage.dataset={viewerColor:'white',boardOrientation:'white'};white.title='White player';black.title='Black player';let focus=false;
stage.closest=()=>focus?{}:null;stage.querySelector=s=>s.includes('white')?white:black;
const listeners={},observers=new Map();let messages=[];log.querySelectorAll=()=>messages;log.querySelector=()=>({});
let resizes=0;const timeouts=[];white.rect={top:650,bottom:710,left:900,right:960,height:60};black.rect={top:100,bottom:160,left:900,right:960,height:60};
const ctx={innerHeight:768,innerWidth:1366,setTimeout:(fn,delay)=>{assert.equal(delay,8000);timeouts.push(fn);return timeouts.length;},clearTimeout(){},Event:class{},window:{addEventListener(k,fn){listeners[k]=fn;},dispatchEvent(){resizes++;}},document:{documentElement:{lang:'es'},addEventListener(k,fn){listeners[k]=fn;},querySelector:s=>s.includes('board-player-stage')?stage:s.includes('online-side')?side:null,getElementById:id=>id==='game-chat-messages'?log:null,createElement:tag=>new El(tag)},MutationObserver:class{constructor(fn){this.fn=fn;}observe(target){observers.set(target,this.fn);}}};
vm.runInNewContext(fs.readFileSync('games/static/games/player_speech.js','utf8'),ctx);listeners.DOMContentLoaded();
function message(id,mine,text){return {dataset:{messageId:String(id)},classList:{contains:()=>mine},querySelector:()=>({textContent:text})};}
messages=[message(1,true,'First')];observers.get(log)();const own=stage.children[0];const first=own.children[0];assert.equal(first.querySelector('p').textContent,'First');assert.equal(own.dataset.speaker,'White player');assert.equal(own.style.left,'970px');assert.equal(own.style.top,'650px');
messages.push(message(2,true,'Second'));observers.get(log)();const second=own.children[1];assert.equal(own.children.length,2,'Messages stack instead of replacing each other');assert.equal(first.querySelector('p').textContent,'First');assert.equal(second.querySelector('p').textContent,'Second');timeouts[0]();assert.equal(own.children.length,1);assert.equal(own.children[0],second,'First expiry leaves the newer message intact');assert.equal(own.hidden,false);
messages.push(message(3,false,'Opponent'));observers.get(log)();const opponent=stage.children[1];assert.equal(opponent.children[0].querySelector('p').textContent,'Opponent');assert.equal(opponent.style.top,'100px');assert.equal(resizes,0,'Desktop messages do not resize board');
ctx.innerWidth=390;listeners.resize();assert.equal(own.style.left,undefined);assert(stage.classList.contains('player-speech-top'));assert(stage.classList.contains('player-speech-bottom'));
ctx.innerWidth=1366;focus=true;listeners.resize();const before=resizes;assert.equal(own.parentElement,stage);assert(!stage.classList.contains('player-speech-top'));assert(!stage.classList.contains('player-speech-bottom'));
second.querySelector('button').events.click();assert.equal(own.hidden,true);assert.equal(opponent.hidden,false,'Closing own message does not close rival message');assert.equal(resizes,before);timeouts.at(-1)();assert.equal(opponent.hidden,true);assert.equal(resizes,before,'Expiry does not resize desktop fullscreen');
console.log('Player speech: independent 8-second messages, stacking, close, expiry, anchors and stable fullscreen passed.');
