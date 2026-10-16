const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for (const name of ['board.js','board.min.js']) {
 const source=fs.readFileSync('games/static/games/'+name,'utf8');
 const start=source.indexOf('function ensureCoachWelcome()'),end=source.indexOf('function addTrainerChatMessage(',start);
 const serialize=source.slice(source.indexOf('function trainerChatLogState()'),source.indexOf('function restoreTrainerChatLog('));
 const hiddenLog={children:[{dataset:{messageType:'trainer'},innerText:'',textContent:'Saved welcome'}]};
 const persistence={document:{getElementById:()=>hiddenLog}};vm.runInNewContext(serialize,persistence);assert.equal(persistence.trainerChatLogState()[0].message,'Saved welcome','Closed chat must retain its text');
 const log={children:[],dataset:{welcome:'Hello from Gchess Bot'}};let home=true,added=0;
 const ctx={isHomeComputerGame:()=>home,document:{getElementById:()=>log},addTrainerChatMessage(text,type){assert.equal(text,log.dataset.welcome);assert.equal(type,'trainer');log.children.push({});added++}};
 vm.runInNewContext(source.slice(start,end),ctx);ctx.ensureCoachWelcome();ctx.ensureCoachWelcome();assert.equal(added,1,'Reloaded conversation must not receive a duplicate welcome');
 log.children=[{text:'Saved conversation'}];ctx.ensureCoachWelcome();assert.equal(added,1);
 home=false;log.children=[];ctx.ensureCoachWelcome();assert.equal(added,1,'Other boards must not get a coach welcome');
 const handler=source.match(/document.getElementById\(['"]home-quick-start['"]\)\?\.addEventListener\(['"]click['"],\s*\(\)\s*=>\s*\{([\s\S]*?)\}\);?/);
 assert.ok(handler,name+' exposes the direct entry action');
 let started=0,toggled=0;
 const quick={SAVED_MOVES:[],coachEnabled:false,toggleCoach(){toggled++;this.coachEnabled=true},startEntryCoachGame(){started++}};
 vm.runInNewContext('(function(){'+handler[1]+'})()',quick);assert.equal(started,1);assert.equal(toggled,1);
 quick.SAVED_MOVES.push({});vm.runInNewContext('(function(){'+handler[1]+'})()',quick);assert.equal(started,2);assert.equal(toggled,1,'Existing game keeps its coach preference');
}
console.log('Coach welcome: initial message, saved-history preservation, scope and direct entry passed in both bundles.');
