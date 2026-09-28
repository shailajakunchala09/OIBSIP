"""Unit tests for strength_analyzer.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strength_analyzer import (
    STRENGTH_MEDIUM,
    STRENGTH_STRONG,
    STRENGTH_VERY_STRONG,
    STRENGTH_WEAK,
    analyze_password,
    calculate_entropy_bits,
    classify_strength,
    strength_to_fraction,
)


class TestEntropyCalculation(unittest.TestCase):
    def test_empty_password_has_zero_entropy(self):
        self.assertEqual(calculate_entropy_bits(""), 0.0)

    def test_longer_password_has_higher_entropy(self):
        short = calculate_entropy_bits("abcDEF12")
        longer = calculate_entropy_bits("abcDEF12abcDEF12")
        self.assertGreater(longer, short)

    def test_more_diverse_password_has_higher_entropy_at_same_length(self):
        low_diversity = calculate_entropy_bits("aaaaaaaa")
        high_diversity = calculate_entropy_bits("aB3!kZ9$")
        self.assertGreater(high_diversity, low_diversity)


class TestStrengthClassification(unittest.TestCase):
    def test_low_entropy_is_weak(self):
        self.assertEqual(classify_strength(10), STRENGTH_WEAK)

    def test_mid_entropy_is_medium(self):
        self.assertEqual(classify_strength(45), STRENGTH_MEDIUM)

    def test_high_entropy_is_strong(self):
        self.assertEqual(classify_strength(70), STRENGTH_STRONG)

    def test_very_high_entropy_is_very_strong(self):
        self.assertEqual(classify_strength(100), STRENGTH_VERY_STRONG)


class TestAnalyzePassword(unittest.TestCase):
    def test_report_fields_populated(self):
        report = analyze_password("Tr0ub4dor&3XyZ!")
        self.assertGreater(report.length, 0)
        self.assertGreater(report.category_count, 0)
        self.assertGreater(report.entropy_bits, 0)
        self.assertIn(report.strength, (
            STRENGTH_WEAK, STRENGTH_MEDIUM, STRENGTH_STRONG, STRENGTH_VERY_STRONG,
        ))
        self.assertTrue(len(report.tips) > 0)

    def test_empty_password_reports_weak(self):
        report = analyze_password("")
        self.assertEqual(report.strength, STRENGTH_WEAK)
        self.assertEqual(report.length, 0)


class TestStrengthToFraction(unittest.TestCase):
    def test_fraction_increases_with_strength(self):
        weak = strength_to_fraction(STRENGTH_WEAK)
        medium = strength_to_fraction(STRENGTH_MEDIUM)
        strong = strength_to_fraction(STRENGTH_STRONG)
        very_strong = strength_to_fraction(STRENGTH_VERY_STRONG)
        self.assertLess(weak, medium)
        self.assertLess(medium, strong)
        self.assertLess(strong, very_strong)
        self.assertEqual(very_strong, 1.0)


if __name__ == "__main__":
    unittest.main()
