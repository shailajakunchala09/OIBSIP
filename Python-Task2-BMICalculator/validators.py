"""
Input validation shared by the desktop app and the web app. Every
function returns (is_valid, value_or_error_message) so callers can
branch on the boolean without a try/except at every call site.
"""

from typing import Tuple, Union

from config import MIN_WEIGHT_KG, MAX_WEIGHT_KG, MIN_HEIGHT_M, MAX_HEIGHT_M


def validate_number(raw_value: str, field_name: str) -> Tuple[bool, Union[float, str]]:
    """Basic checks common to both weight and height: not empty, is a
    number, and not negative or zero."""
    if raw_value is None or str(raw_value).strip() == "":
        return False, f"{field_name} can't be empty"

    try:
        value = float(str(raw_value).strip())
    except ValueError:
        return False, f"{field_name} must be a number"

    if value <= 0:
        return False, f"{field_name} must be greater than zero"

    return True, value


def validate_weight(raw_value: str) -> Tuple[bool, Union[float, str]]:
    ok, result = validate_number(raw_value, "Weight")
    if not ok:
        return ok, result

    if result > MAX_WEIGHT_KG or result < MIN_WEIGHT_KG:
        return False, f"Weight should be between {MIN_WEIGHT_KG} and {MAX_WEIGHT_KG} kg"

    return True, result


def validate_height(raw_value: str) -> Tuple[bool, Union[float, str]]:
    ok, result = validate_number(raw_value, "Height")
    if not ok:
        return ok, result

    if result > MAX_HEIGHT_M or result < MIN_HEIGHT_M:
        return False, f"Height should be between {MIN_HEIGHT_M} and {MAX_HEIGHT_M} m"

    return True, result

def validate_name(raw_value: str) -> Tuple[bool, str]:
    """Names just need to exist and be a sane length - this isn't a
    security boundary, just a check against blank/junk entries."""
    if raw_value is None or raw_value.strip() == "":
        return False, "Name can't be empty"

    name = raw_value.strip()
    if len(name) > 40:
        return False, "Name is too long (max 40 characters)"

    return True, name
