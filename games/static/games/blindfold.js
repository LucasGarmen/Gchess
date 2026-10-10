(() => {
    'use strict';
    const panel = document.getElementById('blindfold-panel');
    if (!panel || typeof SAVED_MOVES === 'undefined') return;
    const text = JSON.parse(document.getElementById('blindfold-texts').textContent);
    const workspace = JSON.parse(document.getElementById('game-workspace-config').textContent);
    const layout = panel.closest('.game-layout');
    const boardArea = layout.querySelector(".board-area");
    const side = layout.querySelector('.computer-side, .online-side');
    const toggle = document.getElementById('blindfold-toggle');
    const form = document.getElementById('blindfold-form');
    const input = document.getElementById('blindfold-move');
    const submit = document.getElementById('blindfold-submit');
    const notation = document.getElementById('blindfold-notation-language');
    const error = document.getElementById('blindfold-error');
    const history = document.getElementById('blindfold-history');
    const storageKey = GAME_ID ? 'gchess-blindfold:'+workspace.actor+':'+GAME_ID : (window.GChessWorkspace?.botStateKey || 'gchess-blindfold:coach')+':blindfold';
    let state = {};
    try { state = JSON.parse(sessionStorage.getItem(storageKey) || '{}') || {}; } catch (_) {}
    const query = new URLSearchParams(location.search);
    const exclusive = panel.dataset.exclusive === 'true' || (!GAME_ID && (state.exclusive === true || query.get('blindfold') === 'exclusive'));
    let active = exclusive || state.active === true;
    let busy = false;
    let lastHistoryKey = '';
    let historyController;
    let submitController;
    let lastBotMeta = '';
    notation.value = state.notation === 'en' ? 'en' : 'local';
    input.value = typeof state.draft === 'string' ? state.draft.slice(0,32) : '';

    function save() {
        try { sessionStorage.setItem(storageKey, JSON.stringify({active, exclusive, notation:notation.value, draft:input.value})); } catch (_) {}
    }
    function moveKey() { return JSON.stringify(SAVED_MOVES.map(move => [move.from,move.to,move.promotion])); }
    function canPlay() {
        return !busy && !gameOver && !analysisMode && !promotionPending && !botRequestLocked() &&
            !pendingMoveSaveCount && isViewingLatestPosition() && currentTurn === playerColor();
    }
    function applyVisibility() {
        if (exclusive && !gameOver) active = true;
        toggle.checked = active;
        toggle.disabled = (exclusive && !gameOver) || busy;
        layout.classList.toggle('blindfold-active', active);
        document.body.classList.toggle('blindfold-playing', active);
        document.body.classList.toggle('blindfold-exclusive-playing', exclusive && !gameOver);
        panel.dataset.active = String(active);
        document.getElementById('blindfold-play').hidden = !active;
        document.getElementById('blindfold-rule').textContent = exclusive ? text.exclusive_help : text.personal_help;
        const coachPanel = layout.querySelector('#computer-coach-panel');
        const mobileOptions = isMobileLayout() ? layout.querySelector('.mobile-play-options-body') : null;
        const host = active ? boardArea : (mobileOptions || coachPanel || side || boardArea);
        if (panel.parentElement !== host) host.prepend(panel);
        const menu = document.getElementById('mobile-nav-toggle');
        if (active && menu && isMobileLayout()) {
            const slot = document.getElementById('blindfold-nav-slot');
            if (menu.parentElement !== slot) slot.append(menu);
        }
        else if (menu?.parentElement?.id === 'blindfold-nav-slot') {
            if (isMobileLayout()) mountMobileNavToggleInBoardToolbar();
            else document.body.insertBefore(menu, document.body.firstChild);
        }
        const meta = String(active)+':'+String(exclusive);
        if (!GAME_ID && window.GChessWorkspace && lastBotMeta !== meta) {
            lastBotMeta = meta;
            window.GChessWorkspace.updateBot({blindfold:active,blindfoldExclusive:exclusive});
        }
    }
    function renderHistory(moves) {
        history.replaceChildren();
        for (let index=0; index<moves.length; index+=2) {
            const row = document.createElement('li');
            row.textContent = moves[index]+(moves[index+1] ? '   '+moves[index+1] : '');
            history.append(row);
        }
        document.getElementById('blindfold-empty').hidden = moves.length > 0;
        history.scrollTop = history.scrollHeight;
    }
    async function request(payload, signal) {
        const response = await fetch(panel.dataset.endpoint, {
            method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCSRFToken()},
            body:JSON.stringify(payload), signal,
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || text.network);
        return data;
    }
    function payload() {
        return GAME_ID ? {game_id:GAME_ID,notation_language:notation.value} : {moves:SAVED_MOVES,notation_language:notation.value};
    }
    async function refreshHistory(key) {
        historyController?.abort();
        historyController = new AbortController();
        const controller = historyController;
        const timer = setTimeout(() => controller.abort(), 15000);
        try {
            const data = await request(payload(),controller.signal);
            if (key !== moveKey()+':'+notation.value) return;
            if (data.move_count !== SAVED_MOVES.length) {
                lastHistoryKey = '';
                if (GAME_ID) await syncMovesFromServer({source:'blindfold-history'});
                return;
            }
            renderHistory(data.history);
        } catch (failure) {
            if (failure.name !== 'AbortError') error.textContent = failure.message;
            // The typed draft is preserved, and a new move/toggle can retry history.
        } finally { clearTimeout(timer); }
    }
    function sync() {
        if (document.hidden) return;
        applyVisibility();
        if (!active) return;
        input.disabled = gameOver;
        submit.disabled = !canPlay();
        const status = gameOver ? text.finished : (currentTurn === playerColor() ? text.turn : text.waiting);
        const turnLabel = currentTurn === 'white' ? window.UI_TEXTS.turn_white : window.UI_TEXTS.turn_black;
        const turn = document.getElementById('blindfold-turn');
        const label = status+(turnLabel && !gameOver ? ' · '+turnLabel : '');
        if (turn.textContent !== label) turn.textContent = label;
        const key = moveKey()+':'+notation.value;
        if (key !== lastHistoryKey) { lastHistoryKey = key; refreshHistory(key); }
    }
    toggle.addEventListener('change', () => {
        if (exclusive && !gameOver) return;
        if (analysisMode) document.getElementById('toggle-analysis-mode')?.click();
        if (!isViewingLatestPosition()) document.getElementById('last-move')?.click();
        active = toggle.checked;
        lastHistoryKey = '';
        if (active) { clearSelection(); clearQueuedMove(); }
        save(); sync();
    });
    notation.addEventListener('change', () => { error.textContent=''; save(); lastHistoryKey=''; sync(); });
    input.addEventListener('input', save);
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (!canPlay()) return;
        const draft = input.value.trim();
        if (!draft) return;
        const key = moveKey();
        const color = playerColor();
        busy = true; error.textContent=''; sync();
        submitController = new AbortController();
        const timer = setTimeout(() => submitController.abort(),15000);
        try {
            const data = await request({...payload(),notation:draft},submitController.signal);
            clearTimeout(timer);
            if (key !== moveKey() || data.move_count !== SAVED_MOVES.length || color !== playerColor()) {
                if (GAME_ID) await syncMovesFromServer({source:'blindfold-stale'});
                throw new Error(text.changed);
            }
            if (gameOver || botRequestLocked() || currentTurn !== color) throw new Error(text.changed);
            const from = getSquare(data.move.from), to = getSquare(data.move.to);
            if (!from || !to || !canPlayerMoveFrom(from) || !isLegalMove(from,to)) throw new Error(text.changed);
            input.value=''; save();
            await playMove(from,to,false,data.move.promotion);
        } catch (failure) {
            if (!input.value) input.value=draft;
            error.textContent=failure.name === 'AbortError' ? text.network : failure.message;
            save();
        } finally { clearTimeout(timer); busy=false; sync(); if (!gameOver) input.focus(); }
    });
    window.addEventListener('resize', applyVisibility);
    document.addEventListener('visibilitychange',sync);
    const interval = setInterval(sync,500);
    window.addEventListener('pagehide',()=>{ save(); clearInterval(interval); historyController?.abort(); submitController?.abort(); });
    applyVisibility(); save(); sync();
})();
