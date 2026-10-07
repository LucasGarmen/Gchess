import chess
from django.test import SimpleTestCase
from games.tests import FakeAnalysisEngine, fake_engine_analysis
from games.views import automatic_move_fact, build_automatic_move_context


class CoachFeedbackTests(SimpleTestCase):
    def test_missing_principal_variation_cannot_claim_best(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        after = board.copy()
        after.push(move)
        context = build_automatic_move_context(FakeAnalysisEngine({board.fen():fake_engine_analysis(30), after.fen():fake_engine_analysis(30)}), board, move, language="es")
        self.assertEqual(context["classification"], "neutral")
        self.assertIsNone(context["best_move_san"])
        self.assertFalse(context["played_equals_best"])

    def test_checkmate_is_described_in_all_languages(self):
        board = chess.Board()
        for uci in ("f2f3", "e7e5", "g2g4"):
            board.push_uci(uci)
        for language, expected in (("es","jaque mate"),("en","checkmate"),("pt","xeque-mate")):
            self.assertIn(expected, automatic_move_fact(board, chess.Move.from_uci("d8h4"), language))

    def test_en_passant_capture_is_identified(self):
        board = chess.Board()
        for uci in ("e2e4","a7a6","e4e5","d7d5"):
            board.push_uci(uci)
        self.assertIn("Capturaste", automatic_move_fact(board, chess.Move.from_uci("e5d6"), "es"))

    def test_quiet_move_has_no_invented_tactical_fact(self):
        self.assertEqual(automatic_move_fact(chess.Board(), chess.Move.from_uci("e2e4"), "es"), "")

    def test_error_comment_contains_legal_opponent_reply(self):
        board = chess.Board()
        played = chess.Move.from_uci("g2g4")
        best = chess.Move.from_uci("e2e4")
        after = board.copy()
        after.push(played)
        alternative = board.copy()
        alternative.push(best)
        engine = FakeAnalysisEngine({board.fen():fake_engine_analysis(45,[best]), after.fen():fake_engine_analysis(-170,[chess.Move.from_uci("e7e5")]), alternative.fen():fake_engine_analysis(45)})
        context = build_automatic_move_context(engine,board,played,language="es")
        self.assertEqual(context["classification"],"mistake")
        self.assertEqual(context["engine_reply_san"],"e5")
        self.assertIn("el rival podría responder con peón a e5",context["comment"])
