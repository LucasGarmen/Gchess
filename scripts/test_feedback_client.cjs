const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let ready,submit,resolveFetch,calls=0,lastRequest;
const words={sending:'Sending',thanks:'Saved',error:'Retry',rate_limit:'Wait'};
const message={value:'A useful suggestion'},send={disabled:false},status={textContent:''};
const form={action:'/feedback/',elements:{category:{value:'idea'},message},reportValidity:()=>true,setAttribute(){},querySelector:()=>({value:'csrf-test'}),addEventListener(n,fn){if(n==='submit')submit=fn;}};
const elements={'launch-ux-texts':{textContent:JSON.stringify(words)},'feedback-form':form,'feedback-send':send,'feedback-status':status};
const ctx={AbortController,setTimeout,clearTimeout,location:{pathname:'/training/'},document:{addEventListener(n,fn){ready=fn;},getElementById:id=>elements[id]||null},fetch:(url,options)=>{calls++;lastRequest=options;return new Promise(resolve=>{resolveFetch=resolve;});}};
vm.runInNewContext(fs.readFileSync('games/static/games/launch_ux.js','utf8'),ctx);ready();
(async()=>{
 const event={preventDefault(){}};const pending=submit(event);await submit(event);assert.equal(calls,1,'Double submit is blocked');assert.equal(send.disabled,true);assert.equal(lastRequest.headers['X-CSRFToken'],'csrf-test');
 resolveFetch({ok:false,status:500});await pending;assert.equal(message.value,'A useful suggestion','Failed submission preserves the draft');assert.equal(status.textContent,'Retry');assert.equal(send.disabled,false);
 const retry=submit(event);resolveFetch({ok:true,status:200,json:async()=>({saved:true})});await retry;assert.equal(message.value,'');assert.equal(status.textContent,'Saved');assert.equal(send.disabled,false);
 message.value='Another useful suggestion';const limited=submit(event);resolveFetch({ok:false,status:429});await limited;assert.equal(status.textContent,'Wait');assert.equal(message.value,'Another useful suggestion');
 console.log('Feedback UI: duplicate guard, CSRF, draft preservation, retry, success and rate limit passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
