(function () {
    const colorSelect = document.getElementById('trainer-player-color');
    if (colorSelect) {
        colorSelect.addEventListener('change', () => { PLAYER_COLOR = colorSelect.value; });
    }
    const form = document.getElementById('trainer-chat-form');

    if (!form || form.dataset.trainerChatBound === 'true') {
        return;
    }

    const input = document.getElementById('trainer-chat-input');
    const submitButton = document.getElementById('trainer-chat-submit');
    const log = document.getElementById('trainer-chat-log');
    let thinking = false;

    function uiText(key, fallback) {
        return typeof UI_TEXTS !== 'undefined' && UI_TEXTS[key] ? UI_TEXTS[key] : fallback;
    }

    function csrfToken() {
        const cookies = document.cookie.split(';');

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }

        return '';
    }

    function currentMoves() {
        if (typeof SAVED_MOVES === 'undefined' || !Array.isArray(SAVED_MOVES)) {
            return [];
        }

        const index = typeof historyIndex === 'number' ? historyIndex : SAVED_MOVES.length;
        return SAVED_MOVES.slice(0, index);
    }

    function addMessage(message, type) {
        if (!log) {
            return;
        }

        const item = document.createElement('div');
        item.classList.add('trainer-chat-message', `trainer-chat-message-${type}`);
        item.dataset.messageType = type;
        item.innerText = message;
        log.appendChild(item);
        log.scrollTop = log.scrollHeight;
    }

    function updateControls() {
        if (log) log.setAttribute('aria-busy', String(thinking));
        if (submitButton) {
            submitButton.disabled = thinking;
            submitButton.innerText = thinking ? uiText('thinking', 'Pensando...') : uiText('ask', 'Perguntar');
        }

        if (input) {
            input.disabled = thinking;
        }
    }

    async function askCoach(question) {
        return window.GChessTrainerChat.ask(question, {
            moves: currentMoves, color: typeof PLAYER_COLOR !== 'undefined' ? PLAYER_COLOR : 'white',
            language: typeof UI_LANGUAGE !== 'undefined' ? UI_LANGUAGE : 'pt',
            csrf: csrfToken,
            setThinking: value => { thinking = value; updateControls(); },
        });
    }

    function submitQuestion() {
        const question = input ? input.value.trim() : '';

        if (!question || thinking) {
            return;
        }

        askCoach(question);
    }

    form.dataset.trainerChatBound = 'fallback';
    form.addEventListener('submit', function (event) {
        event.preventDefault();
        submitQuestion();
    });

    if (input) {
        input.addEventListener('keydown', function (event) {
            if (event.key !== 'Enter' || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
                return;
            }

            event.preventDefault();
            submitQuestion();
        });
    }
}());
