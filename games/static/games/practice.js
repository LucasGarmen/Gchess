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
    const progressKey = 'gchess-practice-progress-v1';
    const practiceDragPieceScale = 1.7;

    const boardElement = document.getElementById('practice-board');
    const levelButtons = Array.from(document.querySelectorAll('[data-practice-level]'));
    const titleElement = document.getElementById('practice-puzzle-title');
    const metaElement = document.getElementById('practice-puzzle-meta');
    const statusElement = document.getElementById('practice-status');
    const resultElement = document.getElementById('practice-result');
    const hintElement = document.getElementById('practice-hint');
    const lineElement = document.getElementById('practice-line');
    const solvedCountElement = document.getElementById('practice-solved-count');
    const errorCountElement = document.getElementById('practice-error-count');
    const accuracyElement = document.getElementById('practice-accuracy');
    const nextButton = document.getElementById('practice-next-puzzle');
    const restartButton = document.getElementById('practice-restart');
    const hintButton = document.getElementById('practice-show-hint');
    const flipButton = document.getElementById('practice-flip-board');
    const rankLabels = document.getElementById('practice-rank-labels');
    const fileLabels = document.getElementById('practice-file-labels');

    if (!boardElement) {
        return;
    }

    const levels = parseJsonScript('practice-levels-data', []);
    const puzzles = parseJsonScript('practice-puzzles-data', []);

    let currentLevel = levels.length > 0 ? levels[0].key : 'easy';
    let currentPuzzleIndex = 0;
    let currentPuzzle = null;
    let currentFen = '';
    let currentPosition = { pieces: {}, turn: 'white' };
    let selectedSquare = null;
    let possibleMoves = [];
    let possibleMovesLoaded = false;
    let playedLine = [];
    let solved = false;
    let pendingMove = false;
    let orientation = 'white';
    let lineMoves = [];
    let progress = loadProgress();
    let dragState = null;
    let suppressNextClick = false;

    function parseJsonScript(id, fallbackValue) {
        const element = document.getElementById(id);
        if (!element) {
            return fallbackValue;
        }

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            console.warn('No se pudo leer JSON de practica:', error);
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

    function loadProgress() {
        try {
            const stored = JSON.parse(localStorage.getItem(progressKey) || '{}');

            return {
                solvedIds: Array.isArray(stored.solvedIds) ? stored.solvedIds : [],
                errors: Number.isInteger(stored.errors) ? stored.errors : 0,
            };
        } catch (error) {
            return { solvedIds: [], errors: 0 };
        }
    }

    function saveProgress() {
        try {
            localStorage.setItem(progressKey, JSON.stringify(progress));
        } catch (error) {
            console.warn('No se pudo guardar el progreso de practica:', error);
        }
    }

    function updateProgressPanel() {
        const solvedCount = progress.solvedIds.length;
        const totalAttempts = solvedCount + progress.errors;
        const accuracy = totalAttempts > 0 ? Math.round((solvedCount / totalAttempts) * 100) : 0;

        solvedCountElement.innerText = String(solvedCount);
        errorCountElement.innerText = String(progress.errors);
        accuracyElement.innerText = `${accuracy}%`;
    }

    function rememberSolvedPuzzle(puzzleId) {
        if (!progress.solvedIds.includes(puzzleId)) {
            progress.solvedIds.push(puzzleId);
            saveProgress();
            updateProgressPanel();
        }
    }

    function rememberError() {
        progress.errors += 1;
        saveProgress();
        updateProgressPanel();
    }

    function puzzlesForLevel(level) {
        return puzzles.filter(puzzle => puzzle.level === level);
    }

    function levelInfo(levelKey) {
        return levels.find(level => level.key === levelKey) || {};
    }

    function levelLabel(levelKey) {
        const level = levelInfo(levelKey);
        return uiText(level.label_key, levelKey);
    }

    function levelDescription(levelKey) {
        const level = levelInfo(levelKey);
        return uiText(level.description_key, `Mate en ${level.mate_in || '?'}`);
    }

    function selectLevel(levelKey) {
        const levelPuzzles = puzzlesForLevel(levelKey);

        if (levelPuzzles.length === 0) {
            return;
        }

        currentLevel = levelKey;
        currentPuzzleIndex = firstUnsolvedIndex(levelPuzzles);
        renderLevelButtons();
        loadPuzzle(levelPuzzles[currentPuzzleIndex]);
    }

    function firstUnsolvedIndex(levelPuzzles) {
        const index = levelPuzzles.findIndex(puzzle => !progress.solvedIds.includes(puzzle.id));
        return index >= 0 ? index : 0;
    }

    function loadPuzzle(puzzle) {
        currentPuzzle = puzzle;
        currentFen = puzzle.fen;
        currentPosition = parseFen(currentFen);
        selectedSquare = null;
        possibleMoves = [];
        possibleMovesLoaded = false;
        playedLine = [];
        solved = false;
        pendingMove = false;
        orientation = puzzle.turn || currentPosition.turn;
        lineMoves = [];

        titleElement.innerText = puzzle.title || uiText('practice_title', 'Practica');
        metaElement.innerText = `${levelLabel(puzzle.level)} - ${levelDescription(puzzle.level)} - ${turnLabel(puzzle.turn)}`;
        hideHint();
        showResult(uiText('practice_make_move', 'Encuentra la mejor jugada.'), 'neutral');
        setPracticeStatus(uiText('practice_make_move', 'Encuentra la mejor jugada.'));

        renderBoard();
        renderMoveLine();
        updateButtons();
    }

    function nextPuzzle() {
        const levelPuzzles = puzzlesForLevel(currentLevel);
        if (levelPuzzles.length === 0) {
            return;
        }

        currentPuzzleIndex = (currentPuzzleIndex + 1) % levelPuzzles.length;
        loadPuzzle(levelPuzzles[currentPuzzleIndex]);
    }

    function restartPuzzle() {
        if (currentPuzzle) {
            loadPuzzle(currentPuzzle);
        }
    }

    function renderLevelButtons() {
        levelButtons.forEach(button => {
            const active = button.dataset.practiceLevel === currentLevel;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }

    function turnLabel(color) {
        if (color === 'black') {
            return uiText('turn_black', 'Turno de negras');
        }

        return uiText('turn_white', 'Turno de blancas');
    }

    function setPracticeStatus(message) {
        if (statusElement) {
            statusElement.innerText = message;
        }
    }

    function parseFen(fen) {
        const [placement, turnToken] = fen.split(' ');
        const pieces = {};
        let rank = 8;
        let fileIndex = 0;

        for (const char of placement) {
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
        boardElement.replaceChildren();
        updateBoardLabels();

        squareSequence().forEach(coord => {
            const square = document.createElement('div');
            const fileIndex = files.indexOf(coord[0]);
            const rank = Number(coord[1]);
            const piece = currentPosition.pieces[coord];
            const isLight = (fileIndex + rank) % 2 === 0;

            square.className = `square ${isLight ? 'square-light' : 'square-dark'}`;
            square.dataset.coord = coord;
            square.dataset.color = piece ? piece.color : '';
            square.dataset.type = piece ? piece.type : '';
            square.draggable = false;

            if (coord === selectedSquare) {
                square.classList.add('selected');
            }

            if (isPossibleTarget(coord)) {
                square.classList.add('possible-move');
            }

            if (piece) {
                square.appendChild(createPieceElement(piece));
            }

            square.addEventListener('click', function () {
                handleSquareClick(coord);
            });
            square.addEventListener('pointerdown', function (event) {
                handlePointerDown(event, coord);
            });

            boardElement.appendChild(square);
        });
    }

    function createPieceElement(piece) {
        const image = document.createElement('img');
        const pieceKey = `${piece.type}_${piece.color}`;

        image.src = `${window.PRACTICE_PIECES_BASE_URL || '/static/games/pieces/'}${pieceKey}.png`;
        image.alt = pieceKey;
        image.className = 'piece';
        image.draggable = false;
        image.addEventListener('error', function () {
            const fallback = document.createElement('span');
            fallback.className = 'piece-fallback';
            fallback.innerText = '?';
            image.replaceWith(fallback);
        });

        return image;
    }

    function canSelectSquare(coord) {
        if (!currentPuzzle || solved || pendingMove) {
            return false;
        }

        const piece = currentPosition.pieces[coord];
        return Boolean(piece && piece.color === currentPuzzle.turn && currentPosition.turn === currentPuzzle.turn);
    }

    function isPossibleTarget(coord) {
        return possibleMoves.some(move => move.to === coord);
    }

    function clearSelection() {
        selectedSquare = null;
        possibleMoves = [];
        possibleMovesLoaded = false;
    }

    async function selectSquare(coord) {
        if (!canSelectSquare(coord)) {
            return;
        }

        selectedSquare = coord;
        possibleMoves = [];
        possibleMovesLoaded = false;
        renderBoard();

        try {
            const response = await fetch(window.PRACTICE_LEGAL_MOVES_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    puzzle_id: currentPuzzle.id,
                    played_line: playedLine,
                    from: coord,
                }),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.error || selectedSquare !== coord) {
                possibleMoves = [];
                possibleMovesLoaded = true;
                renderBoard();
                return;
            }

            possibleMoves = Array.isArray(data.moves) ? data.moves : [];
            possibleMovesLoaded = true;
            renderBoard();
        } catch (error) {
            console.warn('No se pudieron cargar los movimientos legales:', error);
            possibleMoves = [];
            possibleMovesLoaded = true;
            renderBoard();
        }
    }

    function handleSquareClick(coord) {
        if (suppressNextClick) {
            suppressNextClick = false;
            return;
        }

        if (!currentPuzzle || solved || pendingMove) {
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

        if (possibleMovesLoaded && !isPossibleTarget(coord)) {
            return;
        }

        submitMove(selectedSquare, coord);
    }

    function handlePointerDown(event, coord) {
        if (
            !event.isPrimary ||
            event.button !== 0 ||
            !canSelectSquare(coord)
        ) {
            return;
        }

        const piece = currentPosition.pieces[coord];
        dragState = {
            from: coord,
            startX: event.clientX,
            startY: event.clientY,
            piece,
            ghost: null,
            dragging: false,
        };

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
        window.addEventListener('pointercancel', cancelDrag);
    }

    function handlePointerMove(event) {
        if (!dragState) {
            return;
        }

        const distance = Math.hypot(event.clientX - dragState.startX, event.clientY - dragState.startY);
        if (!dragState.dragging && distance < 4) {
            return;
        }

        if (!dragState.dragging) {
            suppressNextClick = true;
            window.setTimeout(function () {
                suppressNextClick = false;
            }, 180);
            dragState.dragging = true;
            selectedSquare = dragState.from;
            possibleMoves = [];
            possibleMovesLoaded = false;
            renderBoard();
            selectSquare(dragState.from);
            createDragGhost(dragState);
        }

        moveDragGhost(event);
    }

    function handlePointerUp(event) {
        if (!dragState) {
            return;
        }

        const wasDragging = dragState.dragging;
        const from = dragState.from;
        clearDragListeners();

        if (!wasDragging) {
            dragState = null;
            return;
        }

        const targetSquare = squareFromPoint(event.clientX, event.clientY);
        removeDragGhost();
        dragState = null;

        if (!targetSquare || targetSquare === from) {
            clearSelection();
            renderBoard();
            return;
        }

        submitMove(from, targetSquare);
    }

    function cancelDrag() {
        clearDragListeners();
        removeDragGhost();
        dragState = null;
        suppressNextClick = false;
        clearSelection();
        renderBoard();
    }

    function clearDragListeners() {
        window.removeEventListener('pointermove', handlePointerMove);
        window.removeEventListener('pointerup', handlePointerUp);
        window.removeEventListener('pointercancel', cancelDrag);
    }

    function createDragGhost(state) {
        removeDragGhost();

        const square = boardElement.querySelector(`[data-coord="${state.from}"]`);
        const squareRect = square ? square.getBoundingClientRect() : boardElement.getBoundingClientRect();
        const ghost = createPieceElement(state.piece);
        ghost.classList.add('drag-piece', 'practice-drag-piece');
        ghost.style.left = '0';
        ghost.style.top = '0';
        ghost.style.width = `${squareRect.width * practiceDragPieceScale}px`;
        ghost.style.height = `${squareRect.height * practiceDragPieceScale}px`;
        document.body.appendChild(ghost);

        if (square) {
            square.classList.add('drag-origin');
        }

        state.ghost = ghost;
    }

    function moveDragGhost(event) {
        if (!dragState || !dragState.ghost) {
            return;
        }

        dragState.ghost.style.transform = `translate(${event.clientX - dragState.ghost.offsetWidth / 2}px, ${event.clientY - dragState.ghost.offsetHeight / 2}px)`;
    }

    function removeDragGhost() {
        if (dragState && dragState.from) {
            const square = boardElement.querySelector(`[data-coord="${dragState.from}"]`);
            if (square) {
                square.classList.remove('drag-origin');
            }
        }

        if (dragState && dragState.ghost) {
            dragState.ghost.remove();
            dragState.ghost = null;
        }
    }

    function squareFromPoint(clientX, clientY) {
        const element = document.elementFromPoint(clientX, clientY);
        const square = element ? element.closest('.practice-board .square') : null;
        return square ? square.dataset.coord : null;
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

    async function submitMove(from, to) {
        if (!currentPuzzle || pendingMove) {
            return;
        }

        pendingMove = true;
        possibleMoves = [];
        possibleMovesLoaded = false;
        setPracticeStatus(uiText('thinking', 'Pensando...'));

        try {
            const response = await fetch(window.PRACTICE_MOVE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    puzzle_id: currentPuzzle.id,
                    played_line: playedLine,
                    move: buildUciMove(from, to),
                }),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.error) {
                clearSelection();
                showResult(data.error || uiText('trainer_error', 'No se pudo revisar la jugada.'), 'wrong');
                return;
            }

            clearSelection();
            currentFen = data.fen || currentFen;
            playedLine = Array.isArray(data.played_line) ? data.played_line : playedLine;

            if (!data.correct) {
                rememberError();
                showResult(data.message || uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle'), 'wrong');
                setPracticeStatus(data.message || uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle'));
                renderBoard();
                return;
            }

            lineMoves.push({ ...data.played_move, auto: false });
            (data.auto_moves || []).forEach(move => {
                lineMoves.push({ ...move, auto: true });
            });

            solved = Boolean(data.solved);
            showResult(data.message || uiText('practice_follow_line', 'Correcto, segui la linea'), solved ? 'solved' : 'correct');
            setPracticeStatus(data.message || uiText('practice_follow_line', 'Correcto, segui la linea'));

            if (solved) {
                rememberSolvedPuzzle(currentPuzzle.id);
            }

            renderBoard();
            renderMoveLine();
        } catch (error) {
            console.error('Erro ao validar puzzle:', error);
            showResult(uiText('trainer_error', 'No se pudo revisar la jugada.'), 'wrong');
        } finally {
            pendingMove = false;
            renderBoard();
            updateButtons();
        }
    }

    function showResult(message, state) {
        resultElement.hidden = false;
        resultElement.innerText = message;
        resultElement.classList.remove('practice-result-neutral', 'practice-result-correct', 'practice-result-wrong', 'practice-result-solved');
        resultElement.classList.add(`practice-result-${state}`);
    }

    function showHint() {
        if (!currentPuzzle) {
            return;
        }

        hintElement.hidden = false;
        hintElement.innerText = currentPuzzle.hint || uiText('practice_no_hint', 'Mira primero los jaques disponibles.');
    }

    function hideHint() {
        hintElement.hidden = true;
        hintElement.innerText = '';
    }

    function renderMoveLine() {
        lineElement.replaceChildren();

        lineMoves.forEach((move, index) => {
            const item = document.createElement('li');
            const label = move.auto
                ? `${move.san || move.uci} (${uiText('practice_auto_reply', 'rival')})`
                : move.san || move.uci;

            item.innerText = label;
            item.classList.toggle('practice-line-auto', move.auto);
            item.value = index + 1;
            lineElement.appendChild(item);
        });
    }

    function updateButtons() {
        const disabled = !currentPuzzle;
        nextButton.disabled = disabled;
        restartButton.disabled = disabled;
        hintButton.disabled = disabled;
        if (flipButton) {
            flipButton.disabled = disabled;
        }
    }

    levelButtons.forEach(button => {
        button.addEventListener('click', function () {
            selectLevel(button.dataset.practiceLevel);
        });
    });

    nextButton.addEventListener('click', nextPuzzle);
    restartButton.addEventListener('click', restartPuzzle);
    hintButton.addEventListener('click', showHint);
    if (flipButton) {
        flipButton.addEventListener('click', function () {
            orientation = orientation === 'white' ? 'black' : 'white';
            renderBoard();
        });
    }

    updateProgressPanel();
    updateButtons();

    if (puzzles.length > 0) {
        selectLevel(currentLevel);
    } else {
        showResult(uiText('practice_no_puzzles', 'No hay puzzles disponibles.'), 'neutral');
    }
}());
