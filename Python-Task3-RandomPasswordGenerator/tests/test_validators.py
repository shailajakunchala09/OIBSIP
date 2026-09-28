"""Unit tests for validators.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validators import (
    ValidationError,
    validate_character_selection,
    validate_length,
    validate_settings,
)


class TestValidateLength(unittest.TestCase):
    def test_minimum_length_accepted(self):
        validate_length(8)  # should not raise

    def test_below_minimum_rejected(self):
        with self.assertRaises(ValidationError):
            validate_length(7)

    def test_zero_length_rejected(self):
        with self.assertRaises(ValidationError):
            validate_length(0)

    def test_negative_length_rejected(self):
        with self.assertRaises(ValidationError):
            validate_length(-5)

    def test_above_maximum_rejected(self):
        with self.assertRaises(ValidationError):
            validate_length(129)

    def test_maximum_length_accepted(self):
        validate_length(128)  # should not raise

    def test_non_integer_rejected(self):
        with self.assertRaises(ValidationError):
            validate_length("16")  # type: ignore[arg-type]

    def test_boolean_rejected(self):
        # bool is technically an int subclass in Python; must be rejected.
        with self.assertRaises(ValidationError):
            validate_length(True)  # type: ignore[arg-type]

    def test_custom_bounds_respected(self):
        validate_length(10, min_len=10, max_len=20)
        with self.assertRaises(ValidationError):
            validate_length(9, min_len=10, max_len=20)
        with self.assertRaises(ValidationError):
            validate_length(21, min_len=10, max_len=20)


class TestValidateCharacterSelection(unittest.TestCase):
    def test_no_categories_rejected(self):
        with self.assertRaises(ValidationError):
            validate_character_selection(False, False, False, False)

    def test_single_category_rejected(self):
        with self.assertRaises(ValidationError):
            validate_character_selection(True, False, False, False)

    def test_two_categories_accepted(self):
        validate_character_selection(True, True, False, False)  # no raise

    def test_all_categories_accepted(self):
        validate_character_selection(True, True, True, True)  # no raise


class TestValidateSettings(unittest.TestCase):
    def test_valid_settings_pass(self):
        validate_settings(16, True, True, True, True)  # no raise

    def test_invalid_length_raises(self):
        with self.assertRaises(ValidationError):
            validate_settings(4, True, True, False, False)

    def test_invalid_selection_raises(self):
        with self.assertRaises(ValidationError):
            validate_settings(16, True, False, False, False)


if __name__ == "__main__":
    unittest.main()
