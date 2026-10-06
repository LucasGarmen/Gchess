const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

function test() {
    const source = fs.readFileSync('games/static/games/board.js', 'utf8');
    const elements = {};
    for (const id of ['home-open-bot', 'home-start-play', 'board', 'mobile-bot-setup', 'mobile-computer-elo', 'mobile-start-bot-game']) {
        elements[id] = {hidden: true, listeners: {}, addEventListener(event, fn) { this.listeners[event] = fn; },
            focus() { this.focused = true; }, scrollIntoView() { this.scrolled = true; }};
    }
    const form = {hidden: true};
    let setupOpened = false, optionsSynced = false, gameOpened = false;
    const sandbox = {
        document: {getElementById: id => elements[id]},
        isHomeComputerGame: () => true, analyzeGameForm: form, gameOver: false,
        pgnPanel: null, computerCoachPanel: null,
        mobileHomeElements: () => ({startButton: elements['mobile-start-bot-game'], setupPanel: elements['mobile-bot-setup']}),
        showMobileBotSetup() { setupOpened = true; elements['mobile-bot-setup'].hidden = false; },
        syncMobileBotOptions() { optionsSynced = true; }, showMobileBotGame() { gameOpened = true; },
        isMobileLayout: () => true, mountMobileNavToggleInBoardToolbar() {},
    };
    const extract = (start, end) => source.slice(source.indexOf(start), source.indexOf(end, source.indexOf(start)));
    vm.runInNewContext(extract('function updateFinishedPanelState()', 'function initialPieceCounts()') +
        extract('function initMobileGameNavigation()', 'async function askTrainerChat('), sandbox);
    sandbox.initMobileGameNavigation();
    elements['home-open-bot'].listeners.click();
    assert.equal(setupOpened, true);
    assert.equal(elements['mobile-bot-setup'].hidden, false);
    assert.equal(elements['mobile-computer-elo'].focused, true);
    elements['mobile-start-bot-game'].listeners.click();
    assert.ok(optionsSynced && gameOpened, 'Mobile CTA must retain existing game setup');
    sandbox.updateFinishedPanelState();
    assert.equal(form.hidden, true);
    sandbox.gameOver = true;
    sandbox.updateFinishedPanelState();
    assert.equal(form.hidden, false, 'Finished game analysis must be reachable without switching tabs');
    sandbox.gameOver = false;
    sandbox.updateFinishedPanelState();
    assert.equal(form.hidden, true);
    console.log('Onboarding: desktop/mobile entry and finished analysis visibility verified.');
}
module.exports = test;
if (require.main === module) test();
