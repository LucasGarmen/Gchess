const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../games/static/games/shop.js'),'utf8');
function setup(fetchImpl){
 const handlers={};const feedback={textContent:''};const focused=[];const scroll=[];
 const category={id:'shop-accessory',open:true,querySelector(){return {focus(opts){focused.push(opts);}}}};
 const page={innerHTML:'before',dataset:{saving:'Saving',saveError:'Failed'},busy:false,
  querySelector(){return feedback;},querySelectorAll(){return [category];},
  setAttribute(){this.busy=true;},removeAttribute(){this.busy=false;}};
 const sandbox={console,FormData:class{},URL,
  DOMParser:class{parseFromString(){return {querySelector(selector){return selector==='.shop-page'?{innerHTML:'server-saved-preview'}:null;}}}},
  document:{querySelector(selector){return selector==='.shop-page'?page:null;},getElementById(){return category;},addEventListener(name,fn){handlers[name]=fn;}},
  window:{location:{hash:'',origin:'http://localhost'},scrollY:240,DOMParser:true,fetch:fetchImpl,addEventListener(){},scrollTo(x,y){scroll.push([x,y]);}}};
 vm.runInNewContext(code,sandbox);
 const event={prevented:false,preventDefault(){this.prevented=true;},target:{matches(){return true;},action:'http://localhost/shop/equip/',closest(){return category;}}};
 return {handlers,event,page,feedback,category,scroll,focused};
}
(async()=>{
 const success=setup(async()=>({ok:true,text:async()=>'<server-rendered shop>'}));
 await success.handlers.submit(success.event);
 assert.ok(success.event.prevented);assert.equal(success.page.innerHTML,'server-saved-preview');
 assert.equal(success.category.open,true);assert.equal(success.page.busy,false);
 assert.deepEqual(success.scroll,[[0,240]]);assert.equal(success.focused[0].preventScroll,true);
 let failCalls=0;
 const failure=setup(async()=>{failCalls++;throw new Error('offline');});
 await failure.handlers.submit(failure.event);
 assert.equal(failure.feedback.textContent,'Failed');assert.equal(failure.page.innerHTML,'before');assert.equal(failure.page.busy,false);
 await failure.handlers.submit(failure.event);assert.equal(failCalls,2);
 let resolve;let calls=0;
 const locked=setup(()=>{calls++;return new Promise(r=>{resolve=r;});});
 const first=locked.handlers.submit(locked.event);
 await locked.handlers.submit(locked.event);assert.equal(calls,1);
 resolve({ok:false});await first;assert.equal(locked.page.busy,false);
 console.log('Live shop: saved preview, open categories, scroll/focus, offline retry and duplicate-submit lock passed.');
})().catch(err=>{console.error(err);process.exitCode=1;});
