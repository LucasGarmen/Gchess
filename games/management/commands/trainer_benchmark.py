import json
import time
import chess
import chess.engine
from django.core.management.base import BaseCommand, CommandError
from games.views import configured_stockfish_path, open_stockfish_engine


class Command(BaseCommand):
    help = "Report installed engine identity and compare trainer search budgets (no Gemini calls)."

    def add_arguments(self, parser):
        parser.add_argument("--runs", type=int, default=3)

    def handle(self, *args, **options):
        path, error = configured_stockfish_path()
        if error:
            raise CommandError("Stockfish unavailable; check STOCKFISH_PATH")
        engine = open_stockfish_engine(path)
        try:
            engine.configure({"Threads": 1, "Hash": 16})
            self.stdout.write(json.dumps({"engine": engine.id, "threads": 1, "hash_mb": 16}))
            positions = [chess.Board(), chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")]
            for seconds in (0.05, 0.12, 0.3, 0.6):
                rows = []
                for board in positions:
                    for _ in range(max(1, min(10, options["runs"]))):
                        engine.configure({"Clear Hash": None})
                        start = time.perf_counter()
                        result = engine.analyse(board, chess.engine.Limit(time=seconds), multipv=3)
                        rows.append({"elapsed_ms": round((time.perf_counter()-start)*1000), "depth": result[0].get("depth"), "nodes": result[0].get("nodes"), "best": board.san(result[0]["pv"][0]), "score": str(result[0]["score"].white())})
                self.stdout.write(json.dumps({"budget_seconds": seconds, "samples": rows}))
        finally:
            engine.quit()
