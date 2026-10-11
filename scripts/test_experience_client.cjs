const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('games/static/games/experience.js','utf8');
function boot(systemReduced=false,stored='auto'){
 const events={},storageEvents={},mediaEvents={},oscillators=[],values={},button={setAttribute(k,v){values[k]=v;}},classes=new Set();
 const media={matches:systemReduced,addEventListener(k,fn){mediaEvents[k]=fn;}};
 const square={offsetWidth:20,classList:{remove(...names){names.forEach(n=>classes.delete(n));},add(n){classes.add(n);}}};
 class AudioContext{constructor(){this.state='running';this.currentTime=0;this.destination={};}createOscillator(){const osc={frequency:{},connect(){},disconnect(){},addEventListener(){},start(){},stop(){}};oscillators.push(osc);return osc;}createGain(){return {gain:{value:1,setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}};}}
 const prefs={enabled:true,volume:.5};
 const ctx={Set,Boolean,setTimeout(){},localStorage:{getItem(){return stored;},setItem(k,v){stored=v;}},window:{AudioContext,matchMedia:()=>media,GchessSound:{isEnabled:()=>prefs.enabled,getVolume:()=>prefs.volume,trackBuffer(){}},addEventListener(k,fn){storageEvents[k]=fn;}},document:{documentElement:{lang:'pt',dataset:{}},querySelectorAll:()=>[button],querySelector:()=>square,addEventListener(k,fn){events[k]=fn;}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);return {fx:ctx.window.GchessExperience,ctx,prefs,oscillators,events,storageEvents,mediaEvents,media,classes,values};
}
const app=boot();let fallback=0;const move={key:'1:e2:e4',to:'e4',capture:false,check:false,fallback:()=>fallback++};
app.fx.move(move);app.fx.move(move);assert.equal(fallback,1,'No duplicate move feedback');
app.fx.move({...move,key:'2:d7:e6',capture:true});assert.equal(fallback,1);assert.equal(app.oscillators.length,2);assert(app.classes.has('capture-arrived'));
app.fx.move({...move,key:'3:f1:b5',check:true});assert.equal(app.oscillators.length,4);
app.fx.move({...move,key:'4:h5:f7',finished:true});assert.equal(app.oscillators.length,4,'The decisive move leaves audio to the result event');
app.prefs.enabled=false;assert.equal(app.fx.tone('victory'),false);app.prefs.enabled=true;app.prefs.volume=0;assert.equal(app.fx.tone('victory'),false);
app.events.click({target:{closest:()=>({})}});assert.equal(app.fx.isReduced(),true);app.ctx.document.documentElement.dataset.motion='reduced';app.fx.reset();app.fx.move(move);assert.equal(fallback,2);
const reduced=boot(true);assert.equal(reduced.fx.isReduced(),true);assert.equal(reduced.values['aria-pressed'],'true');assert.equal(reduced.fx.isReduced(),true);
const persisted=boot(false,'reduced');assert.equal(persisted.fx.isReduced(),true);persisted.storageEvents.storage({key:'gchess-motion',newValue:'standard'});assert.equal(persisted.fx.isReduced(),false);
console.log('Experience: distinct and deduplicated audio, mute/zero volume, finished move suppression, reset, saved/system reduced motion and cross-tab preferences passed.');
