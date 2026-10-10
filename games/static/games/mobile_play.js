document.addEventListener('DOMContentLoaded', () => {
    const chat = document.querySelector('.home-computer-layout .trainer-chat');
    if (!chat) return;
    const disclosure = document.createElement('details');
    disclosure.className = 'mobile-coach-chat';
    const summary = document.createElement('summary');
    summary.textContent = chat.querySelector('h2')?.textContent || 'Coach';
    chat.before(disclosure);
    disclosure.append(summary, chat);
    const mobile = window.matchMedia('(max-width: 900px)');
    const sync = () => { disclosure.open = !mobile.matches; };
    sync();
    mobile.addEventListener('change', sync);

});


document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.home-computer-layout, .online-game-layout');
    const boardArea = layout?.querySelector('.board-area');
    if (!boardArea) return;
    const mobile = window.matchMedia('(max-width: 900px)');
    const language = document.documentElement.lang.slice(0, 2);
    const words = {es: 'Opciones de partida', pt: 'Opções da partida', en: 'Game options'};
    const strip = document.createElement('section');
    strip.className = 'mobile-play-strip';
    const state = document.createElement('div');
    state.className = 'mobile-play-state';
    state.setAttribute('aria-live', 'polite');
    const actions = document.createElement('div');
    actions.className = 'mobile-play-primary';
    strip.append(state, actions);
    boardArea.prepend(strip);
    const side = layout.querySelector('.computer-side, .online-side');
    const options = document.createElement('details');
    options.className = 'mobile-play-options';
    const summary = document.createElement('summary');
    summary.textContent = words[language] || words.pt;
    options.append(summary);
    const body = document.createElement('div');
    body.className = 'mobile-play-options-body';
    options.append(body);
    if (side) side.prepend(options);
    const transfers = [];
    const register = (selector, target) => {
        const element = layout.querySelector(selector);
        if (!element) return;
        const placeholder = document.createComment('mobile play original position');
        element.before(placeholder);
        transfers.push({element, placeholder, target});
    };
    register('#turn-indicator', state);
    register('#game-status', state);
    register('#game-clock', state);
    register('#toggle-coach', actions);
    register('#game-chat-toggle', actions);
    register('.coach-settings', body);
    register('#undo-computer-move', body);
    register('#reset-computer-game', body);

    register('#offer-draw-button', body);
    register('#resign-button', body);
    const sync = () => {
        for (const item of transfers) {
            if (mobile.matches) item.target.append(item.element);
            else item.placeholder.after(item.element);
        }
        const blindfold = layout.querySelector('#blindfold-panel');
        if (blindfold && blindfold.dataset.active !== 'true') {
            const host = mobile.matches ? body : (layout.querySelector('#computer-coach-panel') || side || boardArea);
            if (blindfold.parentElement !== host) host.prepend(blindfold);
        }
        strip.hidden = !mobile.matches;
        options.hidden = !mobile.matches;
        if (!mobile.matches) options.open = false;
    };
    sync();
    mobile.addEventListener('change', sync);
    new MutationObserver(sync).observe(document.body, {attributes: true, attributeFilter: ['class']});
});
