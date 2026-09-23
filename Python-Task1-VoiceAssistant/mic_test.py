import speech_recognition as sr

recognizer = sr.Recognizer()

print("Speak for 5 seconds...")

with sr.Microphone(device_index=1) as source:
    audio = recognizer.record(source, duration=5)

print("Recording successful.")

try:
    text = recognizer.recognize_google(audio)
    print("You said:", text)
except sr.UnknownValueError:
    print("Speech was recorded, but I could not understand it.")
except sr.RequestError as error:
    print("Speech recognition service error:", error)