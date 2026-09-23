import json
import os
import re
import threading
import time
import webbrowser
from datetime import datetime
from email.message import EmailMessage
import smtplib

import pyttsx3
import requests
import speech_recognition as sr
from dotenv import load_dotenv


load_dotenv()


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MICROPHONE_DEVICE_INDEX = None

WEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    ""
).strip()

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    ""
).strip()

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "2525"
    )
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME",
    ""
).strip()

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD",
    ""
).strip()

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS",
    ""
).strip()


# ---------------------------------------------------------
# Text to Speech
# ---------------------------------------------------------

engine = pyttsx3.init()

engine.setProperty(
    "rate",
    170
)

engine.setProperty(
    "volume",
    1.0
)


def speak(text):
    print(f"Assistant: {text}")

    engine.say(text)
    engine.runAndWait()


# ---------------------------------------------------------
# Speech Recognition
# ---------------------------------------------------------

recognizer = sr.Recognizer()


def listen():
    with sr.Microphone(
        device_index=MICROPHONE_DEVICE_INDEX
    ) as source:

        print("\nListening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.8
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=12
            )

        except sr.WaitTimeoutError:

            speak(
                "I didn't hear anything. Please try again."
            )

            return ""


    try:

        text = recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        print(f"You: {text}")

        return text.lower().strip()


    except sr.UnknownValueError:

        speak(
            "I didn't understand. Please repeat."
        )

        return ""


    except sr.RequestError:

        speak(
            "Speech recognition service is unavailable right now."
        )

        return ""


# ---------------------------------------------------------
# Date / Time
# ---------------------------------------------------------

def handle_greeting():

    hour = datetime.now().hour

    if 5 <= hour < 12:
        greeting = "Good morning"

    elif 12 <= hour < 17:
        greeting = "Good afternoon"

    else:
        greeting = "Good evening"

    speak(
        f"{greeting}! Hello! How can I help you?"
    )


def handle_time():

    current_time = datetime.now().strftime(
        "%I:%M %p"
    ).lstrip("0")

    speak(
        f"The current time is {current_time}."
    )


def handle_date():

    current_date = datetime.now().strftime(
        "%A, %B %d, %Y"
    )

    speak(
        f"Today is {current_date}."
    )


# ---------------------------------------------------------
# Web Search
# ---------------------------------------------------------

def handle_search(command):

    prefixes = [
        "search for ",
        "search ",
        "look up ",
        "lookup ",
        "google ",
    ]

    query = command

    for prefix in prefixes:

        if query.startswith(prefix):
            query = query[len(prefix):].strip()
            break


    if not query:

        speak(
            "What would you like me to search for?"
        )

        return


    speak(
        f"Searching the web for {query}."
    )


    url = (
        "https://www.google.com/search?q="
        + requests.utils.quote(query)
    )

    webbrowser.open(url)


# ---------------------------------------------------------
# Weather
# ---------------------------------------------------------

def handle_weather(city="Hyderabad"):

    if not WEATHER_API_KEY:

        speak(
            "Weather service is not configured."
        )

        return


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

            speak(
                "I couldn't get the weather right now."
            )

            return


        data = response.json()


        description = data[
            "weather"
        ][0][
            "description"
        ]

        temperature = round(
            data["main"]["temp"]
        )

        humidity = data[
            "main"
        ][
            "humidity"
        ]


        speak(
            f"The weather in {city} is "
            f"{description}. "
            f"The temperature is "
            f"{temperature} degrees Celsius. "
            f"Humidity is {humidity} percent."
        )


    except requests.RequestException:

        speak(
            "I couldn't connect to the weather service."
        )


# ---------------------------------------------------------
# Knowledge
# ---------------------------------------------------------

KNOWLEDGE_BASE = {

    "python":
        "Python is a high-level general-purpose "
        "programming language.",

    "machine learning":
        "Machine learning is a branch of artificial "
        "intelligence where computers learn patterns "
        "from data.",

    "artificial intelligence":
        "Artificial intelligence is the field of "
        "building systems that can perform tasks "
        "requiring human-like intelligence.",

    "data science":
        "Data science uses programming, statistics "
        "and domain knowledge to analyze data.",

    "flask":
        "Flask is a lightweight Python web framework.",

    "github":
        "GitHub is a platform for hosting and "
        "collaborating on software projects."
}


def handle_knowledge(command):

    for topic, answer in KNOWLEDGE_BASE.items():

        if topic in command:

            speak(answer)

            return


    speak(
        "I don't have that topic in my local knowledge base. "
        "You can use web search to learn more."
    )


# ---------------------------------------------------------
# Reminder
# ---------------------------------------------------------

def parse_reminder(command):

    match = re.search(
        r"in\s+(\d+)\s*"
        r"(seconds?|secs?|minutes?|mins?|hours?|hrs?)"
        r"(?:\s+(?:to|for)\s+(.+))?",
        command,
        re.IGNORECASE
    )


    if not match:
        return None


    amount = int(
        match.group(1)
    )

    unit = match.group(2).lower()

    reminder_message = (
        match.group(3)
        or "your reminder"
    )


    if unit.startswith("second"):

        seconds = amount

    elif unit.startswith("minute"):

        seconds = amount * 60

    else:

        seconds = amount * 3600


    return (
        seconds,
        reminder_message.strip()
    )


def reminder_worker(seconds, message):

    time.sleep(seconds)

    speak(
        f"Reminder: {message}"
    )


def handle_reminder(command):

    result = parse_reminder(command)


    if not result:

        speak(
            "Please say something like "
            "remind me in 1 minute to drink water."
        )

        return


    seconds, message = result


    threading.Thread(
        target=reminder_worker,
        args=(seconds, message),
        daemon=True
    ).start()


    speak(
        f"Reminder set for {message}."
    )


# ---------------------------------------------------------
# Email
# ---------------------------------------------------------

def send_email():

    recipient = input(
        "Recipient email: "
    ).strip()

    subject = input(
        "Subject: "
    ).strip()

    body = input(
        "Message: "
    ).strip()


    if not all([
        SMTP_HOST,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        EMAIL_ADDRESS
    ]):

        speak(
            "Email service is not configured."
        )

        return


    try:

        email = EmailMessage()

        email["From"] = EMAIL_ADDRESS

        email["To"] = recipient

        email["Subject"] = (
            subject or
            "Voice Assistant Email"
        )

        email.set_content(
            body or
            "Sent from my Voice Assistant."
        )


        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(
                email
            )


        speak(
            "The email has been sent successfully."
        )


    except Exception:

        speak(
            "I couldn't send the email."
        )


# ---------------------------------------------------------
# Custom commands
# ---------------------------------------------------------

def load_custom_commands():

    try:

        with open(
            "commands.json",
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


custom_commands = load_custom_commands()


def handle_custom_command(command):

    lower_command = command.lower()


    for name, data in custom_commands.items():

        if name.lower() in lower_command:

            if isinstance(data, str):

                url = data

            elif isinstance(data, dict):

                url = data.get(
                    "url",
                    ""
                )

            else:

                url = ""


            if url:

                speak(
                    f"Opening {name}."
                )

                webbrowser.open(url)

                return


    speak(
        "I couldn't find that custom command."
    )


# ---------------------------------------------------------
# Main command router
# ---------------------------------------------------------

def process_command(command):

    if not command:
        return True


    # Greeting

    if any(
        word in command
        for word in [
            "hello",
            "hi",
            "hey",
            "hai",
            "good morning",
            "good afternoon",
            "good evening"
        ]
    ):

        handle_greeting()
        return True


    # Time

    if (
        "what time" in command
        or "current time" in command
        or "tell me the time" in command
        or command == "time"
    ):

        handle_time()
        return True


    # Date

    if (
        "today's date" in command
        or "todays date" in command
        or "current date" in command
        or "what is the date" in command
        or command == "date"
    ):

        handle_date()
        return True


    # Weather

    if (
        "weather" in command
        or "temperature" in command
        or "forecast" in command
    ):

        handle_weather()
        return True


    # Search

    if (
        command.startswith("search")
        or command.startswith("look up")
        or command.startswith("lookup")
        or command.startswith("google")
    ):

        handle_search(command)
        return True


    # Reminder

    if (
        "remind me" in command
        or "set a reminder" in command
        or command.startswith("reminder")
    ):

        handle_reminder(command)
        return True


    # Email

    if (
        "send email" in command
        or "send an email" in command
        or command == "email"
    ):

        send_email()
        return True


    # Knowledge

    if any(
        command.startswith(prefix)
        for prefix in [
            "what is",
            "who is",
            "define",
            "tell me about",
            "explain"
        ]
    ):

        handle_knowledge(command)
        return True


    # Custom command

    for name in custom_commands:

        if name.lower() in command:

            handle_custom_command(command)

            return True


    # Exit

    if any(
        word in command
        for word in [
            "exit",
            "quit",
            "goodbye",
            "bye",
            "close assistant"
        ]
    ):

        speak(
            "Goodbye. Have a great day!"
        )

        return False


    speak(
        "I didn't understand that. "
        "Please repeat or try another command."
    )

    return True


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

def main():

    speak(
        "Voice assistant is ready."
    )


    speak(
        "You can ask for the time, date, weather, "
        "web search, reminders, knowledge, or email."
    )


    while True:

        command = listen()

        if not process_command(command):
            break


if __name__ == "__main__":
    main()