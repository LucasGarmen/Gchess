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
    const history = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = words[0];
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
    bubble.append(close, text);
    document.body.append(bubble);
    close.addEventListener('click', () => { bubble.hidden = true; });
    const playing = () => document.body.classList.contains('mobile-bot-playing');
    function position() {
        dock.hidden = !playing();
        if (!playing()) { bubble.hidden = true; return; }
        if (bubble.hidden) return;
        const box = avatar.getBoundingClientRect();
        const width = Math.min(300, innerWidth - 24);
        bubble.style.width = width + 'px';
        bubble.style.left = Math.max(12, Math.min(innerWidth <= 900 ? box.left - width - 10 : box.right + 10, innerWidth - width - 12)) + 'px';
        const height = bubble.getBoundingClientRect().height;
        bubble.style.top = Math.max(68, Math.min(innerWidth <= 900 ? box.top - height - 8 : box.top, dock.getBoundingClientRect().top - height - 12)) + 'px';
    }
    function show(value) {
        if (!playing() || !value.trim()) return;
        text.textContent = value.trim();
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
    window.addEventListener('resize', position);
    window.visualViewport?.addEventListener('resize', position);
    document.addEventListener('scroll', position, {capture:true, passive:true});
    position();
});