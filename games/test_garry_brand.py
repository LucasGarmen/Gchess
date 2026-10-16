from django.test import SimpleTestCase
from .i18n import TRANSLATIONS
from .launch_texts import TEXTS
from .first_steps import TEXTS as ENTRY
from .prompts import build_trainer_chat_prompt, build_pgn_analysis_chat_prompt


class AssistantIdentityTests(SimpleTestCase):
    def test_name_is_consistent_in_all_languages_and_entry_points(self):
        for language in ['es','pt','en']:
            for key in ['play_bot','coach_chat','computer_thinking','trainer_error','trainer_analyzing','enable_coach','disable_coach','ask_position']:
                self.assertIn('Gchess Bot', TRANSLATIONS[language][key], (language,key))
            for key in ['hero_title','hero_play','hero_intro','demo','demo_coach','thinking']:
                self.assertIn('Gchess Bot',TEXTS[language][key],(language,key))
            self.assertIn('Gchess Bot',ENTRY[language]['level'])

    def test_both_conversation_prompts_keep_the_same_identity(self):
        for language in ['es','pt','en']:
            for prompt in [build_trainer_chat_prompt('Who are you?',{},language),build_pgn_analysis_chat_prompt('Who are you?',{},language)]:
                self.assertIn('You are Gchess Bot',prompt)
                self.assertIn('Your name is Gchess Bot in every language.',prompt)
