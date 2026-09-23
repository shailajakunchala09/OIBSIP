"""
Central place for constants used across the desktop app, the web app and
the database layer. Keeping these here means the BMI thresholds, colours
and file paths only need to change in one spot.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "bmi_insight.db")

# BMI category boundaries (kg/m^2), per WHO's standard adult classification
BMI_UNDERWEIGHT_MAX = 18.5
BMI_NORMAL_MAX = 24.9
BMI_OVERWEIGHT_MAX = 29.9

BMI_DISCLAIMER = (
    "BMI is a general screening measure and does not replace professional "
    "medical advice."
)

# Reasonable sanity bounds for manual input. These aren't medical limits,
# just guardrails against obvious typos (e.g. a weight of 5000 kg).
MIN_WEIGHT_KG = 1.0
MAX_WEIGHT_KG = 500.0
MIN_HEIGHT_M = 0.3
MAX_HEIGHT_M = 10.0

# Colour system shared by the desktop app (used directly) and roughly
# mirrored in static/css/style.css for the web app.
COLORS = {
    "light": {
        "bg": "#F5F6FA",
        "surface": "#FFFFFF",
        "text": "#1B1F3B",
        "muted": "#6B7280",
        "border": "#E3E6EF",
        "accent": "#3B4CCA",
        "accent_dark": "#2B3699",
        "underweight": "#4A90D9",
        "normal": "#2FA36B",
        "overweight": "#E0A526",
        "obese": "#D9534F",
    },
    "dark": {
        "bg": "#12142B",
        "surface": "#1B1E3F",
        "text": "#EDEFF7",
        "muted": "#9BA0C4",
        "border": "#2E325C",
        "accent": "#6C7CF0",
        "accent_dark": "#4C5BD4",
        "underweight": "#6FA8DC",
        "normal": "#4CC08A",
        "overweight": "#F0B94D",
        "obese": "#E57373",
    },
}

FLASK_SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
