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

PRACTICE_CATEGORIES = [
    {
        "key": "mate_1",
        "label_key": "practice_mate_in_1",
        "description_key": "practice_category_mate_1_description",
    },
    {
        "key": "mate_2",
        "label_key": "practice_mate_in_2",
        "description_key": "practice_category_mate_2_description",
    },
    {
        "key": "mate_3",
        "label_key": "practice_mate_in_3",
        "description_key": "practice_category_mate_3_description",
    },
    {
        "key": "mate_4",
        "label_key": "practice_mate_in_4",
        "description_key": "practice_category_mate_4_description",
    },
    {
        "key": "mate_5_plus",
        "label_key": "practice_mate_in_5_plus",
        "description_key": "practice_category_mate_5_plus_description",
    },
    {
        "key": "pins",
        "label_key": "practice_category_pins",
        "description_key": "practice_category_pins_description",
    },
    {
        "key": "forks",
        "label_key": "practice_category_forks",
        "description_key": "practice_category_forks_description",
    },
    {
        "key": "discovered",
        "label_key": "practice_category_discovered",
        "description_key": "practice_category_discovered_description",
    },
    {
        "key": "endgames",
        "label_key": "practice_category_endgames",
        "description_key": "practice_category_endgames_description",
    },
    {
        "key": "sacrifices",
        "label_key": "practice_category_sacrifices",
        "description_key": "practice_category_sacrifices_description",
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
    {
        "id": "easy-scholars-f7",
        "title": "Mate escolar",
        "level": "easy",
        "mate_in": 1,
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 2 4",
        "turn": "white",
        "solutions": [["h5f7"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "La dama entra en f7 con apoyo del alfil.",
    },
    {
        "id": "easy-fools-mate",
        "title": "Mate del loco",
        "level": "easy",
        "mate_in": 1,
        "fen": "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2",
        "turn": "black",
        "solutions": [["d8h4"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "La diagonal de la dama negra llega directo al rey.",
    },
    {
        "id": "easy-back-rank-rook",
        "title": "Octava fila cerrada",
        "level": "easy",
        "mate_in": 1,
        "fen": "6k1/pp3ppp/8/8/8/8/PP3PPP/4R1K1 w - - 0 1",
        "turn": "white",
        "solutions": [["e1e8"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "La torre aprovecha que los peones no dejan salir al rey.",
    },
    {
        "id": "easy-knight-smother",
        "title": "Caballo encerrador",
        "level": "easy",
        "mate_in": 1,
        "fen": "r5rk/pp4pp/2b5/6N1/8/8/PP4PP/R5K1 w - - 0 1",
        "turn": "white",
        "solutions": [["g5f7"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "El caballo salta a una casilla donde el rey no puede capturarlo.",
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
        "id": "medium-legal-trap",
        "title": "Trampa de Legal",
        "level": "medium",
        "mate_in": 2,
        "fen": "r2qkbnr/ppp2ppp/2np4/4N3/2B1P1b1/2N5/PPPP1PPP/R1BbK2R w KQkq - 0 6",
        "turn": "white",
        "solutions": [["c4f7", "e8e7", "c3d5"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "El sacrificio en f7 atrae al rey a la red de los caballos.",
    },
    {
        "id": "medium-queen-deflection",
        "title": "Desvío del defensor",
        "level": "medium",
        "mate_in": 2,
        "fen": "5rk1/pp2Q1pp/2B5/6N1/8/8/PP4PP/4R1K1 w - - 0 1",
        "turn": "white",
        "solutions": [["e7f8", "g8f8", "e1e8"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "Entrega la dama para sacar al rey de su defensa.",
    },
    {
        "id": "medium-black-deflection",
        "title": "Desvío para negras",
        "level": "medium",
        "mate_in": 2,
        "fen": "4r1k1/pp4pp/8/8/6n1/2b5/PP2q1PP/5RK1 b - - 0 1",
        "turn": "black",
        "solutions": [["e2f1", "g1f1", "e8e1"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "La dama obliga al rey a entrar en la columna de la torre.",
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
    {
        "id": "hard-edge-rich",
        "title": "Rey al borde",
        "level": "hard",
        "mate_in": 3,
        "fen": "7k/pp2Q3/2n5/8/7K/8/PP4PP/R6R w - - 0 1",
        "turn": "white",
        "solutions": [["h4h5", "h8g8", "h5h6", "g8h8", "e7f8"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "Acerca el rey antes de dar el golpe final con la dama.",
    },
    {
        "id": "hard-black-edge-rich",
        "title": "Rey blanco al borde",
        "level": "hard",
        "mate_in": 3,
        "fen": "r6r/pp4pp/8/7k/8/2N5/PP2q3/7K b - - 0 1",
        "turn": "black",
        "solutions": [["h5h4", "h1g1", "h4h3", "g1h1", "e2f1"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "El rey negro gana espacio y la dama remata en la primera fila.",
    },
    {
        "id": "hard-smothered-classic",
        "title": "Mate ahogado clásico",
        "level": "hard",
        "mate_in": 3,
        "fen": "5rk1/pp3Npp/2b5/3Q4/8/2B5/PP4PP/R5K1 w - - 0 1",
        "turn": "white",
        "solutions": [["f7h6", "g8h8", "d5g8", "f8g8", "h6f7"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "El caballo inicia el encierro y vuelve para el mate.",
    },
    {
        "id": "hard-black-smothered",
        "title": "Ahogado para negras",
        "level": "hard",
        "mate_in": 3,
        "fen": "r5k1/pp4pp/2b5/8/3q4/2B5/PP3nPP/5RK1 b - - 0 1",
        "turn": "black",
        "solutions": [["f2h3", "g1h1", "d4g1", "f1g1", "h3f2"]],
        "notation": "uci",
        "solution_only": True,
        "hint": "El caballo obliga al rey a una esquina sin aire.",
    },
]

PRACTICE_THEME_CATEGORIES = {
    "easy-rook-e8": ["endgames"],
    "easy-queen-h7": ["endgames"],
    "easy-double-queen": ["endgames"],
    "easy-black-queen-h2": ["endgames"],
    "easy-scholars-f7": ["forks"],
    "easy-back-rank-rook": ["pins"],
    "easy-knight-smother": ["forks"],
    "medium-queen-net": ["endgames"],
    "medium-corner-queen": ["endgames"],
    "medium-king-net": ["endgames"],
    "medium-legal-trap": ["discovered", "sacrifices"],
    "medium-queen-deflection": ["pins", "sacrifices"],
    "medium-black-deflection": ["pins", "sacrifices"],
    "hard-central-queen": ["endgames"],
    "hard-edge-queen": ["endgames"],
    "hard-diagonal-queen": ["endgames"],
    "hard-edge-rich": ["endgames"],
    "hard-black-edge-rich": ["endgames"],
    "hard-smothered-classic": ["forks", "sacrifices"],
    "hard-black-smothered": ["forks", "sacrifices"],
}


def mate_category_key(mate_in):
    if mate_in <= 1:
        return "mate_1"
    if mate_in == 2:
        return "mate_2"
    if mate_in == 3:
        return "mate_3"
    if mate_in == 4:
        return "mate_4"

    return "mate_5_plus"


def practice_categories_for_puzzle(puzzle):
    # Every puzzle belongs to its mate-depth bucket plus any tactical motif tags.
    categories = [mate_category_key(puzzle["mate_in"])]
    categories.extend(PRACTICE_THEME_CATEGORIES.get(puzzle["id"], []))
    return categories


def public_puzzle_data(puzzle):
    return {
        "id": puzzle["id"],
        "title": puzzle.get("title", ""),
        "level": puzzle["level"],
        "mate_in": puzzle["mate_in"],
        "categories": practice_categories_for_puzzle(puzzle),
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
