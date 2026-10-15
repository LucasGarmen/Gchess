const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.hidden=false;this.style={};this.events={};this.className='';this.title='';this.classList={contains:k=>this.className.split(' ').includes(k),toggle:(k,on)=>{const set=new Set(this.className.split(' ').filter(Boolean));on?set.add(k):set.delete(k);this.className=[...set].join(' ');}};}
 append(...items){for(const item of items){if(item.parentElement)item.parentElement.children=item.parentElement.children.filter(x=>x!==item);item.parentElement=this;this.children.push(item);}}
 prepend(item){this.append(item);this.children=[item,...this.children.filter(x=>x!==item)];}
 setAttribute(){} removeAttribute(name){if(name==='style')this.style={};}
 addEventListener(name,fn){this.events[name]=fn;}
 querySelector(selector){return this.children.find(x=>x.tag===selector)||null;}
}
const stage=new El(),side=new El(),log=new El(),white=new El(),black=new El();stage.dataset={viewerColor:'white',boardOrientation:'white'};white.title='White player';black.title='Black player';let focus=false;
stage.closest=()=>focus?{}:null;stage.querySelector=s=>s.includes('white')?white:black;
const listeners={},observers=new Map();let messages=[];log.querySelectorAll=()=>messages;log.querySelector=()=>({});
const ctx={innerWidth:1366,setTimeout:()=>1,clearTimeout(){},Event:class{},window:{addEventListener(k,fn){listeners[k]=fn;},dispatchEvent(){}},document:{documentElement:{lang:'es'},addEventListener(k,fn){listeners[k]=fn;},querySelector:s=>s.includes('board-player-stage')?stage:s.includes('online-side')?side:null,getElementById:id=>id==='game-chat-messages'?log:null,createElement:tag=>new El(tag)},MutationObserver:class{constructor(fn){this.fn=fn;}observe(target){observers.set(target,this.fn);}}};
vm.runInNewContext(fs.readFileSync('games/static/games/player_speech.js','utf8'),ctx);listeners.DOMContentLoaded();
function message(id,mine,text){return {dataset:{messageId:String(id)},classList:{contains:()=>mine},querySelector:()=>({textContent:text})};}
messages=[message(1,true,'My message')];observers.get(log)();const own=side.children[1].children[0];assert.equal(own.querySelector('p').textContent,'My message');assert.equal(own.dataset.speaker,'White player');
messages.push(message(2,false,'Opponent message'));observers.get(log)();assert.equal(side.children[0].children[0].querySelector('p').textContent,'Opponent message');
ctx.innerWidth=390;listeners.resize();assert.equal(own.parentElement,stage,'Mobile bubbles stay beside portraits');
ctx.innerWidth=1366;focus=true;listeners.resize();assert.equal(own.parentElement,stage,'Fullscreen keeps speech inside the moved stage');
focus=false;listeners.resize();assert.equal(own.parentElement,side.children[1],'Exit fullscreen restores reserved reply area');assert(!own.style.left,'No fixed overlay position in desktop reply area');
console.log('Player speech: reserved desktop areas, speaker identity, mobile and fullscreen reparenting passed.');
