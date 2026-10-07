const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
let source = fs.readFileSync(path.join(__dirname, '../games/templates/games/game_invitation_wait.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
source = source.replace(/const invitationStatusUrl = .*;/,'const invitationStatusUrl = "/status/";')
  .replace(/const cancelInvitationUrl = .*;/,'const cancelInvitationUrl = "/cancel/";')
  .replace(/const autoSearchUrl = .*;/,'const autoSearchUrl = "/search/";');
const flush = () => new Promise(resolve => setImmediate(resolve));
function setup(hidden=false) {
  const elements = {};
  for (const id of ['invitation-wait-status','cancel-invitation']) elements[id] = {disabled:false,innerText:'',addEventListener(event,handler){this.handler=handler;}};
  const requests=[],timers=[],redirects=[];
  let fetchImpl = async () => ({ok:true,json:async()=>({status:'pending'})});
  const context=vm.createContext({
    document:{hidden,cookie:'csrftoken=test-token',getElementById:id=>elements[id]||null},
    window:{location:{assign:url=>redirects.push(url)}},
    UI_TEXTS:{search_auto_open:'searching',search_connection_retry:'retrying',invitation_cancel_error:'cancel failed'},
    AbortController, navigator:{},
    fetch:async(url,options)=>{requests.push({url,options});return fetchImpl(url,options);},
    setTimeout:(callback,delay)=>{const timer={callback,delay};timers.push(timer);return timer;},
    clearTimeout:timer=>{timer.cleared=true;},
  });
  vm.runInContext(source,context);
  return {context,elements,requests,timers,redirects,setFetch:fn=>fetchImpl=fn};
}
(async()=>{
  let s=setup(); await flush();
  assert.equal(s.requests[0].url,'/search/');
  assert.equal(s.requests[0].options.method,'POST');
  assert.equal(s.requests[0].options.headers['X-CSRFToken'],'test-token');
  assert.equal(s.elements['invitation-wait-status'].innerText,'searching');
  s.setFetch(async()=>({ok:true,json:async()=>({status:'accepted',game_url:'/games/42/'})}));
  await s.timers.find(t=>t.delay===3000).callback(); await flush();
  assert.deepEqual(s.redirects,['/games/42/']);

  s=setup(true);await flush();assert.equal(s.requests.length,0);
  vm.runInContext('document.hidden=false',s.context);
  await s.timers.find(t=>t.delay===3000).callback();await flush();
  assert.equal(s.requests.length,1);

  s=setup();await flush();s.setFetch(async()=>{throw new Error('offline');});
  await s.elements['cancel-invitation'].handler();await flush();
  assert.equal(s.elements['cancel-invitation'].disabled,false);
  assert.equal(s.elements['invitation-wait-status'].innerText,'retrying');
  assert.ok(s.timers.filter(t=>t.delay===3000).length>=2);
  assert.ok(s.timers.filter(t=>t.delay===10000).every(t=>t.cleared));

  s=setup();await flush();let finish;
  s.setFetch(()=>new Promise(resolve=>{finish=resolve;}));
  const pending=vm.runInContext('checkInvitationStatus()',s.context);
  await flush();const requestCount=s.requests.length;
  await vm.runInContext('checkInvitationStatus()',s.context);
  assert.equal(s.requests.length,requestCount);
  finish({ok:true,json:async()=>({status:'pending'})});await pending;
  console.log('Matchmaking client: POST/CSRF, automatic board opening, hidden-tab pause, failed cancellation retry and overlapping-request guard verified.');
})().catch(error=>{console.error(error);process.exitCode=1;});
