from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from .i18n import t


class OnboardingTests(TestCase):
    def test_home_entry_and_questions_in_each_language(self):
        for language in ('pt', 'es', 'en'):
            session = self.client.session
            session['language'] = language
            session.save()
            response = self.client.get(reverse('home'))
            self.assertEqual(response.status_code, 200)
            for key in ('home_learning_title', 'home_learning_intro', 'trainer_question_plan', 'trainer_question_last'):
                self.assertContains(response, t(language, key))
            self.assertContains(response, 'id="home-open-bot"')
            self.assertNotContains(response, 'id="home-start-play"')

    def test_finished_analysis_form_is_outside_hidden_pgn_tab(self):
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        self.assertLess(html.index('id="analyze-game-form"'), html.index('id="computer-coach-panel"'))
        self.assertLess(html.index('id="analyze-game-form"'), html.index('id="computer-pgn-panel"'))
        self.assertContains(response, 'action="' + reverse('game_analyzer') + '"')
        self.assertContains(response, 'name="pgn"')

    def test_loaded_analyzer_offers_questions_and_free_text(self):
        for language in ('pt', 'es', 'en'):
            html = render_to_string('games/game_analyzer.html', {
                'current_language': language,
                'moves': [{'from': 'e2', 'to': 'e4', 'san': 'e4'}],
                'analysis': [], 'trainer_player_color': 'white',
            })
            self.assertIn(t(language, 'trainer_question_plan'), html)
            self.assertIn(t(language, 'trainer_question_last'), html)
            self.assertIn('id="trainer-chat-input"', html)
            self.assertIn('data-trainer-question', html)
