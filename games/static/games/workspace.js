(() => {
    'use strict';
    const configNode = document.getElementById('game-workspace-config');
    if (!configNode) return;
    const config = JSON.parse(configNode.textContent);
    const words = config.words;
    const prefix = 'gchess-workspace-v1:' + config.actor + ':';
    const storage = window.sessionStorage;
    const read = (key, fallback) => { try { return JSON.parse(storage.getItem(prefix + key)) ?? fallback; } catch (_) { return fallback; } };
    const write = (key, value) => { try { storage.setItem(prefix + key, JSON.stringify(value)); return true; } catch (_) { return false; } };
    const validId = id => typeof id === 'string' && /^[a-zA-Z0-9_-]{1,80}$/.test(id);
    const requestedId = new URLSearchParams(location.search).get('bot');
    const botId = validId(requestedId) ? requestedId : 'main';
    const onHome = location.pathname === config.home;
    const key = prefix + 'bot:' + botId;
    let bots = read('bots', []);
    if (!Array.isArray(bots)) bots = [];
    bots = bots.filter(bot => bot && validId(bot.id));
    let humans = [];
    let failed = false;
    let refreshing = false;
    const panel = document.getElementById('workspace-panel');
    const toggle = document.getElementById('workspace-toggle');
    const list = document.getElementById('workspace-games');
    const bubble = document.getElementById('game-workspace');
    let drag = null;
    let suppressClick = false;
    function positionBubble(x, y) {
        const box = toggle.getBoundingClientRect();
        x = Math.max(8, Math.min(x, window.innerWidth - box.width - 8));
        y = Math.max(8, Math.min(y, window.innerHeight - box.height - 8));
        Object.assign(bubble.style, {left:x + 'px', top:y + 'px', right:'auto', bottom:'auto'});
        positionPanel();
        return {x, y};
    }
    function positionPanel() {
        if (panel.hidden) return;
        const box = toggle.getBoundingClientRect();
        const width = Math.min(345, window.innerWidth - 24);
        const below = window.innerHeight - box.bottom - 16;
        const above = box.top - 16;
        const opensBelow = below > above;
        panel.style.maxHeight = Math.max(80, opensBelow ? below : above) + 'px';
        panel.style.width = width + 'px';
        panel.style.left = Math.max(12, Math.min(box.right - width, window.innerWidth - width - 12)) + 'px';
        panel.style.right = 'auto';
        panel.style.top = opensBelow ? (box.bottom + 8) + 'px' : 'auto';
        panel.style.bottom = opensBelow ? 'auto' : (window.innerHeight - box.top + 8) + 'px';
    }
    toggle.addEventListener('pointerdown', event => {
        if (event.button !== 0 || !event.isPrimary) return;
        const rect = toggle.getBoundingClientRect();
        drag = {id:event.pointerId, x:event.clientX, y:event.clientY, left:rect.left, top:rect.top, moved:false};
        suppressClick = false;
        toggle.setPointerCapture(event.pointerId);
    });
    toggle.addEventListener('pointermove', event => {
        if (!drag || event.pointerId !== drag.id) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) < 6) return;
        drag.moved = true;
        bubble.classList.add('workspace-dragging');
        positionBubble(drag.left + dx, drag.top + dy);
    });
    function finishDrag(event) {
        if (!drag || event.pointerId !== drag.id) return;
        suppressClick = drag.moved;
        if (drag.moved) { const box = toggle.getBoundingClientRect(); write('position', {x:box.left, y:box.top}); }
        drag = null;
        bubble.classList.remove('workspace-dragging');
        if (toggle.hasPointerCapture(event.pointerId)) toggle.releasePointerCapture(event.pointerId);
    }
    toggle.addEventListener('pointerup', finishDrag);
    toggle.addEventListener('pointercancel', finishDrag);
    window.addEventListener('resize', () => {
        if (bubble.style.left) { const box = toggle.getBoundingClientRect(); positionBubble(box.left, box.top); }
        else positionPanel();
    });
    function registerBot(meta = {}) {
        let entry = bots.find(bot => bot.id === botId);
        if (!entry) { entry = {id:botId, number:Math.max(0, ...bots.map(bot => Number(bot.number) || 0)) + 1}; bots.push(entry); }
        Object.assign(entry, meta);
        write('bots', bots);
        render();
    }
    window.GChessWorkspace = {botStateKey:key, updateBot:registerBot};
    if (onHome) {
        // Claim the old singleton once, preserving an existing game without sharing it between accounts.
        try {
            if (botId === 'main' && !storage.getItem('gchess-workspace-legacy-owner')) {
                const legacy = storage.getItem('gchess-computer-game-state');
                if (legacy && !storage.getItem(key)) storage.setItem(key, legacy);
                storage.setItem('gchess-workspace-legacy-owner', config.actor);
            }
        } catch (_) {}
        registerBot();
    }
    function setOpen(open) {
        panel.hidden = !open;
        toggle.setAttribute('aria-expanded', String(open));
        write('open', open);
        positionPanel();
    }
    function section(label) { const heading = document.createElement('p'); heading.className = 'workspace-group'; heading.textContent = label; list.append(heading); }
    function card(url, title, subtitle, current, yourTurn) {
        const link = document.createElement('a'); link.href = url; link.className = 'workspace-game' + (yourTurn ? ' your-turn' : '');
        if (current) link.setAttribute('aria-current', 'page');
        const name = document.createElement('strong'); name.textContent = title;
        const detail = document.createElement('small'); detail.textContent = subtitle;
        link.addEventListener('click', event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            // Arrive at the selected board with the selector out of the way.
            setOpen(false);
        });
        link.append(name, detail); list.append(link);
    }
    function render() {
        list.replaceChildren();
        document.getElementById('workspace-count').textContent = String(humans.length + bots.length);
        if (bots.length) {
            section(words[12]);
            bots.forEach(bot => card(config.home + '?bot=' + encodeURIComponent(bot.id), 'Bot ' + bot.number + (bot.elo ? ' · ' + bot.elo : ''), bot.finished ? words[6] : (onHome && bot.id === botId ? (bot.yourTurn === false ? words[4] : words[3]) : words[5]), onHome && bot.id === botId, onHome && bot.id === botId && bot.yourTurn));
        }
        section(words[11]);
        humans.forEach(game => card(game.url, game.opponent || '—', words[game.yourTurn ? 3 : 4], location.pathname === game.url, game.yourTurn));
        if (!humans.length || failed) { const empty = document.createElement('p'); empty.textContent = failed ? words[9] : words[13]; list.append(empty); }
    }
    async function refresh() {
        if (refreshing || document.hidden) return;
        refreshing = true;
        try {
            const response = await fetch(config.endpoint, {cache:'no-store', headers:{Accept:'application/json'}});
            if (!response.ok) throw new Error('unavailable');
            const data = await response.json();
            if (data.actor !== config.actor || !Array.isArray(data.games)) throw new Error('identity changed');
            humans = data.games; failed = false;
        } catch (_) { failed = true; }
        finally { refreshing = false; render(); }
    }
    toggle.addEventListener('click', () => { if (suppressClick) { suppressClick = false; return; } setOpen(panel.hidden); if (!panel.hidden) refresh(); });
    document.getElementById('workspace-close').addEventListener('click', () => { setOpen(false); toggle.focus(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && !panel.hidden) { setOpen(false); toggle.focus(); } });
    document.getElementById('workspace-new-bot').addEventListener('click', () => {
        const id = 'bot-' + (window.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2));
        write('open', false);
        location.assign(config.home + '?bot=' + encodeURIComponent(id));
    });
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
    const savedPosition = read('position', null);
    if (savedPosition && Number.isFinite(savedPosition.x) && Number.isFinite(savedPosition.y)) positionBubble(savedPosition.x, savedPosition.y);
    setOpen(read('open', false)); render(); refresh();
    setInterval(refresh, 15000);
})();
