PRACTICE_LEVELS = [
    {
        "key": "easy",
        "label_key": "practice_easy",
        "description_key": "practice_mate_in_1",
        "mate_in": 1,
    },
    {
        "key": "medium",
        "label_key": "practice_medium",
        "description_key": "practice_mate_in_2",
        "mate_in": 2,
    },
    {
        "key": "hard",
        "label_key": "practice_hard",
        "description_key": "practice_mate_in_3",
        "mate_in": 3,
    },
]


# Each solution is one sample full line in UCI notation.
# Even indexes (0, 2, 4) are student moves; odd indexes are rival replies.
# The validator can also accept other moves that prove the mate objective.
PRACTICE_PUZZLES = [
    {
        "id": "easy-rook-e8",
        "title": "Torre en la octava",
        "level": "easy",
        "mate_in": 1,
        "fen": "6k1/5ppp/8/8/8/8/6PP/4R1K1 w - - 0 1",
        "turn": "white",
        "solutions": [["e1e8"]],
        "notation": "uci",
        "hint": "La torre puede cortar toda la octava fila.",
    },
    {
        "id": "easy-queen-h7",
        "title": "Dama protegida",
        "level": "easy",
        "mate_in": 1,
        "fen": "7k/6pp/6K1/7Q/8/8/8/8 w - - 0 1",
        "turn": "white",
        "solutions": [["h5h7"]],
        "notation": "uci",
        "hint": "El rey blanco protege la casilla clave junto al rey rival.",
    },
    {
        "id": "easy-double-queen",
        "title": "Dos mates de dama",
        "level": "easy",
        "mate_in": 1,
        "fen": "8/8/8/8/8/2K5/6Q1/3k4 w - - 0 1",
        "turn": "white",
        "solutions": [["g2d2"], ["g2f1"]],
        "notation": "uci",
        "hint": "La dama tiene dos casillas de mate cerca del rey negro.",
    },
    {
        "id": "easy-black-queen-h2",
        "title": "Negras dan mate",
        "level": "easy",
        "mate_in": 1,
        "fen": "8/8/8/8/7q/6k1/6PP/7K b - - 0 1",
        "turn": "black",
        "solutions": [["h4h2"]],
        "notation": "uci",
        "hint": "La dama negra puede capturar junto al rey blanco.",
    },
    # The original mate-in-2 and mate-in-3 examples were cooperative lines.
    # These replacements were checked as forced mates with python-chess.
    {
        "id": "medium-queen-net",
        "title": "Red de dama",
        "level": "medium",
        "mate_in": 2,
        "fen": "8/8/8/8/k2K4/5Q2/8/8 w - - 0 1",
        "turn": "white",
        "solutions": [["d4c5", "a4a5", "f3a8"]],
        "notation": "uci",
        "hint": "Usa el rey para quitarle al rey negro las casillas de escape.",
    },
    {
        "id": "medium-corner-queen",
        "title": "Dama contra rincón",
        "level": "medium",
        "mate_in": 2,
        "fen": "8/8/8/8/5Q1K/8/8/6k1 w - - 0 1",
        "turn": "white",
        "solutions": [
            ["h4h3", "g1h1", "f4h2"],
            ["h4g3", "g1h1", "f4f1"],
        ],
        "notation": "uci",
        "hint": "El rey blanco debe acercarse sin dejar escapar al rey negro.",
    },
    {
        "id": "medium-king-net",
        "title": "Rey dominante",
        "level": "medium",
        "mate_in": 2,
        "fen": "3k4/8/8/4K3/Q7/8/8/8 w - - 0 1",
        "turn": "white",
        "solutions": [["e5d6", "d8c8", "a4a8"]],
        "notation": "uci",
        "hint": "El rey blanco puede encerrar primero y la dama remata.",
    },
    {
        "id": "hard-central-queen",
        "title": "Dama central",
        "level": "hard",
        "mate_in": 3,
        "fen": "8/8/8/8/3Q4/3K4/8/1k6 w - - 0 1",
        "turn": "white",
        "solutions": [
            ["d4b6", "b1a2", "d3c3", "a2a3", "b6a7"],
            ["d4b6", "b1c1", "b6b8", "c1d1", "b8b1"],
            ["d4e5", "b1a2", "d3c2", "a2a3", "e5a5"],
        ],
        "notation": "uci",
        "hint": "La dama y el rey deben cerrar el borde antes del mate.",
    },
    {
        "id": "hard-edge-queen",
        "title": "Red en la esquina",
        "level": "hard",
        "mate_in": 3,
        "fen": "7k/4Q3/8/8/7K/8/8/8 w - - 0 1",
        "turn": "white",
        "solutions": [
            ["h4h5", "h8g8", "h5h6", "g8h8", "e7f8"],
            ["h4g5", "h8g8", "g5h6", "g8h8", "e7f8"],
        ],
        "notation": "uci",
        "hint": "Acerca el rey para que la dama pueda cubrir la última fuga.",
    },
    {
        "id": "hard-diagonal-queen",
        "title": "Dama diagonal",
        "level": "hard",
        "mate_in": 3,
        "fen": "8/8/6Q1/8/6K1/8/8/5k2 w - - 0 1",
        "turn": "white",
        "solutions": [
            ["g6c2", "f1g1", "g4g3", "g1h1", "c2h2"],
            ["g6c2", "f1e1", "g4g3", "e1f1", "c2f2"],
            ["g4f3", "f1e1", "g6d6", "e1f1", "d6d1"],
        ],
        "notation": "uci",
        "hint": "Coordina rey y dama para llevar al rey negro al rincón.",
    },
]


def public_puzzle_data(puzzle):
    return {
        "id": puzzle["id"],
        "title": puzzle.get("title", ""),
        "level": puzzle["level"],
        "mate_in": puzzle["mate_in"],
        "fen": puzzle["fen"],
        "turn": puzzle["turn"],
        "hint": puzzle.get("hint", ""),
    }


def public_practice_puzzles():
    return [public_puzzle_data(puzzle) for puzzle in PRACTICE_PUZZLES]


def get_practice_puzzle(puzzle_id):
    for puzzle in PRACTICE_PUZZLES:
        if puzzle["id"] == puzzle_id:
            return puzzle

    return None
