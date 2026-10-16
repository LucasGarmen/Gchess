const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let intersect,observed;const preview={classList:{toggle(name,on){this[name]=on;}}};
const board={innerHTML:'initial',closest:()=>preview};
const elements={'hero-demo-lines':{textContent:'[]'}};
const ctx={document:{querySelector:()=>board,getElementById:id=>elements[id]||null},matchMedia:()=>({matches:true,addEventListener(){}}),setTimeout(){},IntersectionObserver:class{constructor(fn){intersect=fn;}observe(target){observed=target;}}};
vm.runInNewContext(fs.readFileSync('games/static/games/home_demo.js','utf8'),ctx);assert.equal(observed,preview);intersect([{isIntersecting:true}]);assert.equal(preview.classList['demo-in-view'],true);intersect([{isIntersecting:false}]);assert.equal(preview.classList['demo-in-view'],false);
console.log('Demo: reduced-motion compatibility and visibility state passed.');
