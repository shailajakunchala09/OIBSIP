"""
Tests for the calculation and validation logic. Run with:

    python -m pytest tests/test_bmi.py -v

These deliberately don't touch the database or the GUI - just the pure
functions in bmi_calculator.py and validators.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from bmi_calculator import calculate_bmi, categorize_bmi
from validators import validate_weight, validate_height, validate_name


class TestCalculateBMI:
    def test_known_value(self):
        # 70kg at 1.75m is a commonly quoted textbook example (~22.86)
        assert calculate_bmi(70, 1.75) == 22.86

    def test_rounds_to_two_decimals(self):
        result = calculate_bmi(68, 1.72)
        assert result == round(68 / (1.72 ** 2), 2)
        assert len(str(result).split(".")[-1]) <= 2

    def test_decimal_inputs(self):
        result = calculate_bmi(55.5, 1.60)
        assert result == round(55.5 / (1.60 ** 2), 2)

    def test_zero_height_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(70, 0)

    def test_negative_height_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(70, -1.5)

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(-10, 1.7)

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(0, 1.7)


class TestCategorizeBMI:
    def test_underweight(self):
        assert categorize_bmi(17.0) == "Underweight"

    def test_underweight_boundary(self):
        # just below 18.5 is still underweight
        assert categorize_bmi(18.49) == "Underweight"

    def test_normal_lower_boundary(self):
        assert categorize_bmi(18.5) == "Normal"

    def test_normal_upper_boundary(self):
        assert categorize_bmi(24.9) == "Normal"

    def test_overweight_lower_boundary(self):
        assert categorize_bmi(25.0) == "Overweight"

    def test_overweight_upper_boundary(self):
        assert categorize_bmi(29.9) == "Overweight"

    def test_obese_boundary(self):
        assert categorize_bmi(30.0) == "Obese"

    def test_very_high_bmi(self):
        assert categorize_bmi(45.0) == "Obese"


class TestValidateWeight:
    def test_valid_weight(self):
        ok, value = validate_weight("68.5")
        assert ok is True
        assert value == 68.5

    def test_empty_weight(self):
        ok, message = validate_weight("")
        assert ok is False
        assert "empty" in message.lower()

    def test_non_numeric_weight(self):
        ok, message = validate_weight("abc")
        assert ok is False
        assert "number" in message.lower()

    def test_negative_weight(self):
        ok, message = validate_weight("-5")
        assert ok is False

    def test_zero_weight(self):
        ok, message = validate_weight("0")
        assert ok is False

    def test_unreasonably_high_weight(self):
        ok, message = validate_weight("900")
        assert ok is False


class TestValidateHeight:
    def test_valid_height(self):
        ok, value = validate_height("1.75")
        assert ok is True
        assert value == 1.75

    def test_zero_height(self):
        ok, message = validate_height("0")
        assert ok is False

    def test_negative_height(self):
        ok, message = validate_height("-1.5")
        assert ok is False

    def test_non_numeric_height(self):
        ok, message = validate_height("tall")
        assert ok is False

    def test_unreasonably_tall(self):
        ok, message = validate_height("5")
        assert ok is False


class TestValidateName:
    def test_valid_name(self):
        ok, value = validate_name("Shailaja")
        assert ok is True
        assert value == "Shailaja"

    def test_empty_name(self):
        ok, message = validate_name("   ")
        assert ok is False

    def test_trims_whitespace(self):
        ok, value = validate_name("  Kunchala  ")
        assert ok is True
        assert value == "Kunchala"
