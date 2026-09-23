"""
The actual BMI maths. Deliberately tiny and dependency-free so both the
desktop app and the Flask app can import it without pulling in Tkinter
or Flask.
"""

from config import BMI_UNDERWEIGHT_MAX, BMI_NORMAL_MAX, BMI_OVERWEIGHT_MAX


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Return BMI rounded to 2 decimal places.

    Raises ValueError if height is zero or negative, since dividing by
    zero (or a negative height, which is meaningless) shouldn't be
    silently handled here - the caller is expected to validate input
    before reaching this point.
    """
    if height_m <= 0:
        raise ValueError("Height must be greater than zero")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero")

    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)


def categorize_bmi(bmi: float) -> str:
    """Map a BMI value to the standard WHO adult category."""
    if bmi < BMI_UNDERWEIGHT_MAX:
        return "Underweight"
    if bmi <= BMI_NORMAL_MAX:
        return "Normal"
    if bmi <= BMI_OVERWEIGHT_MAX:
        return "Overweight"
    return "Obese"


def category_position(bmi: float) -> float:
    """Return a 0-1 position for placing a marker on a BMI scale bar.

    The scale is anchored at 15 (low end of underweight) and 40 (deep
    obesity range), which is enough to place almost any real-world
    reading without the marker running off either edge.
    """
    scale_min, scale_max = 15.0, 40.0
    clamped = max(scale_min, min(bmi, scale_max))
    return (clamped - scale_min) / (scale_max - scale_min)
