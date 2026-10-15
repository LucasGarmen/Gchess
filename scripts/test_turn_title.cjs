const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('games/static/games/online_status.js','utf8');
const snippet=source.slice(source.indexOf(' const originalTitle='),source.indexOf(' let lastCount='));
for(const word of ['Tu turno','Sua vez','Your turn']){
 let callback,created=0,cleared=0;const document={title:'Mesa | Gchess'};
 const context={document,words:[word],setInterval(fn,delay){assert.equal(delay,1200);callback=fn;return ++created;},clearInterval(){cleared++;}};
 vm.createContext(context);vm.runInContext(snippet,context);context.titleTurn(true);assert.equal(document.title,word);context.titleTurn(true);assert.equal(created,1);callback();assert.equal(document.title,'Gchess');callback();assert.equal(document.title,word);context.titleTurn(false);assert.equal(document.title,'Mesa | Gchess');assert.equal(cleared,1);
}
console.log('Turn title: three languages, alternation, single timer and restore passed.');
