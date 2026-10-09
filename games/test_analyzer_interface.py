from django.test import SimpleTestCase
from django.template.loader import render_to_string
from games.templatetags.cosmetic_art import analyzer_words


class AnalyzerInterfaceTests(SimpleTestCase):
    def render_page(self, **extra):
        return render_to_string("games/game_analyzer.html", {"current_language": "es", **extra})

    def test_entry_preserves_input_and_accessible_error(self):
        html = self.render_page(pgn_text="1. e4 invalid", error_message="Invalid PGN")
        self.assertIn("1. e4 invalid</textarea>", html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id="pgn-server-error" role="alert"', html)
        self.assertIn('accept=".pgn,.txt,text/plain"', html)
        self.assertIn('method="POST"', html)

    def test_review_controls_stay_unique_and_near_board(self):
        html = self.render_page(moves=["e2e4"], analysis=[])
        for control in ("prev-move", "next-move", "last-move"):
            self.assertEqual(html.count('id="' + control + '"'), 1)
            self.assertLess(html.index('id="' + control + '"'), html.index('id="board"'))
        self.assertLess(html.index('id="analysis-comment"'), html.index('id="trainer-chat-form"'))

    def test_import_messages_cover_supported_languages(self):
        rows = [analyzer_words(lang) for lang in ("es", "pt", "en")]
        for row in rows:
            self.assertEqual(set(row), set(rows[0]))
            self.assertTrue(all(row.values()))
            self.assertIn("80 KB", row["file_error"])
