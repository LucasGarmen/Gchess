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
    const fenSymbolsByPieceType = {
        pawn: 'p',
        horse: 'n',
        bishop: 'b',
        rook: 'r',
        queen: 'q',
        king: 'k',
    };
    const pieceTypeByPromotion = {
        q: 'queen',
        r: 'rook',
        b: 'bishop',
        n: 'horse',
    };
    const progressKey = 'gchess-practice-progress-v1';
    const practiceDragPieceScale = 1.7;

    const boardElement = document.getElementById('practice-board');
    const categoryButtons = Array.from(document.querySelectorAll('[data-practice-category]'));
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
    const xpLevelElement = document.getElementById('practice-xp-level');
    const xpRemainingElement = document.getElementById('practice-xp-remaining');
    const xpFillElement = document.getElementById('practice-xp-fill');
    const xpCurrentElement = document.getElementById('practice-xp-current');
    const xpTotalElement = document.getElementById('practice-xp-total');
    const xpGainedElement = document.getElementById('practice-xp-gained');

    if (!boardElement) {
        return;
    }

    const categories = parseJsonScript('practice-categories-data', []);
    const levels = parseJsonScript('practice-levels-data', []);
    const puzzles = parseJsonScript('practice-puzzles-data', []);
    const puzzlesByCategory = puzzles.reduce((categoriesByKey, puzzle) => {
        const puzzleCategories = Array.isArray(puzzle.categories) ? puzzle.categories : [];

        puzzleCategories.forEach(categoryKey => {
            if (!categoriesByKey[categoryKey]) {
                categoriesByKey[categoryKey] = [];
            }

            categoriesByKey[categoryKey].push(puzzle);
        });

        return categoriesByKey;
    }, {});
    Object.values(puzzlesByCategory).forEach(categoryPuzzles => {
        categoryPuzzles.sort((first, second) => puzzlePieceCount(second) - puzzlePieceCount(first));
    });

    function firstCategoryWithPuzzles() {
        const category = categories.find(item => puzzlesForCategory(item.key).length > 0);

        if (category) {
            return category.key;
        }

        return categories.length > 0 ? categories[0].key : '';
    }

    let currentCategory = firstCategoryWithPuzzles();
    let currentPuzzleIndex = 0;
    let currentPuzzle = null;
    let currentFen = '';
    let currentPosition = { pieces: {}, turn: 'white' };
    let currentLegalMovesByFrom = {};
    let selectedSquare = null;
    let possibleMoves = [];
    let possibleMovesLoaded = false;
    let playedLine = [];
    let solved = false;
    let pendingMove = false;
    let orientation = 'white';
    let lineMoves = [];
    let progress = loadProgress();
    let puzzleStartedAt = Date.now();
    let dragState = null;
    let suppressNextClick = false;
    let boardSquares = new Map();
    let renderedOrientation = null;

    function parseJsonScript(id, fallbackValue) {
        const element = document.getElementById(id);
        if (!element) {
            return fallbackValue;
        }

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            console.warn('No se pudo leer JSON de práctica:', error);
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
            console.warn('No se pudo guardar el progreso de práctica:', error);
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

    function puzzlesForCategory(categoryKey) {
        return puzzlesByCategory[categoryKey] || [];
    }

    function puzzlePieceCount(puzzle) {
        return Object.keys(parseFen(puzzle.fen || '').pieces).length;
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

    function categoryInfo(categoryKey) {
        return categories.find(category => category.key === categoryKey) || {};
    }

    function categoryLabel(categoryKey) {
        const category = categoryInfo(categoryKey);
        return uiText(category.label_key, categoryKey);
    }

    function categoryDescription(categoryKey) {
        const category = categoryInfo(categoryKey);
        return uiText(category.description_key, '');
    }

    function selectCategory(categoryKey) {
        const categoryPuzzles = puzzlesForCategory(categoryKey);

        currentCategory = categoryKey;
        currentPuzzleIndex = firstUnsolvedIndex(categoryPuzzles);
        renderCategoryButtons();

        if (categoryPuzzles.length === 0) {
            clearPuzzleSelection(categoryKey);
            return;
        }

        loadPuzzle(categoryPuzzles[currentPuzzleIndex]);
    }

    function firstUnsolvedIndex(categoryPuzzles) {
        const index = categoryPuzzles.findIndex(puzzle => !progress.solvedIds.includes(puzzle.id));
        return index >= 0 ? index : 0;
    }

    function clearPuzzleSelection(categoryKey) {
        currentPuzzle = null;
        currentFen = '';
        currentPosition = { pieces: {}, turn: 'white' };
        currentLegalMovesByFrom = {};
        selectedSquare = null;
        possibleMoves = [];
        possibleMovesLoaded = false;
        playedLine = [];
        solved = false;
        pendingMove = false;
        lineMoves = [];
        titleElement.innerText = categoryLabel(categoryKey) || uiText('practice_choose_category', 'Elige una categoria');
        metaElement.innerText = categoryDescription(categoryKey);
        hideHint();
        showResult(uiText('practice_no_category_puzzles', 'No hay puzzles en esta categoria todavia.'), 'neutral');
        setPracticeStatus(uiText('practice_no_category_puzzles', 'No hay puzzles en esta categoria todavia.'));
        renderBoard();
        renderMoveLine();
        updateButtons();
    }

    function loadPuzzle(puzzle) {
        currentPuzzle = puzzle;
        currentFen = puzzle.fen;
        currentPosition = parseFen(currentFen);
        currentLegalMovesByFrom = normalizeLegalMovesByFrom(puzzle.legal_moves);
        selectedSquare = null;
        possibleMoves = [];
        possibleMovesLoaded = false;
        playedLine = [];
        solved = false;
        pendingMove = false;
        orientation = puzzle.turn || currentPosition.turn;
        lineMoves = [];
        puzzleStartedAt = Date.now();

        titleElement.innerText = puzzle.title || uiText('practice_title', 'Práctica');
        metaElement.innerText = `${categoryLabel(currentCategory)} - ${levelLabel(puzzle.level)} - ${levelDescription(puzzle.level)} - ${turnLabel(puzzle.turn)}`;
        hideHint();
        showResult(uiText('practice_make_move', 'Encuentra la mejor jugada.'), 'neutral');
        setPracticeStatus(uiText('practice_make_move', 'Encuentra la mejor jugada.'));

        renderBoard();
        renderMoveLine();
        updateButtons();
    }

    function elapsedPuzzleMilliseconds() {
        return Math.max(0, Date.now() - puzzleStartedAt);
    }

    function restartPuzzleTimer() {
        puzzleStartedAt = Date.now();
    }

    function updateXpProgress(xpProgress) {
        if (!xpProgress || !xpLevelElement) {
            return;
        }

        xpLevelElement.innerText = String(xpProgress.nivel);
        xpRemainingElement.innerText = String(xpProgress.xp_restante);
        xpCurrentElement.innerText = String(xpProgress.xp_del_nivel_actual);
        xpTotalElement.innerText = String(xpProgress.xp_total);

        if (xpFillElement) {
            xpFillElement.style.width = `${Math.max(0, Math.min(100, xpProgress.porcentaje_xp_nivel))}%`;
        }

        if (xpGainedElement && Number(xpProgress.xp_ganado) > 0) {
            xpGainedElement.hidden = false;
            xpGainedElement.innerText = `+${xpProgress.xp_ganado} XP`;
            window.setTimeout(function () {
                xpGainedElement.hidden = true;
            }, 2600);
        }
    }

    function nextPuzzle() {
        const categoryPuzzles = puzzlesForCategory(currentCategory);
        if (categoryPuzzles.length === 0) {
            return;
        }

        currentPuzzleIndex = (currentPuzzleIndex + 1) % categoryPuzzles.length;
        loadPuzzle(categoryPuzzles[currentPuzzleIndex]);
    }

    function restartPuzzle() {
        if (currentPuzzle) {
            loadPuzzle(currentPuzzle);
        }
    }

    function renderCategoryButtons() {
        categoryButtons.forEach(button => {
            const categoryKey = button.dataset.practiceCategory;
            const active = categoryKey === currentCategory;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', active ? 'true' : 'false');
            button.classList.toggle('is-empty', puzzlesForCategory(categoryKey).length === 0);
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
        updateBoardLabels();

        if (renderedOrientation !== orientation || boardSquares.size === 0) {
            buildBoardSquares();
        }

        updateBoardSquares();
    }

    function buildBoardSquares() {
        boardElement.replaceChildren();
        boardSquares = new Map();
        renderedOrientation = orientation;

        squareSequence().forEach(coord => {
            const square = document.createElement('div');

            square.dataset.coord = coord;
            square.draggable = false;
            square.addEventListener('click', function () {
                handleSquareClick(coord);
            });
            square.addEventListener('pointerdown', function (event) {
                handlePointerDown(event, coord);
            });

            boardSquares.set(coord, square);
            boardElement.appendChild(square);
        });
    }

    function updateBoardSquares() {
        boardSquares.forEach((square, coord) => {
            const fileIndex = files.indexOf(coord[0]);
            const rank = Number(coord[1]);
            const piece = currentPosition.pieces[coord];
            const isLight = (fileIndex + rank) % 2 === 0;
            const pieceKey = piece ? `${piece.type}_${piece.color}` : '';

            square.className = `square ${isLight ? 'square-light' : 'square-dark'}`;
            square.dataset.color = piece ? piece.color : '';
            square.dataset.type = piece ? piece.type : '';

            if (coord === selectedSquare) {
                square.classList.add('selected');
            }

            if (isPossibleTarget(coord)) {
                square.classList.add('possible-move');
            }

            if (square.dataset.pieceKey !== pieceKey) {
                square.replaceChildren();

                if (piece) {
                    square.appendChild(createPieceElement(piece));
                }

                square.dataset.pieceKey = pieceKey;
            }
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

    function normalizeLegalMovesByFrom(movesByFrom) {
        if (!movesByFrom || typeof movesByFrom !== 'object' || Array.isArray(movesByFrom)) {
            return {};
        }

        return Object.entries(movesByFrom).reduce((normalized, [from, moves]) => {
            normalized[from] = Array.isArray(moves) ? moves : [];
            return normalized;
        }, {});
    }

    function updateLegalMovesByFrom(movesByFrom) {
        currentLegalMovesByFrom = normalizeLegalMovesByFrom(movesByFrom);
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

    function legalMovesForSquare(coord) {
        return currentLegalMovesByFrom[coord] || [];
    }

    function clearSelection() {
        selectedSquare = null;
        possibleMoves = [];
        possibleMovesLoaded = false;
    }

    function selectSquare(coord) {
        if (!canSelectSquare(coord)) {
            return;
        }

        selectedSquare = coord;
        possibleMoves = legalMovesForSquare(coord);
        possibleMovesLoaded = true;
        renderBoard();
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
            rejectIllegalMove();
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
            possibleMoves = legalMovesForSquare(dragState.from);
            possibleMovesLoaded = true;
            renderBoard();
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

        if (!isLegalMoveTarget(from, targetSquare)) {
            rejectIllegalMove();
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

    function isLegalMoveTarget(from, to) {
        return legalMovesForSquare(from).some(move => move.to === to);
    }

    function rejectIllegalMove() {
        clearSelection();
        showResult(uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle.'), 'wrong');
        setPracticeStatus(uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle.'));
        renderBoard();
    }

    function applyOptimisticMoveToFen(fen, uciMove) {
        const fenParts = fen.split(' ');
        const position = parseFen(fen);
        const pieces = { ...position.pieces };
        const from = uciMove.slice(0, 2);
        const to = uciMove.slice(2, 4);
        const promotion = uciMove[4];
        const movingPiece = pieces[from];

        if (!movingPiece) {
            return fen;
        }

        const targetPiece = pieces[to];
        const movedPiece = { ...movingPiece };

        delete pieces[from];

        if (
            movingPiece.type === 'pawn' &&
            from[0] !== to[0] &&
            !targetPiece &&
            to === (fenParts[3] || '-')
        ) {
            delete pieces[`${to[0]}${from[1]}`];
        }

        if (promotion && pieceTypeByPromotion[promotion]) {
            movedPiece.type = pieceTypeByPromotion[promotion];
        }

        pieces[to] = movedPiece;
        moveCastlingRookIfNeeded(pieces, movingPiece, from, to);

        const nextTurn = position.turn === 'white' ? 'b' : 'w';
        const fullMoveNumber = String(
            Math.max(1, Number(fenParts[5] || '1') + (position.turn === 'black' ? 1 : 0))
        );

        return `${placementFromPieces(pieces)} ${nextTurn} - - 0 ${fullMoveNumber}`;
    }

    function moveCastlingRookIfNeeded(pieces, movingPiece, from, to) {
        if (
            movingPiece.type !== 'king' ||
            Math.abs(files.indexOf(to[0]) - files.indexOf(from[0])) !== 2
        ) {
            return;
        }

        const rank = from[1];
        const kingside = to[0] === 'g';
        const rookFrom = `${kingside ? 'h' : 'a'}${rank}`;
        const rookTo = `${kingside ? 'f' : 'd'}${rank}`;

        if (pieces[rookFrom]) {
            pieces[rookTo] = pieces[rookFrom];
            delete pieces[rookFrom];
        }
    }

    function placementFromPieces(pieces) {
        const ranks = [];

        for (let rank = 8; rank >= 1; rank -= 1) {
            let emptySquares = 0;
            let row = '';

            files.forEach(file => {
                const piece = pieces[`${file}${rank}`];

                if (!piece) {
                    emptySquares += 1;
                    return;
                }

                if (emptySquares > 0) {
                    row += String(emptySquares);
                    emptySquares = 0;
                }

                row += pieceToFenSymbol(piece);
            });

            if (emptySquares > 0) {
                row += String(emptySquares);
            }

            ranks.push(row);
        }

        return ranks.join('/');
    }

    function pieceToFenSymbol(piece) {
        const symbol = fenSymbolsByPieceType[piece.type] || '';
        return piece.color === 'white' ? symbol.toUpperCase() : symbol;
    }

    async function submitMove(from, to) {
        if (!currentPuzzle || pendingMove) {
            return;
        }

        if (!isLegalMoveTarget(from, to)) {
            rejectIllegalMove();
            return;
        }

        const attemptedMove = buildUciMove(from, to);
        const previousFen = currentFen;

        pendingMove = true;
        possibleMoves = [];
        possibleMovesLoaded = false;
        clearSelection();
        currentFen = applyOptimisticMoveToFen(currentFen, attemptedMove);
        setPracticeStatus(uiText('thinking', 'Pensando...'));
        renderBoard();

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
                    move: attemptedMove,
                    elapsed_ms: elapsedPuzzleMilliseconds(),
                }),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.error) {
                currentFen = data.fen || previousFen;
                showResult(data.error || uiText('practice_review_error', 'No se pudo revisar la jugada.'), 'wrong');
                return;
            }

            currentFen = data.fen || currentFen;
            playedLine = Array.isArray(data.played_line) ? data.played_line : playedLine;
            updateLegalMovesByFrom(data.legal_moves);

            if (!data.correct) {
                currentFen = data.fen || previousFen;
                rememberError();
                restartPuzzleTimer();
                showResult(data.message || uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle'), 'wrong');
                setPracticeStatus(data.message || uiText('practice_wrong_objective', 'Esa jugada no resuelve el puzzle'));
                return;
            }

            lineMoves.push({ ...data.played_move, auto: false });
            (data.auto_moves || []).forEach(move => {
                lineMoves.push({ ...move, auto: true });
            });

            solved = Boolean(data.solved);
            showResult(data.message || uiText('practice_follow_line', '¡Correcto, sigue la línea!'), solved ? 'solved' : 'correct');
            setPracticeStatus(data.message || uiText('practice_follow_line', '¡Correcto, sigue la línea!'));

            if (solved) {
                rememberSolvedPuzzle(currentPuzzle.id);
                updateXpProgress(data.xp_progress);
            }

            renderMoveLine();
        } catch (error) {
            currentFen = previousFen;
            console.error('No se pudo validar el puzzle:', error);
            showResult(uiText('practice_review_error', 'No se pudo revisar la jugada.'), 'wrong');
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
        hintElement.innerText = currentPuzzle.hint || uiText('practice_no_hint', 'Busca primero jaques y casillas de escape.');
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

    categoryButtons.forEach(button => {
        button.addEventListener('click', function () {
            selectCategory(button.dataset.practiceCategory);
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

    if (puzzles.length > 0 && currentCategory) {
        selectCategory(currentCategory);
    } else {
        showResult(uiText('practice_no_puzzles', 'No hay puzzles disponibles.'), 'neutral');
    }
}());
