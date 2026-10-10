(() => {
    const board = document.querySelector('.home-hero-visual .entry-mini-board');
    if (!board || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const initial = board.innerHTML;
    const moves = ['e2e4', 'e7e5', 'f1c4', 'b8c6', 'd1h5', 'g8f6', 'h5f7'];
    const index = square => (8 - Number(square[1])) * 8 + square.charCodeAt(0) - 97;
    let turn = 0;
    function advance() {
        if (document.hidden || !board.isConnected) return;
        if (turn === moves.length) {
            board.innerHTML = initial;
            board.removeAttribute('data-mate');
            turn = 0;
            return;
        }
        const move = moves[turn++];
        const from = board.children[index(move.slice(0, 2))];
        const to = board.children[index(move.slice(2))];
        const piece = from.querySelector('img');
        if (!piece) return;
        const origin = from.getBoundingClientRect();
        const destination = to.getBoundingClientRect();
        board.querySelectorAll('[data-last-move]').forEach(cell => cell.removeAttribute('data-last-move'));
        from.setAttribute('data-last-move', '');
        to.setAttribute('data-last-move', '');
        to.replaceChildren(piece);
        piece.animate([{transform: `translate(${origin.left - destination.left}px, ${origin.top - destination.top}px)`}, {transform: 'translate(0, 0)'}], {duration: 600, easing: 'ease-in-out'});
        if (turn === moves.length) board.setAttribute('data-mate', '');
    }
    function tick() {
        advance();
        setTimeout(tick, turn === moves.length ? 3000 : 1400);
    }
    setTimeout(tick, 1400);
})();
