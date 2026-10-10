const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');
function boot(saved,blocked=false){
 const events={},winEvents={},attrs={},classes=new Set(),store={};
 const button={setAttribute(k,v){attrs[k]=v;},classList:{toggle(k,on){on?classes.add(k):classes.delete(k);}},cloneNode(){return this;},removeAttribute(){},after(){}};
 const ctx={Set,Promise,document:{documentElement:{lang:'es'},createElement(){return {setAttribute(){},addEventListener(){}};},querySelectorAll(){return [button];},querySelector(){return null;},addEventListener(k,fn){events[k]=fn;}},window:{addEventListener(k,fn){winEvents[k]=fn;}},localStorage:{getItem(){if(blocked)throw Error('blocked');return saved;},setItem(k,v){if(blocked)throw Error('blocked');store[k]=v;}}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'games/static/games/sound.js'),'utf8'),ctx);events.DOMContentLoaded();
 return {ctx,events,winEvents,attrs,classes,store,click(){events.click({target:{closest(){return button;}}});}};
}
const on=boot(null);assert.equal(on.ctx.window.GchessSound.isEnabled(),true);assert.equal(on.attrs['aria-label'],'Silenciar sonido');
let stopped=0,paused=0;
on.ctx.window.GchessSound.trackBuffer({stop(){stopped++;},addEventListener(){}});
on.ctx.window.GchessSound.trackAudio({dataset:{},volume:1,pause(){paused++;},addEventListener(){}});
on.click();assert.equal(on.store['gchess-sound-enabled'],'false');assert.equal(stopped,1);assert.equal(paused,1);assert.equal(on.attrs['aria-label'],'Activar sonido');assert.equal(on.attrs['aria-pressed'],'false');
on.click();assert.equal(on.store['gchess-sound-enabled'],'true');
const gain={gain:{value:1}};on.ctx.window.GchessSound.trackBuffer({addEventListener(){}},gain);assert.equal(gain.gain.value,.5);
const off=boot('false');assert.equal(off.ctx.window.GchessSound.isEnabled(),false);
const source=fs.readFileSync(path.join(root,'games/static/games/board.js'),'utf8');
vm.runInContext(source.slice(source.indexOf('function playBuffer('),source.indexOf('function unlockStartSoundOnFirstInteraction(')),off.ctx);
off.ctx.getGameAudioContext=()=>{throw Error('Muted sound reached AudioContext');};
assert.equal(vm.runInContext('playBuffer({duration:1})',off.ctx),true);
(async()=>{assert.equal(await vm.runInContext('playAudio({play(){throw Error("Muted playback")}})',off.ctx),true);
off.winEvents.storage({key:'gchess-sound-enabled',newValue:'true'});assert.equal(off.ctx.window.GchessSound.isEnabled(),true);
const privateMode=boot(null,true);privateMode.click();assert.equal(privateMode.ctx.window.GchessSound.isEnabled(),false);
console.log('Sound persistence, mute paths, active sound stop, cross-tab sync and private-storage fallback passed.');})();
