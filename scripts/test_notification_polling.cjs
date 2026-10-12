const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('games/templates/games/base.html','utf8');const start=html.indexOf('let notificationsInFlight = false;'),end=html.indexOf("document.addEventListener('visibilitychange'",start);assert(start>=0&&end>start);
let calls=0,resolveFetch,rendered=0;const ctx={document:{hidden:true},notificationAuthWarningShown:false,notificationNetworkWarningShown:false,notificationsUrl:'/notifications/games/',UI_TEXTS:{notification_polling_stopped:'stop',notification_update_failed:'failed'},console:{warn(){}},fetch:()=>{calls++;return new Promise(resolve=>resolveFetch=resolve);},shouldStopNotificationPolling:r=>r.status===401,stopNotificationPolling:()=>ctx.notificationAuthWarningShown=true,renderGameNotifications:()=>rendered++,positionNotificationPanel(){}};
vm.createContext(ctx);vm.runInContext(html.slice(start,end)+';this.poll=fetchGameNotifications;',ctx);
(async()=>{
 await ctx.poll();assert.equal(calls,0,'Hidden tabs do not poll');ctx.document.hidden=false;
 const first=ctx.poll();await ctx.poll();assert.equal(calls,1,'An in-flight request cannot overlap');
 resolveFetch({ok:true,status:200,json:async()=>({})});await first;assert.equal(rendered,1);
 const second=ctx.poll();resolveFetch({ok:false,status:500});await second;
 const third=ctx.poll();resolveFetch({ok:true,status:200,json:async()=>({})});await third;assert.equal(rendered,2,'Server errors release the request guard');
 const last=ctx.poll();resolveFetch({ok:false,status:401});await last;await ctx.poll();assert.equal(calls,4,'Authentication failures stop future polling');
 console.log('Notification polling: hidden tabs, overlapping requests, recovery and authentication stop passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
