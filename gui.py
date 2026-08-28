import customtkinter as ctk
import speech_recognition as sr
import sounddevice as sd
import scipy.io.wavfile as wav

import webbrowser
import re
import subprocess
from datetime import datetime
from urllib.parse import quote_plus
import os
import threading
import tempfile
import math
import time

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# JARVIS THEME
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#050912"
PANEL = "#0A1220"
PANEL2 = "#0D1828"
CYAN = "#00D9FF"
CYAN2 = "#00A8CC"
WHITE = "#EAF9FF"
GRAY = "#78909C"
GREEN = "#00FF9C"
RED = "#FF4057"


# =========================================================
# API
# =========================================================

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")

if api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
else:
    client = None


# =========================================================
# SPEAK
# =========================================================

def speak(text):

    text = str(text).strip()

    if not text:
        return

    print("JARVIS:", text)

    try:

        powershell_code = r'''
Add-Type -AssemblyName System.Speech

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer

$speaker.Volume = 100
$speaker.Rate = 0

$text = [Console]::In.ReadToEnd()

$speaker.Speak($text)

$speaker.Dispose()
'''

        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                powershell_code
            ],
            input=text,
            text=True,
            timeout=60
        )

    except Exception as e:
        print("VOICE ERROR:", e)


# =========================================================
# AI
# =========================================================
def clean_answer(text):

    if not text:
        return "Sorry, I could not find an answer."

    text = str(text)

    # Remove [text](link)
    text = re.sub(
        r'\[([^\]]+)\]\([^)]+\)',
        r'\1',
        text
    )

    # Remove URLs
    text = re.sub(
        r'https?://\S+',
        '',
        text
    )

    # Remove markdown
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    
    # Remove table lines
    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("|"):
            continue

        if "---|" in line or "|---" in line:
            continue

        lines.append(line)

    text = " ".join(lines)

    # Remove extra spaces
    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    return text.strip()

def ask_ai(question):

    try:
        set_status("SEARCHING WEB", CYAN)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:online",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JARVIS, a helpful AI assistant. "
                        "Use web search for current information. "
                        "Answer briefly in simple English."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            timeout=60
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Sorry, I could not find an answer."

        return clean_answer(answer)

    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return "OpenRouter error. Please check the terminal."

   #======================================
# MICROPHONE
# =========================================================

def listen():

    filename = None

    try:

        set_status("LISTENING", CYAN)

        samplerate = 16000
        duration = 6

        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        set_status("PROCESSING", CYAN)

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as f:

            filename = f.name

        wav.write(
            filename,
            samplerate,
            recording
        )

        recognizer = sr.Recognizer()

        with sr.AudioFile(filename) as source:

            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        return text.lower().strip()

    except sr.UnknownValueError:

        return ""

    except sr.RequestError:

        return ""

    except Exception as e:

        print("MICROPHONE ERROR:", e)

        return ""

    finally:

        if filename:

            try:
                os.remove(filename)
            except:
                pass


# =========================================================
# STATUS
# =========================================================

def set_status(text, color=GREEN):

    try:

        app.after(
            0,
            lambda: status_label.configure(
                text=f"● {text}",
                text_color=color
            )
        )

    except:
        pass


# =========================================================
# CHAT
# =========================================================

def add_message(sender, message):

    def update():

        chat_box.configure(
            state="normal"
        )

        if sender == "You":

            chat_box.insert(
                "end",
                f"\nYOU  ›  {message}\n",
                "user"
            )

        else:

            chat_box.insert(
                "end",
                f"\nJARVIS  ›  {message}\n",
                "jarvis"
            )

        chat_box.configure(
            state="disabled"
        )

        chat_box.see("end")

    app.after(
        0,
        update
    )


# =========================================================
# COMMAND PROCESSOR
# =========================================================

def process_command(command):

    if not command:
        set_status("ONLINE", GREEN)
        return

    add_message(
        "You",
        command
    )


    # HELLO
    if "hello" in command:

        answer = "Hello. I am Jarvis. How can I help you?"

        add_message("JARVIS", answer)

        speak(answer)


    # TIME
    elif "time" in command:

        current_time = datetime.now().strftime("%I:%M %p")

        answer = f"The time is {current_time}."

        add_message("JARVIS", answer)

        speak(answer)


    # DATE
    elif "date" in command:

        today = datetime.now().strftime("%d %B %Y")

        answer = f"Today is {today}."

        add_message("JARVIS", answer)

        speak(answer)


    # CHROME
    elif "open chrome" in command:

        answer = "Opening Chrome."

        add_message("JARVIS", answer)

        speak(answer)

        subprocess.Popen(
            ["cmd", "/c", "start", "", "chrome"]
        )


    # VS CODE
    elif (
        "open vs code" in command
        or "open visual studio code" in command
    ):

        answer = "Opening Visual Studio Code."

        add_message("JARVIS", answer)

        speak(answer)

        subprocess.Popen(
            ["cmd", "/c", "start", "", "code"]
        )


    # VISUAL STUDIO
    elif "open visual studio" in command:

        answer = "Opening Visual Studio."

        add_message("JARVIS", answer)

        speak(answer)

        subprocess.Popen(
            ["cmd", "/c", "start", "", "devenv"]
        )


    # NOTEPAD
    elif "open notepad" in command:

        answer = "Opening Notepad."

        add_message("JARVIS", answer)

        speak(answer)

        os.system("notepad.exe")


    # CALCULATOR
    elif "open calculator" in command:

        answer = "Opening Calculator."

        add_message("JARVIS", answer)

        speak(answer)

        os.system("calc.exe")


    # GOOGLE
    elif "open google" in command:

        answer = "Opening Google."

        add_message("JARVIS", answer)

        speak(answer)

        webbrowser.open(
            "https://www.google.com"
        )


    # YOUTUBE
    elif "youtube" in command:

        query = command.replace(
            "youtube",
            ""
        ).strip()

        if query:

            answer = f"Searching YouTube for {query}."

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

        else:

            answer = "Opening YouTube."

            url = "https://www.youtube.com"

        add_message("JARVIS", answer)

        speak(answer)

        webbrowser.open(url)

        # =====================================================
    # FILE EXPLORER
    # =====================================================

    elif (
        "open file explorer" in command
        or "open explorer" in command
        or "open files" in command
    ):

        answer = "Opening File Explorer."

        add_message("JARVIS", answer)
        speak(answer)

        subprocess.Popen("explorer.exe")


    # =====================================================
    # DOWNLOADS
    # =====================================================

    elif (
        "open downloads" in command
        or "show downloads" in command
    ):

        answer = "Opening Downloads."

        add_message("JARVIS", answer)
        speak(answer)

        downloads = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )

        subprocess.Popen(
            ["explorer.exe", downloads]
        )


    # =====================================================
    # SETTINGS
    # =====================================================

    elif (
        "open settings" in command
        or "system settings" in command
    ):

        answer = "Opening Windows Settings."

        add_message("JARVIS", answer)
        speak(answer)

        subprocess.Popen(
            ["cmd", "/c", "start", "ms-settings:"]
        )


    # =====================================================
    # TASK MANAGER
    # =====================================================

    elif (
        "open task manager" in command
        or "task manager" in command
    ):

        answer = "Opening Task Manager."

        add_message("JARVIS", answer)
        speak(answer)

        subprocess.Popen(
            ["taskmgr.exe"]
        )


    # =====================================================
    # CONTROL PANEL
    # =====================================================

    elif (
        "open control panel" in command
        or "control panel" in command
    ):

        answer = "Opening Control Panel."

        add_message("JARVIS", answer)
        speak(answer)

        subprocess.Popen(
            ["control.exe"]
        )
    # SCREENSHOT
    elif "screenshot" in command:

        try:

            import pyautogui

            filename = (
                "screenshot_"
                + datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                + ".png"
            )

            pyautogui.screenshot(filename)

            answer = "Screenshot captured successfully."

            add_message("JARVIS", answer)

            speak(answer)

        except:

            answer = "I could not take the screenshot."

            add_message("JARVIS", answer)

            speak(answer)


   
    # =====================================================
    # ADVANCED WEB SEARCH
    # =====================================================

    elif (
        "search web" in command
        or "search the web" in command
        or "search for" in command
        or "latest" in command
        or "news" in command
        or "current" in command
        or "recent" in command
        or "today" in command
    ):

        set_status("SEARCHING WEB", CYAN)

        add_message(
            "JARVIS",
            "Searching the web..."
        )

        answer = ask_ai(command)

        add_message(
            "JARVIS",
            answer
        )

        speak(answer)

        set_status(
            "ONLINE",
            GREEN
        )


    # JOKE
    elif "joke" in command:

        set_status("THINKING", CYAN)

        answer = ask_ai(
            "Tell me one short clean funny joke."
        )

        add_message(
            "JARVIS",
            answer
        )

        speak(answer)


    # WHO
    elif (
        "who are you" in command
        or "what are you" in command
    ):

        answer = "I am Jarvis, your personal AI voice assistant."

        add_message(
            "JARVIS",
            answer
        )

        speak(answer)


    # EXIT
    elif (
        "exit" in command
        or "goodbye" in command
        or command == "quit"
    ):

        answer = "Goodbye. See you later."

        add_message(
            "JARVIS",
            answer
        )

        speak(answer)

        app.after(
            1000,
            app.destroy
        )

        return


    # GENERAL AI
    else:

        set_status("THINKING", CYAN)

        answer = ask_ai(command)

        add_message(
            "JARVIS",
            answer
        )

        speak(answer)

    set_status("ONLINE", GREEN)


# =========================================================
# LISTEN BUTTON
# =========================================================

def listen_button_clicked():

    listen_button.configure(
        state="disabled",
        text="◉ LISTENING..."
    )

    def run():

        command = listen()

        if command:

            process_command(command)

        else:

            add_message(
                "JARVIS",
                "I could not understand that."
            )

            set_status("ONLINE", GREEN)

        app.after(
            0,
            lambda: listen_button.configure(
                state="normal",
                text="◉ LISTEN"
            )
        )

    threading.Thread(
        target=run,
        daemon=True
    ).start()


# =========================================================
# SEND TEXT
# =========================================================

def send_command():

    command = entry.get().strip().lower()

    if not command:
        return

    entry.delete(
        0,
        "end"
    )

    threading.Thread(
        target=process_command,
        args=(command,),
        daemon=True
    ).start()


# =========================================================
# ENTER
# =========================================================

def enter_pressed(event):

    send_command()


# =========================================================
# ANIMATED CORE
# =========================================================

def animate_core():

    global animation_angle

    animation_angle += 4

    try:

        core_canvas.delete(
            "all"
        )

        cx = 190
        cy = 190

        # Outer rings
        for i in range(4):

            radius = 145 - i * 25

            offset = math.sin(
                math.radians(
                    animation_angle + i * 40
                )
            ) * 5

            core_canvas.create_oval(
                cx - radius - offset,
                cy - radius - offset,
                cx + radius + offset,
                cy + radius + offset,
                outline=CYAN,
                width=2
            )

        # Center glow layers
        for radius in range(70, 20, -10):

            core_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline=CYAN2,
                width=2
            )

        # Core
        core_canvas.create_oval(
            cx - 25,
            cy - 25,
            cx + 25,
            cy + 25,
            fill=CYAN,
            outline=WHITE,
            width=2
        )

        core_canvas.create_text(
            cx,
            cy,
            text="J",
            fill=BG,
            font=("Arial", 25, "bold")
        )

        core_canvas.create_text(
            cx,
            355,
            text="J A R V I S",
            fill=CYAN,
            font=("Arial", 20, "bold")
        )

        app.after(
            40,
            animate_core
        )

    except:
        pass


# =========================================================
# CLOCK
# =========================================================

def update_clock():

    now = datetime.now().strftime(
        "%I:%M:%S %p"
    )

    clock_label.configure(
        text=now
    )

    app.after(
        1000,
        update_clock
    )


# =========================================================
# SYSTEM INFO
# =========================================================

def update_system():

    try:

        import psutil

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        system_label.configure(
            text=f"CPU {cpu:.0f}%     RAM {ram:.0f}%"
        )

    except:

        system_label.configure(
            text="SYSTEM MONITOR ONLINE"
        )

    app.after(
        2000,
        update_system
    )


# =========================================================
# MAIN WINDOW
# =========================================================

app = ctk.CTk()

app.title(
    "JARVIS — AI Voice Assistant"
)

app.geometry(
    "1250x800"
)

app.minsize(
    1050,
    700
)

app.configure(
    fg_color=BG
)


# =========================================================
# TOP BAR
# =========================================================

top = ctk.CTkFrame(
    app,
    fg_color=BG
)

top.pack(
    fill="x",
    padx=30,
    pady=(20, 5)
)


brand = ctk.CTkLabel(
    top,
    text="J A R V I S",
    text_color=CYAN,
    font=("Arial", 28, "bold")
)

brand.pack(
    side="left"
)


version = ctk.CTkLabel(
    top,
    text="  AI VOICE SYSTEM  •  v1.0",
    text_color=GRAY,
    font=("Arial", 12)
)

version.pack(
    side="left",
    pady=10
)


clock_label = ctk.CTkLabel(
    top,
    text="00:00:00",
    text_color=WHITE,
    font=("Consolas", 17, "bold")
)

clock_label.pack(
    side="right"
)


# =========================================================
# MAIN AREA
# =========================================================

main = ctk.CTkFrame(
    app,
    fg_color=BG
)

main.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=10
)


# =========================================================
# LEFT CORE PANEL
# =========================================================

left = ctk.CTkFrame(
    main,
    fg_color=PANEL,
    corner_radius=20,
    width=470
)

left.pack(
    side="left",
    fill="both",
    padx=(0, 10)
)

left.pack_propagate(False)


core_title = ctk.CTkLabel(
    left,
    text="NEURAL CORE",
    text_color=GRAY,
    font=("Arial", 13, "bold")
)

core_title.pack(
    pady=(20, 0)
)


core_canvas = ctk.CTkCanvas(
    left,
    width=380,
    height=400,
    bg=PANEL,
    highlightthickness=0
)

core_canvas.pack(
    pady=10
)


status_label = ctk.CTkLabel(
    left,
    text="● ONLINE",
    text_color=GREEN,
    font=("Arial", 16, "bold")
)

status_label.pack(
    pady=5
)


system_label = ctk.CTkLabel(
    left,
    text="SYSTEM MONITOR ONLINE",
    text_color=GRAY,
    font=("Consolas", 12)
)

system_label.pack(
    pady=5
)


# =========================================================
# RIGHT CHAT PANEL
# =========================================================

right = ctk.CTkFrame(
    main,
    fg_color=PANEL,
    corner_radius=20
)

right.pack(
    side="right",
    fill="both",
    expand=True
)


chat_title = ctk.CTkLabel(
    right,
    text="CONVERSATION",
    text_color=CYAN,
    font=("Arial", 16, "bold")
)

chat_title.pack(
    anchor="w",
    padx=20,
    pady=(20, 10)
)


chat_box = ctk.CTkTextbox(
    right,
    fg_color=PANEL2,
    text_color=WHITE,
    corner_radius=15,
    font=("Consolas", 14),
    wrap="word"
)

chat_box.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=(0, 15)
)

chat_box.tag_config(
    "user",
    foreground=CYAN
)

chat_box.tag_config(
    "jarvis",
    foreground=GREEN
)

chat_box.configure(
    state="disabled"
)


# =========================================================
# INPUT
# =========================================================

input_frame = ctk.CTkFrame(
    right,
    fg_color="transparent"
)

input_frame.pack(
    fill="x",
    padx=20,
    pady=(0, 10)
)


entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="Ask JARVIS anything...",
    height=48,
    fg_color=PANEL2,
    border_color=CYAN2,
    font=("Arial", 14)
)

entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 10)
)

entry.bind(
    "<Return>",
    enter_pressed
)


send_button = ctk.CTkButton(
    input_frame,
    text="SEND",
    width=90,
    height=48,
    fg_color=CYAN2,
    hover_color=CYAN,
    text_color=BG,
    font=("Arial", 13, "bold"),
    command=send_command
)

send_button.pack(
    side="right"
)


# =========================================================
# CONTROL BUTTONS
# =========================================================

controls = ctk.CTkFrame(
    right,
    fg_color="transparent"
)

controls.pack(
    fill="x",
    padx=20,
    pady=(0, 20)
)


listen_button = ctk.CTkButton(
    controls,
    text="◉ LISTEN",
    height=48,
    fg_color=CYAN2,
    hover_color=CYAN,
    text_color=BG,
    font=("Arial", 14, "bold"),
    command=listen_button_clicked
)

listen_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 5)
)


google_button = ctk.CTkButton(
    controls,
    text="GOOGLE",
    height=48,
    fg_color=PANEL2,
    border_width=1,
    border_color=CYAN2,
    command=lambda: webbrowser.open(
        "https://www.google.com"
    )
)

google_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=5
)


youtube_button = ctk.CTkButton(
    controls,
    text="YOUTUBE",
    height=48,
    fg_color=PANEL2,
    border_width=1,
    border_color=CYAN2,
    command=lambda: webbrowser.open(
        "https://www.youtube.com"
    )
)

youtube_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=5
)


exit_button = ctk.CTkButton(
    controls,
    text="EXIT",
    height=48,
    fg_color="#40121A",
    hover_color=RED,
    command=app.destroy
)

exit_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(5, 0)
)


# =========================================================
# WELCOME
# =========================================================

add_message(
    "JARVIS",
    "System initialized. All primary systems are online."
)


# =========================================================
# START ANIMATIONS
# =========================================================

animation_angle = 0

animate_core()
update_clock()
update_system()


# =========================================================
# START
# =========================================================

app.mainloop()