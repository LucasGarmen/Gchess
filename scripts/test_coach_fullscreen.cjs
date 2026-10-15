const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.events={};this.className='';this.hidden=false;this.textContent='';this.style={setProperty(){}};this.classList={contains:k=>this.className.split(' ').includes(k),add:k=>{if(!this.classList.contains(k))this.className+=' '+k;},remove:k=>this.className=this.className.split(' ').filter(x=>x!==k).join(' '),toggle:(k,on)=>on?this.classList.add(k):this.classList.remove(k)};}
 detach(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(x=>x!==this);this.parentElement=null;}
 append(...nodes){for(const node of nodes){node.detach();node.parentElement=this;this.children.push(node);}}
 insertBefore(node,before){node.detach();node.parentElement=this;this.children.splice(this.children.indexOf(before),0,node);}
 setAttribute(k,v){this[k]=v;}getAttribute(k){return this[k]??null;}removeAttribute(k){if(k==='style')this.style={setProperty(){}};else delete this[k];}
 addEventListener(k,fn){this.events[k]=fn;}
 closest(selector){let e=this;while(e){if(e.classList.contains(selector.slice(1)))return e;e=e.parentElement;}return null;}
 getBoundingClientRect(){return {left:20,right:60,top:50,width:400,height:100};}
 querySelectorAll(selector){return this.children.filter(x=>x.classList.contains(selector.slice(1)));}
 get lastElementChild(){return this.children.at(-1);}
}
function boot(width){
 const body=new Element();body.className='mobile-bot-playing';const wrapper=new Element();wrapper.className='board-wrapper';const stage=new Element();stage.className='board-player-stage';const avatar=new Element();wrapper.append(stage);stage.append(avatar);body.append(wrapper);
 const log=new Element(),form=new Element(),comment=new Element();comment.hidden=true;const events={},observers=[];
 const replyArea=new Element();replyArea.className='computer-side';body.append(replyArea);const layout={querySelector:selector=>selector==='.computer-side'?replyArea:avatar};const document={body,documentElement:{lang:'pt'},querySelector:()=>layout,getElementById:id=>({'trainer-chat-form':form,'trainer-chat-log':log,'coach-comment':comment}[id]),createElement:tag=>new Element(tag),addEventListener(k,fn){events[k]=fn;}};
 const ctx={document,innerWidth:width,innerHeight:844,window:{addEventListener(){},visualViewport:{addEventListener(){}}},MutationObserver:class{constructor(fn){this.fn=fn;}observe(target){observers.push({target,fn:this.fn});}}};
 vm.runInNewContext(fs.readFileSync('games/static/games/coach_access.js','utf8'),ctx);events.DOMContentLoaded();
 const dock=body.children.find(x=>x.classList.contains('coach-chat-dock')),bubble=body.children.find(x=>x.classList.contains('board-coach-bubble'));
 function reply(text){const message=new Element();message.className='trainer-chat-message-trainer';message.textContent=text;log.append(message);observers.find(x=>x.target===log).fn();}
 function advice(text){comment.hidden=false;comment.textContent=text;observers.find(x=>x.target===comment).fn();}
 function enter(){const full=new Element();full.className='focus-play';body.append(full);full.append(dock);events['gchess:focus-mode-changed']();return full;}
 function exit(full){body.append(dock);full.detach();events['gchess:focus-mode-changed']();}
 return {body,stage,replyArea,dock,bubble,reply,advice,enter,exit};
}
for(const width of [1280,390]){
 const app=boot(width);app.reply('Original reply');const full=app.enter();assert.equal(app.bubble.parentElement,app.dock,'Existing reply enters native fullscreen subtree');
 app.reply('New reply while fullscreen');assert.equal(app.bubble.hidden,false);assert.equal(app.bubble.children[1].textContent,'New reply while fullscreen');assert.equal(app.bubble.parentElement,app.dock);
 app.advice('Automatic advice');assert.equal(app.bubble.children[1].textContent,'Automatic advice');
 app.bubble.children[0].events.click();assert.equal(app.bubble.hidden,true);app.reply('Another reply');assert.equal(app.bubble.hidden,false);
 app.exit(full);assert.equal(app.bubble.parentElement,width<=900?app.stage:app.replyArea,'Normal placement returns after exiting');assert.equal(app.bubble.children[1].textContent,'Another reply');assert.equal(app.bubble.classList.contains('coach-reply-fullscreen'),false);
 app.reply('Long advice '.repeat(70));const expand=app.bubble.children[2];assert.equal(expand.hidden,false);expand.events.click();assert.equal(expand.getAttribute('aria-expanded'),'true');assert.equal(app.bubble.classList.contains('coach-reply-expanded'),true);app.reply('Short');assert.equal(expand.hidden,true);assert.equal(app.bubble.classList.contains('coach-reply-expanded'),false);const again=app.enter();assert.equal(app.bubble.parentElement,app.dock);app.exit(again);assert.equal(app.dock.children.filter(x=>x===app.bubble).length,0,'Repeated fullscreen does not leave duplicate replies');
}
console.log('Coach fullscreen: PC/mobile, existing/new replies, automatic advice, close, restore and repeated entry passed.');
