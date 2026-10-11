(() => {
'use strict';
const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)');
let preference='auto',audio=null,lastMove=null;
try{preference=localStorage.getItem('gchess-motion')||'auto';}catch(_){}
const isReduced=()=>preference==='reduced'||Boolean(reduced?.matches);
const labels={pt:['Reduzir animações','Ativar animações','Animações reduzidas pelo dispositivo'],es:['Reducir animaciones','Activar animaciones','Animaciones reducidas por el dispositivo'],en:['Reduce animations','Enable animations','Animations reduced by your device']}[document.documentElement.lang.slice(0,2)]||['Reduce animations','Enable animations','Animations reduced by your device'];
function render(){document.documentElement.dataset.motion=isReduced()?'reduced':'standard';document.querySelectorAll('[data-motion-toggle]').forEach(button=>{button.disabled=Boolean(reduced?.matches);button.setAttribute('aria-pressed',String(isReduced()));button.title=button.disabled?labels[2]:labels[isReduced()?1:0];button.setAttribute('aria-label',button.title);});}
function context(){if(typeof window.getGameAudioContext==='function')return window.getGameAudioContext();const Type=window.AudioContext||window.webkitAudioContext;if(!Type)return null;try{audio=audio||new Type();return audio;}catch(_){return null;}}
function unlock(){const ctx=context();if(ctx?.state==='suspended')ctx.resume().catch(()=>{});}
// Short, quiet procedural sounds need no downloads, codecs, or external libraries.
function tone(kind){if(!window.GchessSound?.isEnabled()||window.GchessSound.getVolume()===0)return false;const ctx=context();if(!ctx||ctx.state!=='running')return false;
 const patterns={capture:[[170,0,.06],[110,.04,.08]],check:[[480,0,.08],[620,.11,.09]],victory:[[440,0,.1],[554,.11,.1],[659,.22,.16]],defeat:[[330,0,.11],[262,.12,.17]],draw:[[392,0,.09],[392,.12,.14]],finished:[[392,0,.13]]};
 const notes=patterns[kind];if(!notes)return false;
 notes.forEach(([frequency,delay,duration])=>{const oscillator=ctx.createOscillator(),gain=ctx.createGain();oscillator.type=kind==='capture'?'sine':'triangle';oscillator.frequency.value=frequency;const time=ctx.currentTime+delay;gain.gain.setValueAtTime(0,time);gain.gain.linearRampToValueAtTime(kind==='capture'?.055:.025,time+.008);gain.gain.exponentialRampToValueAtTime(.0001,time+duration);oscillator.connect(gain);gain.connect(ctx.destination);const level=ctx.createGain();level.gain.value=1;window.GchessSound.trackBuffer(oscillator,level);gain.disconnect();gain.connect(level);level.connect(ctx.destination);oscillator.addEventListener('ended',()=>{gain.disconnect();level.disconnect();oscillator.disconnect();},{once:true});oscillator.start(time);oscillator.stop(time+duration+.01);});return true;
}
function move(detail){if(lastMove===detail.key)return;lastMove=detail.key;
 const square=document.querySelector(`#board .square[data-coord="${detail.to}"]`);if(square&&!isReduced()){square.classList.remove('move-arrived','capture-arrived');void square.offsetWidth;square.classList.add(detail.capture?'capture-arrived':'move-arrived');setTimeout(()=>square.classList.remove('move-arrived','capture-arrived'),220);}
 if(detail.finished)return;const kind=detail.check?'check':detail.capture?'capture':'move';if(kind==='move'||!tone(kind))detail.fallback?.();
}
window.GchessExperience={isReduced,move,tone,reset(){lastMove=null;}};
document.addEventListener('pointerdown',unlock,{once:true});document.addEventListener('keydown',unlock,{once:true});
document.addEventListener('click',event=>{if(!event.target.closest('[data-motion-toggle]')||reduced?.matches)return;preference=isReduced()?'standard':'reduced';try{localStorage.setItem('gchess-motion',preference);}catch(_){}render();});
window.addEventListener('storage',event=>{if(event.key==='gchess-motion'||event.key===null){preference=event.newValue||'auto';render();}});
reduced?.addEventListener?.('change',render);document.addEventListener('DOMContentLoaded',render);render();
})();
