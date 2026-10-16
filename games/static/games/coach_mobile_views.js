document.addEventListener('DOMContentLoaded', () => {
    const dock = document.querySelector('.coach-chat-dock');
    const board = document.querySelector('.home-computer-layout');
    if (!dock || !board) return;
    const lang = document.documentElement.lang.slice(0, 2);
    const words = {es:['Tablero','Chat con Gchess Bot','Vista de la partida'],pt:['Tabuleiro','Chat com Gchess Bot','Visualização da partida'],en:['Board','Chat with Gchess Bot','Game view']}[lang] || ['Board','Chat with Gchess Bot','Game view'];
    const media = matchMedia('(max-width: 900px)');
    const nav = document.createElement('div');
    nav.className = 'coach-mobile-views'; nav.setAttribute('role', 'group'); nav.setAttribute('aria-label', words[2]);
    const buttons = words.slice(0, 2).map((label, index) => {
        const button = document.createElement('button'); button.type = 'button';
        button.textContent = label; button.setAttribute('aria-pressed', String(index === 0));
        button.addEventListener('click', () => setView(index === 1, true));
        nav.append(button); return button;
    });
    let chat = false;
    function toggleClass(name, on) {
        if (document.body.classList.contains(name) !== on) document.body.classList.toggle(name, on);
    }
    function setView(next, focus = false) {
        chat = next;
        sync();
        if (focus) {
            if (chat) document.getElementById('trainer-chat-input')?.focus({preventScroll:true});
            else { document.getElementById('trainer-chat-input')?.blur(); buttons[0].focus({preventScroll:true}); }
        }
    }
    function viewport() {
        const visible = window.visualViewport;
        document.documentElement.style.setProperty('--coach-visible-top', ((visible?.offsetTop || 0) + 64) + 'px');
        document.documentElement.style.setProperty('--coach-keyboard-inset', Math.max(0, innerHeight - (visible?.height || innerHeight) - (visible?.offsetTop || 0)) + 'px');
    }
    function sync() {
        const active = media.matches && document.body.classList.contains('mobile-bot-playing');
        toggleClass('coach-mobile-views-active', active);
        toggleClass('coach-chat-view', active && chat);
        nav.hidden = !active;
        const host = document.querySelector('.focus-play') || document.body;
        if (nav.parentElement !== host) host.append(nav);
        buttons.forEach((button, index) => button.setAttribute('aria-pressed', String((index === 1) === chat)));
        if (active && chat) dock.querySelector('details').open = true;
        viewport();
    }
    media.addEventListener('change', sync);
    new MutationObserver(sync).observe(document.body, {attributes:true, attributeFilter:['class']});
    document.addEventListener('gchess:focus-mode-changed', sync);
    window.addEventListener('resize', viewport);
    window.visualViewport?.addEventListener('resize', viewport);
    window.visualViewport?.addEventListener('scroll', viewport);
    sync();
});
