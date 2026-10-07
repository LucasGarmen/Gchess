const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.disabled=false;this.hidden=false;this.textContent='';}
 append(...children){this.children.push(...children);}
 prepend(child){this.children.unshift(child);}
 replaceChildren(){this.children=[];this.replacements=(this.replacements||0)+1;}
 addEventListener(type,handler){this.listeners[type]=handler;}
 setAttribute(key,value){this[key]=value;}
 querySelector(selector){return this.children.find(c=>'.'+c.className===selector)||null;}
}
const panel=new Element('div'),count=new Element('span');let request,refreshes=0,fail=false;
const source=fs.readFileSync('games/templates/games/base.html','utf8');
const code=source.slice(source.indexOf("        let notificationSignature = ''"),source.indexOf('        async function fetchGameNotifications()'));
const context=vm.createContext({document:{createElement:tag=>new Element(tag)},notificationPanel:panel,notificationCount:count,UI_TEXTS:{accept:'Accept',reject:'Reject',notification_update_failed:'Failed'},window:{location:{}},getBaseCSRFToken:()=> 'test-token',fetchGameNotifications:async()=>refreshes++,fetch:async(url,options)=>{request={url,options};return {ok:!fail,json:async()=>({ok:true})};}});
vm.runInContext(code,context);
const words={actions:'Games',tournaments:'Tournaments',training:'Training',dismiss:'Dismiss',error:'Try again',note:'Notice hidden'};
const notice={label:'<script>unsafe</script>',url:'/games/3/',open_label:'Open',dismiss_label:'Dismiss',dismiss_url:'/notifications/dismiss/game:3:0/'};
const training={...notice,label:'Weekly',url:'/training/weekly/'};
const invitation={id:4,label:'Invite',opponent_mode:'direct',dismiss_url:'/notifications/dismiss/invite:4/'};
context.renderGameNotifications([invitation],[notice],[notice],[training],words);
assert.equal(count.innerText,3,'training does not inflate the action badge');
assert.deepEqual(panel.children.slice(0,3).map(g=>g.children[0].textContent),['Games','Tournaments','Training']);
assert.equal(panel.children[0].children[2].children[0].textContent,notice.label,'labels are plain text');
context.renderGameNotifications([invitation],[notice],[notice],[training],words);
assert.equal(panel.replacements,1,'unchanged polls preserve buttons and focus');
(async()=>{
 const dismiss=panel.children[0].children[2].children[1].children[1];
 await dismiss.listeners.click();assert.equal(request.options.method,'POST');assert.equal(request.options.headers['X-CSRFToken'],'test-token');assert.equal(refreshes,1);assert.equal(dismiss.disabled,false);
 context.renderGameNotifications([invitation],[],[],[],words);
 fail=true;const accept=panel.children[0].children[1].children[1].children[0];
 await accept.listeners.click();assert.equal(panel.children[0].textContent,'Try again');assert.equal(panel.children[0].role,'alert');assert.equal(accept.disabled,false);
 context.renderGameNotifications([],[],[],[training],words);assert.equal(count.hidden,true);assert.equal(panel.children[0].children[0].textContent,'Training');
 console.log('Notification client checks passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
