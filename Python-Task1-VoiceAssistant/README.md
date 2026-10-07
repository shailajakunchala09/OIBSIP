# 🎙️ Voice Assistant

<p align="center">
  <b>Intelligent Voice Interaction &amp; Personal Assistant</b><br/>
  <i>Interact naturally through voice, text, and useful everyday commands.</i>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white">
  <img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript&logoColor=black">
  <img alt="HTML5" src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white">
  <img alt="CSS3" src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white">
  <img alt="Status" src="https://img.shields.io/badge/Status-Complete-16a34a">
  <img alt="Internship" src="https://img.shields.io/badge/OASIS%20INFOBYTE-Task%201-7c3aed">
</p>

---

## Live Demo:

### https://voiceassistant-oibsip.onrender.com/

---

## 📖 Project Overview

**Voice Assistant** is a Python and Flask-based intelligent assistant developed for
**OASIS INFOBYTE's Python Programming Internship — Task 1: Voice Assistant**.

The application provides a convenient way to interact with an assistant through
voice commands and text. It processes user requests, identifies supported tasks,
performs the required action, and provides responses through the web interface
and voice feedback.

The project combines **speech recognition, text-to-speech, natural-language
command processing, web search, weather information, reminders, knowledge
responses, email communication, custom commands, and a responsive web
interface** into a single application.

---

## 🎯 Why This Project?

Traditional computer interaction often requires users to type requests manually
or switch between multiple applications.

This project explores how voice-based interaction can make common tasks more
natural and convenient by allowing users to communicate with an assistant using
spoken commands.

The project also provides practical experience in integrating a Python backend,
web technologies, APIs, browser capabilities, and external services into one
application.

---

## ✨ Key Features

- 🎤 **Voice Input** — Accepts spoken commands through a microphone
- 🗣️ **Voice Response** — Provides spoken feedback using text-to-speech
- 💬 **Conversation Interface** — Displays user requests and assistant responses
- 🕐 **Date & Time** — Provides the current date and time
- 🔎 **Web Search** — Searches the web for requested information
- 🌤️ **Weather Information** — Retrieves weather information through an API
- 🧠 **Knowledge Responses** — Handles supported general and technical questions
- ⏰ **Reminders** — Creates timed reminders with audible alerts
- ✉️ **Email Support** — Sends emails through SMTP
- ⚙️ **Custom Commands** — Supports configurable commands through JSON
- 🌓 **Theme Support** — Provides System, Light, and Dark themes
- ⚠️ **Error Handling** — Handles microphone and speech-related errors gracefully
- 📱 **Responsive Interface** — Provides a clean web-based user interface

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Backend | Flask |
| Frontend | HTML5, CSS3, JavaScript |
| Voice Input | Speech Recognition, Browser Speech Recognition |
| Voice Output | pyttsx3, Browser Speech Synthesis |
| Weather | OpenWeatherMap API |
| Email | SMTP |
| Configuration | JSON, Environment Variables |
| Development | Git, GitHub, Python Virtual Environment |

---

## 🏗 Architecture

The application connects the web interface with the Python backend and external
services to process voice and text-based requests.

```text
User
  │
  ▼
Web Interface
  │
  ├── Voice Input
  ├── Text Input
  └── User Commands
          │
          ▼
      Flask Backend
          │
          ▼
   Voice Assistant Logic
          │
    ┌─────┼──────────────┐
    ▼     ▼              ▼
Commands  APIs       External Services
    │     │              │
    │     ├── Weather    └── SMTP Email
    │     └── Web Search
    │
    ▼
Assistant Response
    │
    ├── Text Response
    └── Voice Response

📁 Project Structure
Python-Task1-VoiceAssistant/
├── app.py
├── voice_assistant.py
├── commands.json
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── mic_test.py
│
├── screenshots/
│   ├── 01-voice-assistant-home.png
│   ├── 02-voice-assistant-listening.png
│   ├── 03-voice-assistant-response.png
│   └── 04-voice-assistant-commands.png
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── app.js

🗂 File Overview
| File                   | Responsibility                                          |
| ---------------------- | ------------------------------------------------------- |
| `app.py`               | Flask application and backend functionality             |
| `voice_assistant.py`   | Desktop voice-assistant implementation                  |
| `commands.json`        | Configurable command definitions                        |
| `templates/index.html` | Main web interface                                      |
| `static/style.css`     | Interface styling and responsive design                 |
| `static/app.js`        | Browser interaction and voice functionality             |
| `requirements.txt`     | Python dependencies                                     |
| `.env.example`         | Environment configuration template                      |
| `mic_test.py`          | Microphone testing utility                              |
| `.gitignore`           | Prevents local and sensitive files from being committed |


🔐 Configuration & Environment

The application uses environment variables for configuration and sensitive
information.

A template is provided in:

.env.example

Create a local .env file when required and configure the necessary API or
email-related values.

Security: Never commit real API keys, passwords, or other sensitive
credentials to GitHub.

⚠️ Validation & Error Handling

The application includes handling for common voice-assistant issues such as:

Microphone-related errors
Speech recognition failures
Invalid or unsupported commands
API-related failures
Email-related errors
Unexpected assistant responses

The goal is to provide useful feedback instead of allowing the application to
terminate unexpectedly.

📸 Screenshots
01. Home Interface

02. Voice Listening

03. Assistant Response

04. Available Commands

▶️ How to Run
python app.py
⚙️ Installation

Clone the repository:

git clone https://github.com/shailajakunchala09/OIBSIP.git

Navigate to the project:

cd OIBSIP/Python-Task1-VoiceAssistant

Create a virtual environment:

python -m venv .venv

Activate the virtual environment on Windows:

.venv\Scripts\activate

Install the required dependencies:

pip install -r requirements.txt

Start the application:

python app.py
🕹 Usage
Start the Flask application.
Open the application in a web browser.
Allow microphone access when prompted.
Enter a command using voice or text.
The assistant processes the request.
View the response in the conversation interface.
Use supported features such as weather, web search, reminders, email, and
custom commands.
🚀 Future Enhancements
Conversational memory
Improved intent classification
Enhanced natural-language understanding
Additional API integrations
Expanded custom command support
Personalized user preferences
Advanced reminder management
Improved contextual conversations
🎓 Learning Outcomes

Building this project provided practical experience in:

Python application development
Flask web application development
Speech recognition and text-to-speech
Frontend and backend integration
API integration
SMTP email integration
JSON-based configuration
Environment variable management
Error handling
Git and GitHub workflow
Deploying a Python web application
👩‍💻 Developer

Kunchala Shailaja

BCA Graduate | Python Programming | AI/ML Learner

🔗 GitHub:
https://github.com/shailajakunchala09

📌 Project Status

✅ Complete — OASIS INFOBYTE Python Programming Internship
Task 1: Voice Assistant


This is much closer to the **VaultForge README style** while remaining specific to your Voice Assistant.

**Don't commit this yet.** Replace your current `README.md` with this version, save it, and then run:

