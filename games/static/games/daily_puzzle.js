(function () {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const pieceTypes = {
        p: 'pawn',
        n: 'horse',
        b: 'bishop',
        r: 'rook',
        q: 'queen',
        k: 'king',
    };
    const pieceTypeByPromotion = {
        q: 'queen',
        r: 'rook',
        b: 'bishop',
        n: 'horse',
    };

    const boardElement = document.getElementById('daily-board');
    const boardArea = document.getElementById('daily-board-area');
    const startButton = document.getElementById('daily-start');
    const statusElement = document.getElementById('daily-status');
    const resultElement = document.getElementById('daily-result');
    const resultLabel = document.getElementById('daily-result-label');
    const timerElement = document.getElementById('daily-timer');
    const rankLabels = document.getElementById('daily-rank-labels');
    const fileLabels = document.getElementById('daily-file-labels');

    if (!boardElement) {
        return;
    }

    let puzzle = parseJsonScript('daily-puzzle-data', {});
    let attempt = parseJsonScript('daily-attempt-data', null);
    let status = parseJsonScript('daily-status-data', 'not_started');
    let currentFen = puzzle.fen || '';
    let currentPosition = parseFen(currentFen);
    let currentLegalMovesByFrom = normalizeLegalMovesByFrom(puzzle.legal_moves);
    let playedLine = Array.isArray(puzzle.played_line) ? puzzle.played_line : [];
    let orientation = puzzle.turn || currentPosition.turn;
    let selectedSquare = null;
    let possibleMoves = [];
    let pendingMove = false;
    let completed = Boolean(attempt && attempt.completed);
    let timerStartedAt = null;
    let timerIntervalId = null;

    function parseJsonScript(id, fallbackValue) {
        const element = document.getElementById(id);
        if (!element) {
            return fallbackValue;
        }

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            console.warn('No se pudo leer JSON del puzzle diario:', error);
            return fallbackValue;
        }
    }

    function uiText(key, fallback) {
        if (window.UI_TEXTS && window.UI_TEXTS[key]) {
            return window.UI_TEXTS[key];
        }

        return fallback;
    }

    function getCSRFToken() {
        const cookies = document.cookie.split(';');

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }

        return '';
    }

    function elapsedMilliseconds() {
        if (!timerStartedAt) {
            return attempt && Number.isInteger(attempt.elapsed_ms) ? attempt.elapsed_ms : 0;
        }

        return Math.max(0, Date.now() - timerStartedAt);
    }

    function formatTime(milliseconds) {
        const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        if (minutes > 0) {
            return `${minutes}m ${String(seconds).padStart(2, '0')}s`;
        }

        return `${seconds}s`;
    }

    function startTimer(initialMilliseconds) {
        const elapsed = Number(initialMilliseconds) || 0;
        timerStartedAt = Date.now() - elapsed;
        timerElement.innerText = formatTime(elapsed);

        if (timerIntervalId) {
            clearInterval(timerIntervalId);
        }

        timerIntervalId = setInterval(function () {
            timerElement.innerText = formatTime(elapsedMilliseconds());
        }, 500);
    }

    function stopTimer(finalTime) {
        if (timerIntervalId) {
            clearInterval(timerIntervalId);
            timerIntervalId = null;
        }

        timerStartedAt = null;

        if (finalTime) {
            timerElement.innerText = finalTime;
        }
    }

    function parseFen(fen) {
        const [placement, turnToken] = (fen || '').split(' ');
        const pieces = {};
        let rank = 8;
        let fileIndex = 0;

        for (const char of placement || '') {
            if (char === '/') {
                rank -= 1;
                fileIndex = 0;
                continue;
            }

            if (/\d/.test(char)) {
                fileIndex += Number(char);
                continue;
            }

            const color = char === char.toUpperCase() ? 'white' : 'black';
            const type = pieceTypes[char.toLowerCase()];
            const coord = `${files[fileIndex]}${rank}`;

            pieces[coord] = { color, type };
            fileIndex += 1;
        }

        return {
            pieces,
            turn: turnToken === 'b' ? 'black' : 'white',
        };
    }

    function normalizeLegalMovesByFrom(movesByFrom) {
        if (!movesByFrom || typeof movesByFrom !== 'object' || Array.isArray(movesByFrom)) {
            return {};
        }

        return Object.entries(movesByFrom).reduce((normalized, [from, moves]) => {
            normalized[from] = Array.isArray(moves) ? moves : [];
            return normalized;
        }, {});
    }

    function squareSequence() {
        const ranks = orientation === 'black'
            ? [1, 2, 3, 4, 5, 6, 7, 8]
            : [8, 7, 6, 5, 4, 3, 2, 1];
        const orderedFiles = orientation === 'black' ? [...files].reverse() : files;
        const squares = [];

        ranks.forEach(rank => {
            orderedFiles.forEach(file => {
                squares.push(`${file}${rank}`);
            });
        });

        return squares;
    }

    function updateBoardLabels() {
        const ranks = orientation === 'black'
            ? ['1', '2', '3', '4', '5', '6', '7', '8']
            : ['8', '7', '6', '5', '4', '3', '2', '1'];
        const orderedFiles = orientation === 'black' ? [...files].reverse() : files;

        Array.from(rankLabels.children).forEach((label, index) => {
            label.innerText = ranks[index];
        });

        Array.from(fileLabels.children).forEach((label, index) => {
            label.innerText = orderedFiles[index];
        });
    }

    function renderBoard() {
        currentPosition = parseFen(currentFen);
        updateBoardLabels();
        boardElement.replaceChildren();

        squareSequence().forEach(coord => {
            const square = document.createElement('div');
            const fileIndex = files.indexOf(coord[0]);
            const rank = Number(coord[1]);
            const piece = currentPosition.pieces[coord];
            const isLight = (fileIndex + rank) % 2 === 0;

            square.className = `square ${isLight ? 'square-light' : 'square-dark'}`;
            square.dataset.coord = coord;

            if (coord === selectedSquare) {
                square.classList.add('selected');
            }

            if (possibleMoves.some(move => move.to === coord)) {
                square.classList.add('possible-move');
            }

            if (piece) {
                square.appendChild(createPieceElement(piece));
            }

            square.addEventListener('click', function () {
                handleSquareClick(coord);
            });
            boardElement.appendChild(square);
        });
    }

    function createPieceElement(piece) {
        const image = document.createElement('img');
        const pieceKey = `${piece.type}_${piece.color}`;

        image.src = `${window.DAILY_PIECES_BASE_URL || '/static/games/pieces/'}${pieceKey}.png`;
        image.alt = pieceKey;
        image.className = 'piece';
        image.decoding = 'async';
        image.draggable = false;
        return image;
    }

    function canSelectSquare(coord) {
        if (completed || pendingMove) {
            return false;
        }

        const piece = currentPosition.pieces[coord];
        return Boolean(piece && piece.color === puzzle.turn && currentPosition.turn === puzzle.turn);
    }

    function handleSquareClick(coord) {
        if (completed || pendingMove) {
            return;
        }

        if (!selectedSquare) {
            selectSquare(coord);
            return;
        }

        if (selectedSquare === coord) {
            clearSelection();
            renderBoard();
            return;
        }

        if (canSelectSquare(coord)) {
            selectSquare(coord);
            return;
        }

        if (!possibleMoves.some(move => move.to === coord)) {
            clearSelection();
            renderBoard();
            return;
        }

        submitMove(selectedSquare, coord);
    }

    function selectSquare(coord) {
        if (!canSelectSquare(coord)) {
            return;
        }

        selectedSquare = coord;
        possibleMoves = currentLegalMovesByFrom[coord] || [];
        renderBoard();
    }

    function clearSelection() {
        selectedSquare = null;
        possibleMoves = [];
    }

    function buildUciMove(from, to) {
        const piece = currentPosition.pieces[from];
        const promotion = piece &&
            piece.type === 'pawn' &&
            ((piece.color === 'white' && to[1] === '8') || (piece.color === 'black' && to[1] === '1'))
            ? 'q'
            : '';

        return `${from}${to}${promotion}`;
    }

    async function startDailyPuzzle() {
        startButton.disabled = true;

        try {
            const response = await fetch(window.DAILY_START_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                statusElement.innerText = data.error || uiText('daily_already_completed', 'Already completed.');
                startButton.disabled = false;
                return;
            }

            puzzle = data.puzzle || puzzle;
            attempt = data.attempt || attempt;
            status = data.status || 'in_progress';
            completed = Boolean(attempt && attempt.completed);
            currentFen = puzzle.fen;
            currentLegalMovesByFrom = normalizeLegalMovesByFrom(puzzle.legal_moves);
            playedLine = Array.isArray(puzzle.played_line) ? puzzle.played_line : [];
            orientation = puzzle.turn || parseFen(currentFen).turn;
            boardArea.hidden = completed;
            startButton.hidden = true;

            if (completed) {
                completeDaily(attempt.resultado, attempt.tiempo, uiText('daily_already_completed', 'Already completed.'));
                return;
            }

            statusElement.innerText = uiText('daily_in_progress', 'Solve today\'s puzzle.');
            startTimer(attempt ? attempt.elapsed_ms : 0);
            renderBoard();
        } catch (error) {
            console.error('No se pudo iniciar el puzzle diario:', error);
            statusElement.innerText = uiText('practice_review_error', 'The move could not be reviewed.');
            startButton.disabled = false;
        }
    }

    async function submitMove(from, to) {
        pendingMove = true;
        clearSelection();
        statusElement.innerText = uiText('thinking', 'Pensando...');

        try {
            const response = await fetch(window.DAILY_MOVE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    move: buildUciMove(from, to),
                    elapsed_ms: elapsedMilliseconds(),
                    played_line: playedLine,
                }),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok && !data.completed) {
                statusElement.innerText = data.error || uiText('practice_review_error', 'The move could not be reviewed.');
                return;
            }

            currentFen = data.fen || currentFen;
            playedLine = Array.isArray(data.played_line) ? data.played_line : playedLine;
            currentLegalMovesByFrom = normalizeLegalMovesByFrom(data.legal_moves);

            if (data.completed) {
                renderBoard();
                completeDaily(data.result, data.time, data.message);
                return;
            }

            statusElement.innerText = data.message || uiText('daily_continue', 'Correct, keep following the line.');
            renderBoard();
        } catch (error) {
            console.error('No se pudo validar el puzzle diario:', error);
            statusElement.innerText = uiText('practice_review_error', 'The move could not be reviewed.');
        } finally {
            pendingMove = false;
        }
    }

    function completeDaily(result, time, message) {
        completed = true;
        stopTimer(time);
        boardArea.hidden = true;
        startButton.hidden = true;
        resultElement.hidden = false;
        resultLabel.innerText = result === 'correct'
            ? uiText('daily_correct', 'Correct!')
            : uiText('daily_incorrect', 'Incorrect.');
        resultElement.innerText = `${message || resultLabel.innerText} ${time || ''}. ${uiText('daily_back_tomorrow', 'Come back tomorrow for a new puzzle.')}`;
        statusElement.innerText = uiText('daily_back_tomorrow', 'Come back tomorrow for a new puzzle.');
    }

    if (attempt && attempt.completed) {
        timerElement.innerText = attempt.tiempo || '0s';
    }

    if (status === 'in_progress') {
        boardArea.hidden = false;
        startButton.hidden = true;
        statusElement.innerText = uiText('daily_in_progress', 'Solve today\'s puzzle.');
        startTimer(attempt ? attempt.elapsed_ms : 0);
        renderBoard();
    }

    if (startButton) {
        startButton.addEventListener('click', startDailyPuzzle);
    }
}());
