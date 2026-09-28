"""Unit tests for password_generator.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import AMBIGUOUS_CHARS, DIGITS, LOWERCASE, SYMBOLS, UPPERCASE
from password_generator import (
    GeneratorSettings,
    PasswordGenerationError,
    contains_all_required_categories,
    generate_password,
)
from validators import ValidationError


def make_settings(**overrides) -> GeneratorSettings:
    defaults = dict(
        length=16,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        use_symbols=True,
        exclude_ambiguous=False,
    )
    defaults.update(overrides)
    return GeneratorSettings(**defaults)


class TestExactLength(unittest.TestCase):
    def test_generated_password_matches_requested_length(self):
        for length in (8, 12, 16, 32, 64, 128):
            settings = make_settings(length=length)
            password = generate_password(settings)
            self.assertEqual(len(password), length)


class TestCategoryGuarantees(unittest.TestCase):
    def test_all_categories_present_when_all_selected(self):
        settings = make_settings()
        for _ in range(50):
            password = generate_password(settings)
            self.assertTrue(any(c in UPPERCASE for c in password))
            self.assertTrue(any(c in LOWERCASE for c in password))
            self.assertTrue(any(c in DIGITS for c in password))
            self.assertTrue(any(c in SYMBOLS for c in password))
            self.assertTrue(contains_all_required_categories(password, settings))

    def test_uppercase_only_requirement(self):
        settings = make_settings(use_upper=True, use_lower=True,
                                  use_digits=False, use_symbols=False)
        password = generate_password(settings)
        self.assertTrue(any(c in UPPERCASE for c in password))

    def test_lowercase_only_requirement(self):
        settings = make_settings(use_upper=False, use_lower=True,
                                  use_digits=True, use_symbols=False)
        password = generate_password(settings)
        self.assertTrue(any(c in LOWERCASE for c in password))

    def test_number_requirement(self):
        settings = make_settings(use_upper=True, use_lower=False,
                                  use_digits=True, use_symbols=False)
        password = generate_password(settings)
        self.assertTrue(any(c in DIGITS for c in password))

    def test_symbol_requirement(self):
        settings = make_settings(use_upper=False, use_lower=True,
                                  use_digits=False, use_symbols=True)
        password = generate_password(settings)
        self.assertTrue(any(c in SYMBOLS for c in password))

    def test_unselected_categories_never_appear(self):
        settings = make_settings(use_upper=True, use_lower=True,
                                  use_digits=False, use_symbols=False)
        for _ in range(30):
            password = generate_password(settings)
            self.assertFalse(any(c in DIGITS for c in password))
            self.assertFalse(any(c in SYMBOLS for c in password))


class TestAmbiguousExclusion(unittest.TestCase):
    def test_ambiguous_characters_excluded_when_enabled(self):
        settings = make_settings(length=64, exclude_ambiguous=True)
        for _ in range(20):
            password = generate_password(settings)
            for ch in AMBIGUOUS_CHARS:
                self.assertNotIn(ch, password)

    def test_ambiguous_characters_may_appear_when_disabled(self):
        # Not a strict guarantee any single run contains one, so we check
        # across many generations that at least one ambiguous char shows up.
        settings = make_settings(length=64, exclude_ambiguous=False)
        found_any = False
        for _ in range(50):
            password = generate_password(settings)
            if any(ch in AMBIGUOUS_CHARS for ch in password):
                found_any = True
                break
        self.assertTrue(found_any)


class TestRandomnessAndValidation(unittest.TestCase):
    def test_passwords_change_between_generations(self):
        settings = make_settings()
        passwords = {generate_password(settings) for _ in range(20)}
        # With a 16-char password from a large pool, collisions are
        # astronomically unlikely; expect all 20 to be unique.
        self.assertEqual(len(passwords), 20)

    def test_invalid_length_raises(self):
        settings = make_settings(length=4)
        with self.assertRaises(ValidationError):
            generate_password(settings)

    def test_single_category_raises(self):
        settings = make_settings(use_upper=True, use_lower=False,
                                  use_digits=False, use_symbols=False)
        with self.assertRaises(ValidationError):
            generate_password(settings)

    def test_no_category_raises(self):
        settings = make_settings(use_upper=False, use_lower=False,
                                  use_digits=False, use_symbols=False)
        with self.assertRaises(ValidationError):
            generate_password(settings)


if __name__ == "__main__":
    unittest.main()
