# BMI Insight

> A modern BMI calculator and personal health analytics application built for the **OASIS INFOBYTE Python Programming Internship — Task 2**.

BMI Insight is an advanced BMI tracking application with both a **Flask web interface** and a **Tkinter desktop application**. It calculates BMI, classifies results, stores historical measurements in SQLite, and visualizes changes over time.

---

## ✨ Features

### BMI Calculator
- Enter weight in kilograms and height in meters
- Calculate BMI instantly
- BMI rounded to 2 decimal places
- Standard BMI classification:
  - Underweight: `< 18.5`
  - Normal: `18.5 – 24.9`
  - Overweight: `25.0 – 29.9`
  - Obese: `≥ 30.0`
- Clear validation and error messages
- Color-coded BMI category feedback
- Visual BMI scale with result indicator

### Multi-User Support
- Create and select named users
- Maintain separate BMI histories for each user
- Store all records in SQLite

### History & Analytics
- View complete BMI history
- Delete individual records
- Search/filter historical measurements
- Display latest, previous, highest and lowest BMI
- Track total number of measurements
- Visualize BMI trends over time
- Visualize weight trends over time
- Export historical data from the web application

### User Experience
- Modern responsive web dashboard
- Dark, professional interface
- Responsive mobile layout
- Toast notifications
- Confirmation before deleting records
- Tkinter desktop version with light/dark theme support

### Reliability & Security
- Input validation for empty, non-numeric, zero and negative values
- Reasonable weight and height range validation
- SQLite database error handling
- Parameterized SQL queries
- No hardcoded secrets
- Flask secret key configurable through environment variables
- Debug mode disabled by default

---

## 🖥️ Application Versions

BMI Insight includes two interfaces built on the same core Python logic.

### Web Application

Built with Flask and designed as a modern analytics dashboard.

**Pages**

| Page | Description |
|---|---|
| Dashboard | BMI calculation, result card, recent records and BMI trend |
| History | Complete measurement history with search and delete |
| Analytics | BMI/weight charts and summary statistics |

### Desktop Application

Built with Tkinter and organized into three main areas:

| Section | Description |
|---|---|
| Dashboard | User selection, BMI calculation and visual result |
| History | Saved measurements with delete functionality |
| Analytics | Statistics and Matplotlib trend charts |

Both applications use the same BMI calculation and validation modules, keeping the core logic consistent across interfaces.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3 | Application logic |
| Flask | Web application and API |
| Tkinter | Desktop GUI |
| SQLite | Persistent data storage |
| Matplotlib | Desktop data visualization |
| Chart.js | Web data visualization |
| HTML5 | Web structure |
| CSS3 | Web styling |
| JavaScript | Frontend interaction |
| pytest | Automated testing |
| Gunicorn | Production web server |

---

## 🏗️ Project Architecture

```text
Python-Task2-BMICalculator/
│
├── app.py
├── desktop_app.py
├── bmi_calculator.py
├── database.py
├── validators.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── history.html
│   └── analytics.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── assets/
│
├── data/
│   └── bmi_insight.db
│
├── screenshots/
│
└── tests/
    └── test_bmi.py
