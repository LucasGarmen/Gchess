document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.home-computer-layout');
    const avatar = layout?.querySelector('[data-coach-player]');
    const form = document.getElementById('trainer-chat-form');
    const log = document.getElementById('trainer-chat-log');
    const comment = document.getElementById('coach-comment');
    if (!avatar || !form || !log) return;
    const lang = document.documentElement.lang.slice(0, 2);
    const words = {es: ['Chat con el coach', 'Cerrar consejo'], pt: ['Chat com o coach', 'Fechar conselho'], en: ['Chat with the coach', 'Close advice']}[lang] || ['Chat with the coach', 'Close advice'];
    const dock = document.createElement('section');
    dock.className = 'coach-chat-dock';
    dock.setAttribute('aria-label', words[0]);
    const handle = document.createElement('div');
    handle.className = 'coach-chat-handle';
    handle.textContent = words[0] + ' ⠿';
    dock.append(handle);
    const history = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = {es:'Historial', pt:'Histórico', en:'History'}[lang] || 'History';
    history.append(summary, log);
    dock.append(history, form);
    document.body.append(dock);
    const bubble = document.createElement('aside');
    bubble.className = 'board-coach-bubble';
    bubble.hidden = true;
    const close = document.createElement('button');
    close.type = 'button'; close.textContent = '×'; close.setAttribute('aria-label', words[1]);
    const text = document.createElement('div');
    text.setAttribute('role', 'status');
    const expand = document.createElement('button');
    expand.type = 'button'; expand.className = 'coach-reply-expand';
    const expandWords = {es:['Leer más','Ver menos'],pt:['Ler mais','Ver menos'],en:['Read more','Show less']}[lang] || ['Read more','Show less'];
    expand.textContent = expandWords[0];
    expand.setAttribute('aria-expanded', 'false');
    expand.addEventListener('click', () => {
        const opened = expand.getAttribute('aria-expanded') !== 'true';
        expand.setAttribute('aria-expanded', String(opened));
        expand.textContent = expandWords[opened ? 1 : 0];
        bubble.classList.toggle('coach-reply-expanded', opened); position();
    });
    bubble.append(close, text, expand);
    document.body.append(bubble);
    close.addEventListener('click', () => { bubble.hidden = true; position(); });
    const playing = () => document.body.classList.contains('mobile-bot-playing');
    const wrapper = avatar.closest('.board-wrapper');
    const replyArea = layout.querySelector('.computer-side');
    window.GchessChatDock?.bind(dock,handle);
    function position() {
        dock.hidden = !playing();
        const mobile = innerWidth <= 900;
        const fullscreen = dock.closest('.focus-play');
        if (mobile || fullscreen) dock.removeAttribute('style');

        bubble.classList.toggle('coach-reply-fullscreen', Boolean(fullscreen));
        bubble.classList.remove('coach-reply-reserved');
        wrapper?.style.setProperty('--coach-reply-top','0px');
        wrapper?.style.setProperty('--coach-reply-bottom','0px');
        if (!playing()) { bubble.hidden = true; return; }
        if (fullscreen) {
            // Native fullscreen only paints descendants of its fullscreen element.
            // Keep replies beside the composer, including replies arriving asynchronously.
            if (bubble.parentElement !== dock) dock.insertBefore(bubble, history);
            bubble.classList.remove('coach-reply-inline');
            bubble.removeAttribute('style');
            return;
        }
        if (bubble.hidden) return;
        const stage = avatar.closest('.board-player-stage');
        if (mobile && stage) {
            if (bubble.parentElement !== stage) stage.append(bubble);
            bubble.classList.add('coach-reply-inline');
            const portrait = avatar.getBoundingClientRect();
            const board = stage.getBoundingClientRect();
            bubble.style.width = Math.max(120,board.width-56)+'px';
            bubble.style.left = '0px';
            const height = bubble.getBoundingClientRect().height;
            const above = portrait.top < board.top;
            bubble.dataset.side = above ? 'above' : 'below';
            bubble.style.top = (above ? -height-8 : board.height+8)+'px';
            wrapper?.style.setProperty(above ? '--coach-reply-top' : '--coach-reply-bottom',Math.max(0,height-40)+'px');
        } else {
            const target = replyArea || dock;
            if (bubble.parentElement !== target) target.insertBefore(bubble, target.firstElementChild);
            bubble.classList.remove('coach-reply-inline');
            bubble.removeAttribute('style');
            bubble.classList.add('coach-reply-reserved');
        }
    }
    function show(value) {
        if (!playing() || !value.trim()) return;
        text.textContent = value.trim();
        expand.hidden = text.textContent.length < 420;
        expand.setAttribute('aria-expanded','false');
        expand.textContent = expandWords[0];
        bubble.classList.remove('coach-reply-expanded');
        bubble.hidden = false;
        position();
    }
    let lastReply = '';
    new MutationObserver(() => {
        const latest = log.lastElementChild;
        if (latest?.dataset.messageType === 'error') history.open = true;
        const last = [...log.querySelectorAll('.trainer-chat-message-trainer')].pop();
        if (last && last.textContent !== lastReply) { lastReply = last.textContent; show(lastReply); }
    }).observe(log, {childList:true, subtree:true, characterData:true});
    if (comment) new MutationObserver(() => { if (!comment.hidden) show(comment.textContent); }).observe(comment, {childList:true, subtree:true, characterData:true, attributes:true, attributeFilter:['hidden']});
    new MutationObserver(position).observe(document.body, {attributes:true, attributeFilter:['class']});
    const stage = avatar.closest('.board-player-stage');
    if (stage) new MutationObserver(position).observe(stage, {attributes:true, attributeFilter:['data-board-orientation']});
    document.addEventListener('gchess:focus-mode-changed', position);
    window.addEventListener('resize', position);
    window.visualViewport?.addEventListener('resize', position);
    document.addEventListener('scroll', position, {capture:true, passive:true});
    position();
});