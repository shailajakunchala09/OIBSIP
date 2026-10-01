import unittest

from errors import ValidationError
from validators import validate_city


class ValidateCityTests(unittest.TestCase):
    def test_empty_and_whitespace_are_rejected(self):
        for raw in ("", "   ", "\t\n", None):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                validate_city(raw)

    def test_valid_names_are_normalised(self):
        self.assertEqual(validate_city("  London  "), "London")
        self.assertEqual(validate_city("New    York"), "New York")
        self.assertEqual(validate_city("São Paulo"), "São Paulo")
        self.assertEqual(validate_city("St. John's"), "St. John's")
        self.assertEqual(validate_city("Paris, FR"), "Paris, FR")
        self.assertEqual(validate_city("Stratford-upon-Avon"), "Stratford-upon-Avon")

    def test_invalid_characters_are_rejected(self):
        for raw in ("Lon<don>", "12345", "Paris; DROP TABLE", "city@home", "a1b2"):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                validate_city(raw)

    def test_too_short_and_too_long(self):
        with self.assertRaises(ValidationError):
            validate_city("A")
        with self.assertRaises(ValidationError):
            validate_city("x" * 101)


if __name__ == "__main__":
    unittest.main()
