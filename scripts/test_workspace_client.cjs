const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('games/static/games/board.js', 'utf8');
const snippet = source.slice(source.indexOf('function saveComputerGameState()'), source.indexOf('function mobileHomeElements()'));
const store = new Map();
const make = id => {
  const context = {
    COMPUTER_GAME_STATE_KEY: 'account:1:bot:' + id,
    SAVED_MOVES: [], PLAYER_COLOR: 'white', boardOrientation: 'white', coachEnabled: true, gameOver: false,
    isHomeComputerGame: () => true, playerColor: () => 'white', trainerChatLogState: () => [{text:id}],
    restoreTrainerChatLog: messages => { context.chat = messages; },
    document: {getElementById: () => null},
    window: {sessionStorage: {setItem:(key,value)=>store.set(key,value), getItem:key=>store.get(key)}, GChessWorkspace:{updateBot:meta=>{context.meta=meta;}}},
    console,
  };
  vm.createContext(context); vm.runInContext(snippet, context); return context;
};
const first=make('one'), second=make('two');
first.SAVED_MOVES.push({from_square:'e2',to_square:'e4'}); first.saveComputerGameState();
second.SAVED_MOVES.push({from_square:'d2',to_square:'d4'}); second.saveComputerGameState();
const reopened=make('one'); reopened.restoreComputerGameState();
assert.equal(reopened.SAVED_MOVES[0].to_square,'e4');
assert.equal(reopened.chat[0].text,'one');
assert.equal(make('three').SAVED_MOVES.length,0);
assert.equal(JSON.parse(store.get('account:1:bot:two')).moves[0].to_square,'d4');
store.set('account:1:bot:broken','invalid JSON');
assert.doesNotThrow(()=>make('broken').restoreComputerGameState());
assert.equal(first.meta.yourTurn,false);
console.log('Independent bots preserve moves and coach conversations; malformed state is handled safely.');
