const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let ready,submit,response,payload,rendered,moved=false;
const status={setAttribute(){},hidden:true},button={textContent:'Send',disabled:false},input={value:'hello'},panel={classList:{add(){}}};
const form={querySelector:()=>button,before(){},setAttribute(){},addEventListener(name,fn,capture){assert(capture);submit=fn;}};
const elements={'game-chat-form':form,'game-chat-input':input,'game-chat-panel':panel,'game-chat-toggle':{}};
const ctx={GAME_ID:7,AbortController,setTimeout,clearTimeout,document:{documentElement:{lang:'en'},cookie:'csrftoken=test',addEventListener(n,fn){ready=fn;},getElementById:id=>elements[id],createElement:()=>status,querySelector:()=>({append(){moved=true;}}),body:{append(){}}},renderGameChat:data=>rendered=data,fetch:async(url,options)=>{payload={url,options};return response;}};
vm.runInNewContext(fs.readFileSync('games/static/games/online_chat.js','utf8'),ctx);ready();
const event={preventDefault(){},stopImmediatePropagation(){}};
(async()=>{
 response={ok:false,status:503};await submit(event);assert.equal(input.value,'hello');assert.equal(status.hidden,false);assert.equal(button.disabled,false);
 response={ok:true,status:200,json:async()=>({messages:[{text:'hello'}]})};await submit(event);assert.equal(input.value,'');assert.equal(rendered.messages[0].text,'hello');assert.equal(payload.options.headers['X-CSRFToken'],'test');assert.equal(payload.url,'/games/7/chat/?mark_read=1');assert(moved);
 input.value='keep me';response={ok:true,status:200,redirected:true};await submit(event);assert.equal(input.value,'keep me');assert(status.textContent.includes('Session expired'));
 let resolve;ctx.fetch=()=>new Promise(r=>resolve=r);const first=submit(event);await submit(event);assert.equal(button.disabled,true);resolve({ok:true,status:200,json:async()=>({messages:[]})});await first;assert.equal(button.disabled,false);
 console.log('Online chat: confirmed HTTP send, CSRF, preserved failures, expired session, pending guard and near-board control passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
