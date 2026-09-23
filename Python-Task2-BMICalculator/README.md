# BMI Insight

Personal Health & Fitness Analytics - a BMI calculator built for the
**OASIS INFOBYTE Python Programming Internship**, Task 2.

This is the Advanced Tier version of the BMI Calculator task: a desktop
app (Tkinter) and a web app (Flask) that share the same calculation and
validation code, both backed by SQLite so BMI history actually persists
between sessions instead of disappearing when the window closes.

## Why I built this project

The beginner version of this task is just "take weight and height,
print the BMI." That's a fine starting point, but it doesn't really
show much beyond basic arithmetic. I wanted to push it further and
build something closer to a real small health-tracking tool: multiple
people using the same app, a proper history instead of a single
one-off result, and some way to actually see how a person's BMI
changes over time rather than just staring at one number. That's
where the SQLite storage and the trend charts came from - they weren't
in the brief just to pad the feature list, they're what makes "BMI
Calculator" into "BMI *Insight*."

## What the application does

You pick (or add) a user, type in a weight and height, and hit
Calculate. The app validates the input, works out the BMI, classifies
it into a category, and saves the result to that user's history. From
there you can look back at previous records, delete ones you don't
want, or check the analytics tab/page to see BMI and weight trends
over time.

## Key features

- Weight (kg) and height (m) input with a Calculate button
- BMI computed as `weight / height²`, rounded to 2 decimal places
- Category classification: Underweight, Normal, Overweight, Obese
- Input validation: empty fields, non-numeric values, negative
  numbers, zero height, and unreasonable values are all rejected with
  a clear message instead of crashing the app
- Visual result feedback - a colour-coded category badge and a BMI
  scale bar with a marker showing where the result sits

## Advanced features

- Multiple named users, each with their own independent history
- BMI records saved to a SQLite database (not just kept in memory)
- Full history view per user, with the ability to delete individual
  records
- BMI trend and weight trend charts (Matplotlib on desktop, Chart.js
  on the web version)
- Summary statistics: latest, previous, highest, lowest BMI, and total
  record count
- CSV export of a user's history (web version)
- Search/filter through history by category or date (web version)
- Light/dark theme toggle (desktop version)
- Toast notifications and confirmation prompts before deleting records
  (web version)
- Database error handling throughout - connection issues, insert
  failures, and read failures show a message instead of a stack trace

## Screenshots

Screenshots aren't included in this repository yet - see
[`screenshots/README.md`](screenshots/README.md) for exactly what to
capture and how, before this gets pushed as a finished submission.

| | |
|---|---|
| Dashboard | `screenshots/01-dashboard.png` |
| BMI result | `screenshots/02-bmi-result.png` |
| History | `screenshots/03-history.png` |
| Analytics | `screenshots/04-analytics.png` |
| Mobile view | `screenshots/05-mobile-view.png` |

## Desktop application

Built with Tkinter, split into three tabs:

- **Dashboard** - user selector, add-user dialog, weight/height inputs,
  Calculate/Reset buttons, and the result card with the category badge
  and BMI scale
- **History** - a table of every saved record for the selected user,
  with refresh and delete-selected controls
- **Analytics** - summary stat cards plus BMI and weight trend charts
  rendered with Matplotlib, embedded directly in the window

There's a light/dark mode toggle in the header, and the window resizes
properly instead of clipping content.

## Web live demo

A Flask version of the same idea, styled as a dark navy/indigo
dashboard rather than a plain form. It's meant to double as the "live
demo" link for the internship submission.

Pages:

- **Dashboard** (`/`) - calculate a BMI and see recent records
- **History** (`/history`) - full history with search and CSV export
- **Analytics** (`/analytics`) - stats and trend charts (Chart.js)

The desktop and web versions call the exact same `bmi_calculator.py`
and `validators.py` functions, so a BMI of 22.86 for 70kg/1.75m on one
is a BMI of 22.86 on the other too - there's no duplicated, slightly
different logic hiding in either interface.

## Technology stack

- **Python 3** - core language
- **Tkinter** - desktop GUI
- **Flask** - web app and REST-ish JSON API
- **SQLite** (`sqlite3`, standard library) - persistent storage
- **Matplotlib** - trend charts in the desktop app
- **Chart.js** (via CDN) - trend charts in the web app
- **HTML / CSS / vanilla JS** - web front end, no frontend framework
- **pytest** - automated tests
- **Gunicorn** - production server for deployment

## How the application works

1. A user is selected or created (`users` table).
2. Weight and height are validated (`validators.py`) - empty, non-numeric,
   negative, zero-height, and out-of-range values are all caught before
   anything is calculated.
3. `bmi_calculator.py` computes the BMI and its category.
4. The record is saved to `bmi_records`, linked to the user.
5. History and analytics views read that same table back and render it
   as a table, and as a chart summarising the trend.

## Project structure

```
Python-Task2-BMICalculator/
│
├── app.py                 # Flask web app + JSON API
├── desktop_app.py          # Tkinter desktop app
├── bmi_calculator.py       # BMI formula + categorisation
├── database.py             # SQLite access layer
├── validators.py           # Input validation
├── config.py                # Shared constants (colours, thresholds, paths)
├── requirements.txt
├── .gitignore
├── README.md
│
├── templates/
│   ├── base.html           # Shared sidebar layout
│   ├── index.html          # Dashboard
│   ├── history.html
│   └── analytics.html
│
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── assets/
│
├── data/                   # SQLite database lives here (gitignored)
│
├── screenshots/
│
└── tests/
    └── test_bmi.py
```

## Database design

Two tables, linked by `user_id`:

**users**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| name | TEXT | Unique |
| created_at | TEXT | Set automatically |

**bmi_records**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key → users.id |
| weight | REAL | kg |
| height | REAL | m |
| bmi | REAL | Rounded to 2 decimals |
| category | TEXT | Underweight / Normal / Overweight / Obese |
| created_at | TEXT | Set automatically |

All queries go through parameterised statements in `database.py` - no
string-formatted SQL anywhere in the project.

## Installation

```bash
git clone <this-repo-url>
cd OIBSIP/Python-Task2-BMICalculator
```

### Virtual environment setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Running the desktop application

```bash
python desktop_app.py
```

The SQLite database is created automatically on first run, at
`data/bmi_insight.db`.

### Running the Flask application

```bash
python app.py
```

Then open `http://localhost:5000` in a browser.

### Testing

```bash
python -m pytest tests/test_bmi.py -v
```

Tests cover the BMI formula, category boundaries (including the exact
18.5/24.9/25.0/29.9/30.0 edges), decimal weights/heights, and all the
validation rejection cases (empty, non-numeric, negative, zero height,
out-of-range).

## Usage examples

```python
from bmi_calculator import calculate_bmi, categorize_bmi

bmi = calculate_bmi(70, 1.75)      # 22.86
category = categorize_bmi(bmi)     # "Normal"
```

```python
from validators import validate_weight

ok, result = validate_weight("-5")
# ok is False, result is "Weight must be greater than zero"
```

## Validation / error handling

- Empty weight/height fields are rejected before any calculation runs
- Non-numeric input (letters, symbols) is caught with `try/except`
  around the float conversion, not left to crash the app
- Negative values and zero height/weight are explicitly checked, since
  `weight / height**2` would otherwise raise a `ZeroDivisionError` or
  silently produce a nonsense BMI
- Values outside a sane human range (e.g. 900kg) are flagged too, since
  they're almost certainly typos
- Database errors (connection issues, failed inserts, failed reads,
  failed deletes) are caught in `database.py` and re-raised as a plain
  `DatabaseError` with a readable message - no raw `sqlite3` tracebacks
  reach the UI

## Privacy / security

- No hardcoded secrets or passwords anywhere in the source
- The Flask secret key is read from an environment variable, with a
  clearly-labelled dev-only fallback for local use
- All SQL is parameterised
- No `eval()`, no shell execution
- Debug mode is off unless `FLASK_DEBUG=1` is explicitly set
- The database file lives under `data/` and is excluded from Git

## BMI disclaimer

> BMI is a general screening measure and does not replace professional
> medical advice.

This app doesn't diagnose anything, doesn't give treatment advice, and
doesn't claim BMI on its own is a complete picture of someone's health
- it's a simple, widely-used screening number and nothing more.

## Future improvements

- Body fat % / waist-to-hip ratio as additional metrics alongside BMI
- Exporting analytics charts as images, not just raw CSV data
- Optional user authentication if this ever moved beyond a local/demo tool
- Unit toggle for pounds/inches for users outside metric-only countries

## Learning outcomes

This task was a good excuse to actually practice separating logic from
interface - the same `bmi_calculator.py` and `validators.py` are used
untouched by both a Tkinter app and a Flask app, which forced me to
keep those modules free of anything UI-specific. It was also the first
time I've wired up Matplotlib inside a Tkinter window rather than just
saving a chart to a file, and the first time I've built a small JSON
API by hand instead of just server-rendering everything.

## Developer

**Kunchala Shailaja**
Python Programming Internship - OASIS INFOBYTE

## Project status

Complete for Task 2 submission. Working desktop app, working web app,
passing tests, and no outstanding TODOs in the core feature set.
