const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const sandbox = {window:{},document:{body:{dataset:{pieces:'rustic'}}}};
vm.runInNewContext(fs.readFileSync(path.join(root,'games/static/games/cosmetics.js'),'utf8'),sandbox);
for (const style of ['rustic',...fs.readdirSync(path.join(root,'games/static/games')).filter(x=>x.startsWith('pieces-') && x!=='pieces-rustic').map(x=>x.slice(7)),'unknown','../bad']) {
    sandbox.document.body.dataset.pieces=style;
    for (const type of ['king','queen','rook','bishop','horse','pawn']) {
        for (const color of ['white','black']) {
            const url=sandbox.window.GchessPieceUrl(type+'_'+color);
            const expected=['unknown','../bad','rustic'].includes(style)?'rustic':style;
            assert.ok(url.startsWith('/static/games/pieces-'+expected+'/'));
            assert.ok(fs.existsSync(path.join(root,'games/static',url.replace('/static/','').split('?')[0])),url);
        }
    }
}
// Equipment redirects open only a known category. No invented DOM target or script execution.
const category={open:false};
const ui={window:{location:{hash:'#shop-face'},addEventListener(){}},document:{addEventListener(){},getElementById(id){assert.equal(id,'shop-face');return category;}}};
vm.runInNewContext(fs.readFileSync(path.join(root,'games/static/games/shop.js'),'utf8'),ui);
assert.equal(category.open,true);
console.log('Cosmetic asset URLs, safe fallback and category restoration passed.');
