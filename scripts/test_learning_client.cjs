const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
for (const file of ['games/static/games/analyzer.js','games/static/games/analyzer.min.js']) {
    for (const saved of [true,false]) {
        const handlers={};
        const sandbox={REVIEW_SAVED:saved, document:{getElementById:()=>null,addEventListener(){}},window:{addEventListener:(name,fn)=>handlers[name]=fn}};
        vm.runInNewContext(fs.readFileSync(file,'utf8'),sandbox);
        let blocked=false;
        handlers.beforeunload({preventDefault(){blocked=true;}});
        assert.equal(blocked,!saved,'Only unsaved reviews should warn about losing analysis');
    }
}
console.log('Saved reviews can be reopened; unsaved analysis keeps its exit warning in both browser artifacts.');
