const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
let listener, now = 0; const played=[];
const sandbox={performance:{now:()=>now},window:{GchessExperience:{interaction:kind=>played.push(kind)}},document:{addEventListener(name,fn,capture){assert.equal(name,'click');assert.equal(capture,true);listener=fn;}}};
vm.runInNewContext(fs.readFileSync('games/static/games/ui_sound.js','utf8'),sandbox);
function click({summary=false,open=false,expanded=null,disabled=false,excluded=false,trusted=true}={}){
 now+=100;const control={matches:s=>s==='summary'?summary:disabled,closest:()=>excluded?{}:null,getAttribute:()=>expanded,parentElement:{open}};
 listener({isTrusted:trusted,defaultPrevented:false,target:{closest:()=>control}});
}
click();click({summary:true});click({summary:true,open:true});click({expanded:'false'});click({expanded:'true'});
assert.deepEqual(played,['ui_click','ui_open','ui_close','ui_open','ui_close']);
for(const args of [{disabled:true},{excluded:true},{trusted:false}])click(args);
assert.equal(played.length,5,'Disabled controls, board/mute controls and programmatic events are silent');
now=500;listener({isTrusted:true,target:{closest:()=>({matches:()=>false,closest:()=>null,getAttribute:()=>null})}});
assert.equal(played.length,5,'Rapid duplicates are suppressed');
console.log('UI sounds: click, expand/collapse, silent excluded controls and duplicate suppression passed.');
