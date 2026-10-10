document.addEventListener('DOMContentLoaded', () => {
    const openGameChat = () => {
        if (location.hash === '#game-chat-panel' && document.getElementById('game-chat-panel')?.hidden) document.getElementById('game-chat-toggle')?.click();
    };
    openGameChat();
    window.addEventListener('hashchange', openGameChat);
    const contacts = [...document.querySelectorAll('.nav-contact-detail')];
    const close = (except = null) => contacts.forEach(item => { if (item !== except) item.open = false; });
    contacts.forEach(item => item.addEventListener('toggle', () => { if (item.open) { close(item); if (item.classList.contains('nav-player-chat')) loadConversations(); } }));
    async function loadConversations() {
        const list = document.getElementById('nav-player-conversations');
        const config = document.getElementById('game-workspace-config');
        if (!list || !config) return;
        const message = text => { const p = document.createElement('p'); p.textContent = text; list.replaceChildren(p); };
        message(list.dataset.empty);
        try {
            const response = await fetch(JSON.parse(config.textContent).endpoint, {cache:'no-store',headers:{Accept:'application/json'}});
            if (!response.ok) throw new Error('unavailable');
            const data = await response.json();
            if (!Array.isArray(data.games)) throw new Error('invalid');
            if (!data.games.length) return;
            list.replaceChildren();
            data.games.forEach(game => {
                const a = document.createElement('a'); a.href = game.url + '#game-chat-panel'; a.textContent = game.opponent || 'Chat'; list.append(a);
            });
        } catch (_) { message(list.dataset.error); }
    }
    document.addEventListener('click', event => { if (!event.target.closest('.nav-contact-links')) close(); });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        const active = contacts.find(item => item.open);
        if (active) { close(); active.querySelector('summary').focus(); }
    });
});