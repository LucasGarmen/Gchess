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
    bubble.append(close, text);
    document.body.append(bubble);
    close.addEventListener('click', () => { bubble.hidden = true; position(); });
    const playing = () => document.body.classList.contains('mobile-bot-playing');
    let drag = null;
    let desktopPosition = null;
    const wrapper = avatar.closest('.board-wrapper');
    function moveDock(x, y) {
        const rect = dock.getBoundingClientRect();
        desktopPosition = {x:Math.max(8,Math.min(x,innerWidth-rect.width-8)), y:Math.max(8,Math.min(y,innerHeight-rect.height-8))};
        Object.assign(dock.style,{left:desktopPosition.x+'px',top:desktopPosition.y+'px',right:'auto',bottom:'auto'});
    }
    handle.addEventListener('pointerdown', event => {
        if (innerWidth <= 900 || event.button !== 0 || !event.isPrimary) return;
        const rect = dock.getBoundingClientRect();
        drag = {id:event.pointerId,x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};
        handle.setPointerCapture(event.pointerId);
    });
    handle.addEventListener('pointermove', event => {
        if (!drag || event.pointerId !== drag.id) return;
        moveDock(drag.left+event.clientX-drag.x,drag.top+event.clientY-drag.y);
    });
    const endDrag = event => { if (drag?.id === event.pointerId) {drag=null;if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);} };
    handle.addEventListener('pointerup',endDrag);
    handle.addEventListener('pointercancel',endDrag);
    function position() {
        dock.hidden = !playing();
        const mobile = innerWidth <= 900;
        if (mobile) dock.removeAttribute('style');
        else if (desktopPosition) moveDock(desktopPosition.x,desktopPosition.y);
        wrapper?.style.setProperty('--coach-reply-top','0px');
        wrapper?.style.setProperty('--coach-reply-bottom','0px');
        if (!playing()) { bubble.hidden = true; return; }
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
            if (bubble.parentElement !== document.body) document.body.append(bubble);
            bubble.classList.remove('coach-reply-inline');
            const box = avatar.getBoundingClientRect();
            const width = Math.min(240,Math.max(150,innerWidth-box.right-24));
            bubble.style.width = width+'px';
            bubble.style.left = Math.min(box.right+8,innerWidth-width-12)+'px';
            const height = bubble.getBoundingClientRect().height;
            bubble.style.top = Math.max(12,Math.min(box.top,innerHeight-height-110))+'px';
        }
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