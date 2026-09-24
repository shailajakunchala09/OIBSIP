# 🧮 BMI Insight

<p align="center">
  <img src="https://img.icons8.com/fluency/96/weight-scale.png" width="85" alt="BMI Insight Logo">
</p>

<p align="center">
  <strong>Personal BMI Tracking & Health Analytics</strong>
  <br>
</p>

<p align="center">
  A Python-based BMI calculator and personal health analytics application
  with multi-user support, persistent SQLite storage, historical tracking,
  and BMI trend visualization through both web and desktop interfaces.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Tkinter-2C2C2C?style=for-the-badge" alt="Tkinter">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=python&logoColor=white" alt="Matplotlib">
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chart.js&logoColor=white" alt="Chart.js">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
</p>

---

### LIVE DEMO:

**Coming Soon**

---

## About

BMI Insight is a Python-based application designed to provide a simple, organized, and persistent way to calculate and track Body Mass Index (BMI).

Instead of calculating a BMI value once and losing the result, users can create named profiles, record multiple measurements, view their previous records, and analyze BMI and weight changes over time.

The project provides both a **Flask web application** and a **Tkinter desktop application**, using shared calculation, validation, and SQLite database logic.

The application is developed as part of the **OASIS INFOBYTE Python Programming Internship — Task 2 (Advanced Tier)**.

---

## Why This Project?

A basic BMI calculator performs a calculation and displays a result.

BMI Insight extends this concept into a small personal tracking and analytics system by adding persistent storage, multiple user profiles, historical records, and trend visualization.

### Advantages

- Simple and clear BMI calculation
- Separate records for multiple users
- Persistent history using SQLite
- BMI and weight trend visualization
- Web and desktop interfaces
- Input validation and error handling
- Modular and reusable Python code
- Automated testing for core functionality

---

## Key Features

| Feature | Description |
|---|---|
| ⚖️ BMI Calculator | Calculates BMI from weight and height |
| 📊 BMI Classification | Classifies BMI into standard health categories |
| 👤 Multi-User Support | Allows separate named user profiles |
| 💾 SQLite Storage | Stores BMI records persistently |
| 📋 History | Displays previous BMI measurements |
| 🔎 Search & Filter | Filters historical records in the web application |
| 🗑️ Delete Records | Removes individual historical measurements |
| 📈 BMI Trend | Visualizes BMI measurements over time |
| ⚖️ Weight Trend | Visualizes weight changes over time |
| 📊 Analytics | Displays BMI summary statistics |
| 🎨 Color-Coded Result | Provides visual category feedback |
| 📏 BMI Scale | Shows the result on a visual BMI scale |
| 🌐 Web Application | Flask-based responsive web dashboard |
| 🖥️ Desktop Application | Tkinter-based graphical application |
| 🌗 Theme Support | Light and dark theme support in desktop application |
| 🔔 Notifications | User feedback and delete confirmations |
| ⚠️ Error Handling | Handles invalid input and database errors |
| 🧪 Automated Testing | Core logic tested using pytest |

---

### Technology Stack

## Backend

Python 3  
Flask  
SQLite  
sqlite3  

## Desktop GUI

Tkinter  
Matplotlib  

## Frontend

HTML5  
CSS3  
JavaScript  
Chart.js  

## Testing

pytest  

## Deployment

Gunicorn  
Git  
GitHub  

## Development

Python Virtual Environment  
JSON  
Environment Variables  

---

## BMI Calculation

BMI is calculated using the standard formula:

```text
BMI = Weight / Height²
