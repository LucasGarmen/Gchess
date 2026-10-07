import importlib
import re
from pathlib import Path
from string import Formatter

from django.test import SimpleTestCase

from .i18n import TRANSLATIONS


def flatten_texts(row, prefix=""):
    texts = {}
    for key, value in row.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            texts.update(flatten_texts(value, path + "."))
        else:
            texts[path] = value
    return texts


class InterfaceLanguageTests(SimpleTestCase):
    def catalogs(self):
        yield "main", TRANSLATIONS
        for name, attribute in (
            ("create_texts", "TEXTS"), ("social_texts", "SOCIAL_TEXTS"),
            ("learning_texts", "LEARNING_TEXTS"), ("learning_progress_texts", "TEXTS"),
            ("daily_training_texts", "TEXTS"), ("weekly_texts", "TEXTS"),
            ("tournament_texts", "TEXTS"), ("blindfold", "TEXTS"), ("first_steps", "TEXTS"),
        ):
            catalog = getattr(importlib.import_module(f"games.{name}"), attribute)
            yield name, {language: flatten_texts(row) for language, row in catalog.items()}

    def test_all_interface_catalogs_cover_three_languages(self):
        for name, catalog in self.catalogs():
            self.assertEqual(set(catalog), {"es", "pt", "en"}, name)
            expected = set().union(*(set(row) for row in catalog.values()))
            for language, row in catalog.items():
                with self.subTest(catalog=name, language=language):
                    self.assertEqual(set(row), expected)
                    self.assertTrue(all(isinstance(text, str) and text.strip() for text in row.values()))

    def test_translations_preserve_format_fields(self):
        def fields(text):
            return {field for _, field, _, _ in Formatter().parse(text) if field is not None}
        for name, catalog in self.catalogs():
            for key, text in catalog["pt"].items():
                for language in ("es", "en"):
                    with self.subTest(catalog=name, key=key, language=language):
                        self.assertEqual(fields(catalog[language][key]), fields(text))

    def test_template_translation_keys_exist_in_every_language(self):
        root = Path(__file__).resolve().parent.parent
        keys = set()
        for directory in (root / "games/templates", root / "accounts/templates"):
            for template in directory.rglob("*.html"):
                keys.update(re.findall(r"\{%\s*tr\s+[\"']([^\"']+)[\"']", template.read_text(encoding="utf-8")))
        self.assertTrue(keys)
        for language, catalog in TRANSLATIONS.items():
            self.assertFalse(keys - set(catalog), f"Missing template translations: {language}")
