# BMI Insight

**BMI Calculator · Personal Tracking · Historical Analytics**

BMI Insight is a Python-based BMI tracking application that combines real-time BMI calculation with multi-user profiles, persistent SQLite storage, historical records, and trend visualization.

The project includes both a **Flask web application** and a **Tkinter desktop application**, built around shared calculation and validation modules.

> Developed as part of the **OASIS INFOBYTE Python Programming Internship — Task 2 (Advanced Tier)**.

---

## Contents

- [Overview](#overview)
- [Features](#features)
- [Application](#application)
- [BMI Calculation](#bmi-calculation)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database](#database)
- [Validation](#validation)
- [API](#api)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Screenshots](#screenshots)
- [Deployment](#deployment)
- [Security](#security)
- [Privacy & Medical Disclaimer](#privacy--medical-disclaimer)
- [OASIS INFOBYTE Task](#oasis-infobyte-task)
- [Author](#author)

---

## Overview

BMI Insight extends the traditional BMI calculator into a lightweight personal tracking system.

A user can create a profile, enter weight and height, calculate BMI, save the measurement, review previous records, and analyze BMI and weight changes over time.

The application is designed around a simple separation of concerns:

```text
Interface
   │
   ├── Flask Web Application
   └── Tkinter Desktop Application
          │
          ▼
      Core Logic
          │
          ├── BMI Calculation
          ├── Input Validation
          └── Database Access
                  │
                  ▼
             SQLite Storage
                  │
          ┌───────┴───────┐
          ▼               ▼
       History        Analytics
