const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

// Test request/retry behavior without a browser or a live Gemini request.
async function test() {
    function element() {
        return {
            children: [], dataset: {}, classList: {add() {}}, innerText: '',
            listeners: {}, appendChild(child) { this.children.push(child); },
            addEventListener(name, callback) { this.listeners[name] = callback; },
            focus() {},
        };
    }
    const log = element();
    const input = {...element(), value: 'e4 fue buena?'};
    const requests = [];
    const suggestion = {...element(), innerText: 'Que hago ahora?'};
    let moves = [{from: 'e2', to: 'e4'}];
    let result = {status: 'timeout', source: 'unavailable', answer: null,
        engine_analysis: 'e4: estimated loss 0.1', retryable: true};
    const sandbox = {
        window: {}, document: {
            getElementById: id => id === 'trainer-chat-log' ? log : input,
            createElement: element,
            querySelectorAll: () => [suggestion],
        }, AbortController, setTimeout, clearTimeout,
        fetch: async (url, request) => {
            requests.push(JSON.parse(request.body));
            return {ok: true, status: 200, json: async () => result};
        },
    };
    vm.runInNewContext(fs.readFileSync('games/static/games/trainer_conversation.js', 'utf8'), sandbox);
    const options = {moves: () => moves, color: 'white', language: 'es', csrf: () => '', setThinking() {}};
    await sandbox.window.GChessTrainerChat.ask(input.value, options);
    assert.equal(input.value, 'e4 fue buena?');
    assert.equal(log.children.filter(x => x.dataset.messageType === 'trainer').length, 0);
    assert.ok(log.children.find(x => x.dataset.messageType === 'engine').innerText.includes('no es una respuesta conversacional'));
    const retry = log.children.find(x => x.dataset.messageType === 'error').children[0];
    moves = [{from: 'e2', to: 'e4'}, {from: 'e7', to: 'e5'}];
    result = {status: 'ok', answer: 'e4 mantiene la evaluación.', topic: 'chess',
        fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', position_moves: ['e2e4']};
    await retry.listeners.click();
    assert.deepEqual(requests[0], requests[1], 'Retry must preserve original question, position and history');
    assert.equal(input.value, '');
    input.value = 'Por que?';
    await sandbox.window.GChessTrainerChat.ask(input.value, options);
    assert.deepEqual(requests[2].reference_moves, ['e2e4']);
    assert.equal(requests[2].history.length, 2, 'Failed turns and engine notices are not conversational answers');
    assert.equal(requests[2].history[1].role, 'assistant');
    input.value = 'Hablame del espacio';
    result = {status: 'quota', answer: null, engine_analysis: null};
    const before = log.children.filter(x => x.dataset.messageType === 'engine').length;
    await sandbox.window.GChessTrainerChat.ask(input.value, options);
    assert.equal(input.value, 'Hablame del espacio');
    assert.equal(log.children.filter(x => x.dataset.messageType === 'engine').length, before);
    suggestion.listeners.click();
    assert.equal(input.value, suggestion.innerText);
    assert.equal(requests.length, 4, 'Suggestions fill the field without sending a question');
    input.disabled = true;
    input.value = 'Mi propia pregunta';
    suggestion.listeners.click();
    assert.equal(input.value, 'Mi propia pregunta');
    console.log('Trainer client: preserved text, exact retry, historical position and separate engine fallback verified.');
}

module.exports = test;
if (require.main === module) test().catch(error => { console.error(error); process.exitCode = 1; });
