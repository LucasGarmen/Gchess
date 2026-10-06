const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('games/static/games/practice.js','utf8');
const initialize = source.slice(source.indexOf("    const challengeStartButton ="), source.lastIndexOf('}());'));
for (const challenge of [true, false]) {
    let selected=0,started=0;
    const button={disabled:false,hidden:false,dataset:{readyText:'Ready'},addEventListener(name,fn){this[name]=fn;}};
    const context={
        document:{getElementById:()=>button,body:{classList:{add(){}}}},
        puzzles:[{}],currentCategory:'test',challengeMode:challenge,
        selectCategory(){selected++;},startBlitzTimer(){started++;},showResult(){},uiText:(_,fallback)=>fallback,
    };
    vm.runInNewContext(initialize,context);
    if(challenge) {
        assert.equal(started,0,'Reading the rules must not start the clock');
        assert.equal(selected,0,'A timed puzzle must not be exposed before starting');
        button.click();button.click();
        assert.equal(started,1,'Double clicks must start exactly one run');
        assert.equal(selected,1);
        assert.equal(button.hidden,true);
    } else {
        assert.equal(selected,1,'Untimed practice must remain immediately available');
    }
}
console.log('Challenge entry: clock waits, double clicks are guarded, practice still starts normally.');
