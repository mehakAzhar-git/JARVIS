import sounddevice as sd
import sounddevice as sd
import wave
import speech_recognition as sr
import webbrowser
import subprocess
from datetime import datetime
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# LOAD OPENROUTER API KEY
# =========================================================

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")

if not api_key:
    print("ERROR: OPENROUTER_API_KEY not found in .env file")
    exit()

print("OPENROUTER API KEY FOUND: True")


# =========================================================
# OPENROUTER CLIENT
# =========================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# =========================================================
# VOICE FUNCTION
# =========================================================

def speak(text):

    text = str(text).strip()

    if not text:
        return

    print("JARVIS:", text)

    try:

        powershell_code = """
Add-Type -AssemblyName System.Speech

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer

$speaker.Volume = 100
$speaker.Rate = 0

$text = [Console]::In.ReadToEnd()

$speaker.Speak($text)

$speaker.Dispose()
"""

        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                powershell_code
            ],
            input=text,
            text=True,
            capture_output=True
        )

    except Exception as e:

        print("VOICE ERROR:", e)


# =========================================================
# AI FUNCTION
# =========================================================

def ask_ai(question):

    try:

        print("JARVIS AI: Thinking...")

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b:free",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Jarvis, a helpful voice assistant. "
                        "Answer in simple English. "
                        "Keep answers short because the answer "
                        "will be spoken aloud. "
                        "Use maximum 3 short sentences. "
                        "Do not use markdown, tables, bullets, "
                        "asterisks, or special formatting."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],

            timeout=30
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Sorry, I did not get an answer."

        answer = answer.strip()

        print("JARVIS AI:", answer)

        return answer


    except Exception as e:

        print("AI ERROR:", e)

        return "Sorry, I could not connect to my AI service."


# =========================================================
# LISTEN FUNCTION
# =========================================================

def listen():

    print("Listening...")

    sample_rate = 44100
    duration = 5

    try:

        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        with wave.open("voice.wav", "wb") as file:

            file.setnchannels(1)
            file.setsampwidth(2)
            file.setframerate(sample_rate)
            file.writeframes(audio.tobytes())


    except Exception as e:

        print("MICROPHONE ERROR:", e)

        return ""


    recognizer = sr.Recognizer()

    try:

        with sr.AudioFile("voice.wav") as source:

            recorded_audio = recognizer.record(source)


        text = recognizer.recognize_google(
            recorded_audio
        )

        print("You:", text)

        return text.lower()


    except sr.UnknownValueError:

        speak("Sorry, I could not understand you.")

        return ""


    except sr.RequestError:

        speak("There is an internet connection problem.")

        return ""


# =========================================================
# START JARVIS
# =========================================================

speak(
    "Hello! I am Jarvis. How can I help you?"
)


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    command = listen()


    # =====================================================
    # IF NOTHING WAS HEARD
    # =====================================================

    if not command:

        continue


    # =====================================================
    # HELLO
    # =====================================================

    if "hello" in command or "hi jarvis" in command:

        speak(
            "Hello! Nice to hear from you."
        )


    # =====================================================
    # TIME
    # =====================================================

    elif "time" in command:

        current_time = datetime.now().strftime(
            "%I:%M %p"
        )

        speak(
            "The time is " + current_time
        )


    # =====================================================
    # DATE
    # =====================================================

    elif "date" in command:

        today = datetime.now().strftime(
            "%d %B %Y"
        )

        speak(
            "Today is " + today
        )


    # =====================================================
    # GOOGLE
    # =====================================================

    elif command == "google" or "open google" in command:

        speak(
            "Opening Google."
        )

        webbrowser.open(
            "https://www.google.com"
        )


    # =====================================================
    # YOUTUBE
    # =====================================================

    elif "youtube" in command:

        search_query = command.replace(
            "youtube",
            ""
        ).replace(
            "search",
            ""
        ).strip()


        if search_query:

            speak(
                "Searching YouTube for "
                + search_query
            )

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(search_query)
            )

            webbrowser.open(url)


        else:

            speak(
                "Opening YouTube."
            )

            webbrowser.open(
                "https://www.youtube.com"
            )


    # =====================================================
    # NOTEPAD
    # =====================================================

    elif "notepad" in command:

        speak(
            "Opening Notepad."
        )

        os.system(
            "notepad.exe"
        )


    # =====================================================
    # CALCULATOR
    # =====================================================

    elif "calculator" in command:

        speak(
            "Opening Calculator."
        )

        os.system(
            "calc.exe"
        )


    # =====================================================
    # GOOGLE SEARCH
    # =====================================================

    elif command.startswith("search"):

        search_query = command.replace(
            "search",
            "",
            1
        ).strip()


        if search_query:

            speak(
                "Searching Google for "
                + search_query
            )

            url = (
                "https://www.google.com/search?q="
                + quote_plus(search_query)
            )

            webbrowser.open(url)


        else:

            speak(
                "What should I search for?"
            )


    # =====================================================
    # JOKE
    # =====================================================

    elif "joke" in command:

        answer = ask_ai(
            "Tell me one short, clean and funny joke."
        )

        speak(answer)


    # =====================================================
    # STOP / EXIT
    # =====================================================

    elif (
        "stop" in command
        or "exit" in command
        or "goodbye" in command
        or "quit" in command
    ):

        speak(
            "Goodbye! Have a nice day."
        )

        break


    # =====================================================
    # AI
    # =====================================================

    else:

        answer = ask_ai(command)

        speak(answer)