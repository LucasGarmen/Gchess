const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

async function testArtifact(filename) {
    const source = fs.readFileSync(filename, 'utf8');
    const start = source.indexOf('async function requestCoachAnalysis(');
    const end = Math.min(...["document.getElementById('prev-move')", 'document.getElementById("prev-move")', 'restoreComputerGameState()'].map(marker => source.indexOf(marker, start)).filter(index => index >= 0));
    assert.ok(start >= 0 && Number.isFinite(end), 'Coach test boundaries must exist in both artifacts');
    const timers = new Map();
    const comments = [];
    let rejectFetch;
    let nextTimer = 0;
    const sandbox = {
        SAVED_MOVES: [{from:'e2',to:'e4'}], coachAnalysisKey: () => 'first',
        shouldRunCoachAnalysisForSnapshot: () => true, lastCoachAnalysisCompletedKey:'',
        coachAnalysisRequestKey:'', coachAnalysisAbortController:null, isCoachAnalysisLoading:false,
        createAbortControllerIfAvailable: () => new AbortController(),
        cancelCoachAnalysisRequest() {}, setCoachComment: text => comments.push(text),
        uiText: (key,text) => text, neutralCoachFallbackComment: () => 'move recorded',
        playerColor: () => 'white', currentUiLanguage: () => 'es', getCSRFToken: () => '',
        setTimeout: fn => {const id=++nextTimer; timers.set(id,fn); return id;}, clearTimeout: id => timers.delete(id),
        fetch: (url,options) => new Promise((resolve,reject) => {
            rejectFetch=reject;
            options.signal.addEventListener('abort',()=>reject(Object.assign(new Error('timeout'),{name:'AbortError'})));
        }), console:{error(){}},
    };
    vm.createContext(sandbox);
    vm.runInContext(source.slice(start,end),sandbox);
    const first = sandbox.requestCoachAnalysis('first');
    sandbox.coachAnalysisRequestKey='newer';
    rejectFetch(new Error('old network error'));
    await first;
    assert.equal(comments.length,1,'An old failure must not replace the newer commentary');
    assert.equal(sandbox.coachAnalysisRequestKey,'newer');
    assert.equal(timers.size,0);

    sandbox.isCoachAnalysisLoading=false;
    sandbox.coachAnalysisRequestKey='';
    const second = sandbox.requestCoachAnalysis('second');
    Array.from(timers.values())[0]();
    await second;
    assert.equal(comments.at(-1),'move recorded');
    assert.equal(sandbox.isCoachAnalysisLoading,false,'A timeout must release the coach request');
    assert.equal(timers.size,0);

    const third = sandbox.requestCoachAnalysis('repeated');
    sandbox.coachAnalysisAbortController = new AbortController();
    const commentCount = comments.length;
    rejectFetch(new Error('old failure for the same board'));
    await third;
    assert.equal(comments.length,commentCount,'A canceled request cannot overwrite a replacement for the same board');
    assert.equal(sandbox.coachAnalysisRequestKey,'repeated');
    assert.equal(timers.size,0);

    const positionStart = source.indexOf('function trainerChatMoves()');
    const positionEnd = source.indexOf('function trainerChatLogState()',positionStart);
    const positions = {SAVED_MOVES:['e2e4','e7e5'],historyIndex:1,ANALYZER_MODE:false,isViewingLatestPosition:()=>false};
    vm.createContext(positions);
    vm.runInContext(source.slice(positionStart,positionEnd),positions);
    assert.deepEqual(Array.from(positions.trainerChatMoves()),['e2e4'],'Chat must use the visible historical board');
    positions.isViewingLatestPosition=()=>true;
    assert.deepEqual(Array.from(positions.trainerChatMoves()),['e2e4','e7e5']);
}

(async()=>{
    for(const path of ['games/static/games/board.js','games/static/games/board.min.js']) await testArtifact(path);
    console.log('Coach: historical positions, stale errors, timeout and request cleanup verified in both browser artifacts.');
})().catch(error=>{console.error(error);process.exitCode=1;});
