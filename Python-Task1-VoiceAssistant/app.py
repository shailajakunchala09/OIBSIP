import json
import os
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request


load_dotenv()

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

WEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY", ""
).strip()

SMTP_HOST = os.getenv(
    "SMTP_HOST", ""
).strip()

SMTP_PORT = int(
    os.getenv("SMTP_PORT", "2525")
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME", ""
).strip()

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD", ""
).strip()

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS", ""
).strip()

COMMANDS_FILE = "commands.json"


# =========================================================
# CUSTOM COMMANDS
# =========================================================

def load_custom_commands():
    try:
        if not os.path.exists(COMMANDS_FILE):
            return {}

        with open(
            COMMANDS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except Exception as error:
        print(f"Custom command error: {error}")
        return {}


CUSTOM_COMMANDS = load_custom_commands()


# =========================================================
# DATE / TIME
# =========================================================

def get_part_of_day():
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Good morning"

    if 12 <= hour < 17:
        return "Good afternoon"

    return "Good evening"


def get_current_date():
    return datetime.now().strftime(
        "%A, %B %d, %Y"
    )


def get_current_time():
    return datetime.now().strftime(
        "%I:%M %p"
    ).lstrip("0")


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(text):
    text = text.lower().strip()

    # Greeting
    greeting_patterns = [
        "hi",
        "hello",
        "hey",
        "hai",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you"
    ]

    if any(
        text == item or text.startswith(item + " ")
        for item in greeting_patterns
    ):
        return "greeting"

    # Time
    time_patterns = [
        "what time is it",
        "what is the time",
        "current time",
        "tell me the time",
        "time right now",
        "what time",
        "the time"
    ]

    if any(
        pattern in text
        for pattern in time_patterns
    ):
        return "time"

    # Date
    date_patterns = [
        "today's date",
        "todays date",
        "current date",
        "what is the date",
        "what's the date",
        "what day is it",
        "which day is it",
        "date today"
    ]

    if any(
        pattern in text
        for pattern in date_patterns
    ):
        return "date"

    # Weather
    weather_patterns = [
        "weather",
        "temperature",
        "forecast",
        "how hot",
        "how cold",
        "climate"
    ]

    if any(
        pattern in text
        for pattern in weather_patterns
    ):
        return "weather"

    # Search
    search_patterns = [
        "search for",
        "search",
        "look up",
        "lookup",
        "google"
    ]

    if any(
        text.startswith(pattern)
        for pattern in search_patterns
    ):
        return "search"

    # Reminder
    reminder_patterns = [
        "remind me",
        "set a reminder",
        "reminder",
        "remind"
    ]

    if any(
        pattern in text
        for pattern in reminder_patterns
    ):
        return "reminder"

    # Email
    email_patterns = [
        "send an email",
        "send email",
        "email"
    ]

    if any(
        pattern in text
        for pattern in email_patterns
    ):
        return "email"

    # Knowledge
    knowledge_patterns = [
        "what is",
        "who is",
        "define",
        "tell me about",
        "explain"
    ]

    if any(
        text.startswith(pattern)
        for pattern in knowledge_patterns
    ):
        return "knowledge"

    # Exit
    exit_patterns = [
        "exit",
        "quit",
        "goodbye",
        "bye",
        "close assistant",
        "stop assistant"
    ]

    if any(
        pattern in text
        for pattern in exit_patterns
    ):
        return "exit"

    # Custom commands
    for command_name in CUSTOM_COMMANDS:
        if command_name.lower() in text:
            return "custom"

    return "unknown"


# =========================================================
# SEARCH
# =========================================================

def extract_search_query(text):
    prefixes = [
        "search for ",
        "search ",
        "look up ",
        "lookup ",
        "google "
    ]

    lower_text = text.lower()

    for prefix in prefixes:
        if lower_text.startswith(prefix):
            return text[len(prefix):].strip()

    return text.strip()


def search_result(query):
    query = query.strip()

    if not query:
        return {
            "success": False,
            "message": "What would you like me to search for?"
        }

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    return {
        "success": True,
        "message": f"Searching the web for {query}.",
        "query": query,
        "url": url
    }


# =========================================================
# WEATHER
# =========================================================

def get_weather(city="Hyderabad"):
    if not WEATHER_API_KEY:
        return {
            "success": False,
            "message": "Weather service is not configured."
        }

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": "I couldn't get the weather right now."
            }

        data = response.json()

        description = data["weather"][0]["description"]
        temperature = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        message = (
            f"The weather in {city} is {description}. "
            f"The temperature is {temperature} degrees Celsius, "
            f"feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent, "
            f"with wind speed of {wind_speed} meters per second."
        )

        return {
            "success": True,
            "message": message,
            "city": city,
            "temperature": temperature,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "description": description
        }

    except requests.RequestException:
        return {
            "success": False,
            "message": "I couldn't connect to the weather service."
        }


# =========================================================
# KNOWLEDGE
# =========================================================

KNOWLEDGE_BASE = {
    "python": (
        "Python is a high-level general-purpose programming "
        "language known for its readable syntax and wide range "
        "of applications."
    ),
    "artificial intelligence": (
        "Artificial intelligence is the field of creating "
        "computer systems that can perform tasks that normally "
        "require human intelligence."
    ),
    "machine learning": (
        "Machine learning is a branch of artificial intelligence "
        "where systems learn patterns from data to make "
        "predictions or decisions."
    ),
    "data science": (
        "Data science combines programming, statistics and "
        "domain knowledge to analyze data and generate useful insights."
    ),
    "html": (
        "HTML stands for HyperText Markup Language and is used "
        "to structure web pages."
    ),
    "css": (
        "CSS stands for Cascading Style Sheets and controls "
        "the appearance and layout of websites."
    ),
    "javascript": (
        "JavaScript is a programming language commonly used "
        "to create interactive websites."
    ),
    "flask": (
        "Flask is a lightweight Python framework used to build "
        "web applications."
    ),
    "github": (
        "GitHub is a platform for hosting, managing and "
        "collaborating on software projects."
    )
}


def answer_knowledge(question):
    lower_question = question.lower()

    for topic, answer in KNOWLEDGE_BASE.items():
        if topic in lower_question:
            return answer

    return (
        "I don't have a specific answer in my local knowledge "
        "base. You can use web search to learn more."
    )


# =========================================================
# REMINDER
# =========================================================

def parse_reminder(text):
    pattern = re.search(
        r"(?:in)\s+(\d+)\s*"
        r"(seconds?|secs?|minutes?|mins?|hours?|hrs?)"
        r"(?:\s+(?:to|for)\s+(.+))?$",
        text,
        re.IGNORECASE
    )

    if not pattern:
        return None

    amount = int(pattern.group(1))
    unit = pattern.group(2).lower()

    message = (
        pattern.group(3)
        or "your reminder"
    ).strip()

    if (
        unit.startswith("second") or
        unit.startswith("sec")
    ):
        seconds = amount

    elif (
        unit.startswith("minute") or
        unit.startswith("min")
    ):
        seconds = amount * 60

    else:
        seconds = amount * 3600

    return {
        "seconds": seconds,
        "message": message
    }


# =========================================================
# EMAIL
# =========================================================

def send_email(recipient, subject, body):
    if not all([
        SMTP_HOST,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        EMAIL_ADDRESS
    ]):
        return {
            "success": False,
            "message": "Email service is not configured."
        }

    if not recipient:
        return {
            "success": False,
            "message": "Please provide a recipient email address."
        }

    try:
        email = EmailMessage()

        email["From"] = EMAIL_ADDRESS
        email["To"] = recipient
        email["Subject"] = (
            subject or "Voice Assistant Email"
        )

        email.set_content(
            body or "Sent from my Voice Assistant."
        )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=15
        ) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(email)

        return {
            "success": True,
            "message": "The email has been sent successfully."
        }

    except Exception as error:
        print(f"Email error: {error}")

        return {
            "success": False,
            "message": "I couldn't send the email right now."
        }


# =========================================================
# COMMAND HANDLER
# =========================================================

def handle_command(text):
    text = (text or "").strip()

    if not text:
        return {
            "success": False,
            "intent": "unknown",
            "message": "I didn't receive anything. Please try again."
        }

    intent = detect_intent(text)

    if intent == "greeting":
        return {
            "success": True,
            "intent": "greeting",
            "message": (
                f"{get_part_of_day()}! "
                "Hello! How can I help you?"
            )
        }

    if intent == "time":
        return {
            "success": True,
            "intent": "time",
            "message": (
                f"The current time is {get_current_time()}."
            )
        }

    if intent == "date":
        return {
            "success": True,
            "intent": "date",
            "message": (
                f"Today is {get_current_date()}."
            )
        }

    if intent == "search":
        query = extract_search_query(text)

        return {
            **search_result(query),
            "intent": "search"
        }

    if intent == "weather":
        city = "Hyderabad"

        city_match = re.search(
            r"(?:in|for)\s+([a-zA-Z\s]+)$",
            text,
            re.IGNORECASE
        )

        if city_match:
            possible_city = city_match.group(1).strip()

            if possible_city:
                city = possible_city.title()

        result = get_weather(city)

        return {
            **result,
            "intent": "weather"
        }

    if intent == "knowledge":
        return {
            "success": True,
            "intent": "knowledge",
            "message": answer_knowledge(text)
        }

    if intent == "reminder":
        reminder = parse_reminder(text)

        if not reminder:
            return {
                "success": False,
                "intent": "reminder",
                "message": (
                    "Please say something like "
                    "remind me in 1 minute to drink water."
                )
            }

        seconds = reminder["seconds"]
        reminder_message = reminder["message"]

        if seconds < 60:
            display_time = f"{seconds} seconds"

        elif seconds < 3600:
            minutes = seconds // 60
            display_time = f"{minutes} minute"

            if minutes != 1:
                display_time += "s"

        else:
            hours = seconds // 3600
            display_time = f"{hours} hour"

            if hours != 1:
                display_time += "s"

        return {
            "success": True,
            "intent": "reminder",
            "message": (
                f"Reminder set for {display_time}: "
                f"{reminder_message}."
            ),
            "seconds": seconds,
            "reminder_message": reminder_message
        }

    if intent == "email":
        return {
            "success": True,
            "intent": "email",
            "message": (
                "The email form is ready. "
                "Enter the recipient, subject and message."
            ),
            "open_email": True
        }

    if intent == "custom":
        lower_text = text.lower()

        for name, command_data in CUSTOM_COMMANDS.items():

            if name.lower() in lower_text:

                if isinstance(command_data, str):
                    url = command_data

                elif isinstance(command_data, dict):
                    url = command_data.get("url", "")

                else:
                    url = ""

                if url:
                    return {
                        "success": True,
                        "intent": "custom",
                        "message": f"Opening {name}.",
                        "url": url
                    }

        return {
            "success": False,
            "intent": "custom",
            "message": "I couldn't find that custom command."
        }

    if intent == "exit":
        return {
            "success": True,
            "intent": "exit",
            "message": "Goodbye. Have a great day!"
        }

    return {
        "success": False,
        "intent": "unknown",
        "message": (
            "I didn't understand that command. "
            "Please repeat or try another command."
        )
    }


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Voice Assistant",
        "time": datetime.now().isoformat()
    })


@app.route("/api/command", methods=["POST"])
def command_api():
    try:
        data = request.get_json(silent=True) or {}

        result = handle_command(
            data.get("text", "")
        )

        return jsonify(result)

    except Exception as error:
        print(f"Command error: {error}")

        return jsonify({
            "success": False,
            "intent": "error",
            "message": (
                "Something went wrong. "
                "Please try again."
            )
        }), 500


@app.route("/api/email", methods=["POST"])
def email_api():
    try:
        data = request.get_json(silent=True) or {}

        recipient = (
            data.get("recipient", "")
            .strip()
        )

        subject = (
            data.get("subject", "")
            .strip()
        )

        body = (
            data.get("body", "")
            .strip()
        )

        result = send_email(
            recipient,
            subject,
            body
        )

        return jsonify(result), (
            200 if result["success"] else 400
        )

    except Exception as error:
        print(f"Email error: {error}")

        return jsonify({
            "success": False,
            "message": (
                "Unable to process the email request."
            )
        }), 500


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", 5000)
        ),
        debug=True
    )