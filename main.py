import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import tkintermapview
import pyttsx3
import speech_recognition as sr
import threading
import requests
from urllib.parse import quote_plus
import webbrowser
import re
import xml.etree.ElementTree as ET
from tkcalendar import Calendar

from config import API_KEY



# =========================================================
# TEXT TO SPEECH
# =========================================================

engine = pyttsx3.init()
engine.setProperty("rate", 160)
engine.setProperty("volume", 1.0)


def speak(text):
    def speak_thread():
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("Speech error:", e)

    threading.Thread(
        target=speak_thread,
        daemon=True
    ).start()


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()
root.title("Smart Weather Assistant")
root.geometry("1400x850")
root.configure(bg="white")
root.state("zoomed")


# =========================================================
# TOP FRAME
# =========================================================

top_frame = tk.Frame(
    root,
    bg="#2196F3",
    height=100
)
top_frame.pack(fill="x")


# ---------------- Logo ----------------

try:
    logo_image = Image.open("image/logo.png")
    logo_image = logo_image.resize((60, 60))
    logo = ImageTk.PhotoImage(logo_image)

    logo_label = tk.Label(
        top_frame,
        image=logo,
        bg="#2196F3"
    )
    logo_label.image = logo
    logo_label.pack(side="left", padx=15, pady=10)

except Exception as e:
    print("Could not load logo:", e)


# ---------------- Title ----------------

title = tk.Label(
    top_frame,
    text="Smart Weather Assistant",
    font=("Arial", 24, "bold"),
    fg="white",
    bg="#2196F3"
)
title.pack(side="left", padx=20, pady=20)


# ---------------- Date and Time ----------------

time_label = tk.Label(
    top_frame,
    text="Date: --\nTime: --",
    font=("Arial", 14),
    fg="white",
    bg="#2196F3"
)
time_label.pack(side="right", padx=20, pady=20)


def update_time():
    current_time = datetime.now()

    date = current_time.strftime("%A, %B %d, %Y")
    time = current_time.strftime("%I:%M:%S %p")

    time_label.config(
        text=f"Date: {date}\nTime: {time}"
    )

    root.after(1000, update_time)


# =========================================================
# LEFT FRAME
# =========================================================

left_frame = tk.Frame(
    root,
    bg="white",
    width=350
)

left_frame.pack(
    side="left",
    fill="y"
)

left_frame.pack_propagate(False)


# =========================================================
# SEARCH
# =========================================================

search_label = tk.Label(
    left_frame,
    text="Search Location:",
    font=("Arial", 14),
    width=25,
    bg="#eeeeee"
)

search_label.pack(pady=10)


city_entry = tk.Entry(
    left_frame,
    font=("Arial", 14),
    width=25
)

city_entry.pack(pady=5)

city_entry.bind(
    "<Return>",
    lambda event: search_weather()
)


# =========================================================
# WEATHER FUNCTION
# =========================================================

def search_weather():
    city = city_entry.get().strip()

    if not city:
        status_label.config(text="Please enter a city.")
        return

    # Prevent another search while one is running
    if search_button["state"] == "disabled":
        return

    search_button.config(state="disabled")
    voice_button.config(state="disabled")

    status_label.config(
        text=f"Searching for {city}..."
    )

    # Run weather API request in background
    threading.Thread(
        target=get_weather,
        args=(city,),
        daemon=True
    ).start()

    # Start weather news
    get_weather_news(city)


def get_weather(city):

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=5
        )

        data = response.json()

        if response.status_code != 200:

            message = data.get(
                "message",
                "Location not found."
            )

            root.after(
                0,
                search_failed,
                message
            )

            return

        # Get weather information
        temperature_value = data["main"]["temp"]
        humidity_value = data["main"]["humidity"]
        wind_value = data["wind"]["speed"]

        weather_description = data["weather"][0]["description"]
        weather_main = data["weather"][0]["main"]

        latitude = data["coord"]["lat"]
        longitude = data["coord"]["lon"]

        country = data["sys"]["country"]

        # Send results back to Tkinter thread
        root.after(
            0,
            update_weather_display,
            city,
            country,
            temperature_value,
            humidity_value,
            wind_value,
            weather_description,
            weather_main,
            latitude,
            longitude
        )

    except requests.exceptions.Timeout:

        root.after(
            0,
            search_failed,
            "The weather service took too long to respond."
        )

    except requests.exceptions.ConnectionError:

        root.after(
            0,
            search_failed,
            "No internet connection."
        )

    except Exception as e:

        print("Weather error:", e)

        root.after(
            0,
            search_failed,
            "Something went wrong."
        )



def update_weather_display(
    city,
    country,
    temperature_value,
    humidity_value,
    wind_value,
    weather_description,
    weather_main,
    latitude,
    longitude
):

    # Update location
    location_label.config(
        text=f"{city.title()}, {country}"
    )

    # Update temperature
    temperature_label.config(
        text=f"Temperature: {temperature_value:.1f} °C"
    )

    # Update humidity
    humidity_label.config(
        text=f"Humidity: {humidity_value}%"
    )

    # Update wind
    wind_label.config(
        text=f"Wind Speed: {wind_value:.1f} m/s"
    )

    # Update description
    description_label.config(
        text=weather_description.title()
    )

    # Move map
    map_widget.set_position(
        latitude,
        longitude
    )

    map_widget.set_zoom(10)

    # Change weather icon
    update_weather_icon(weather_main)

    # Status
    status_label.config(
        text="Weather updated successfully!"
    )

    # Enable buttons again
    search_button.config(
        state="normal"
    )

    voice_button.config(
        state="normal"
    )

    # Speak result
    message = (
        f"The current weather in {city} is "
        f"{weather_description}. "
        f"The temperature is "
        f"{temperature_value:.1f} degrees Celsius."
    )

    speak(message)


def search_failed(message):

    status_label.config(
        text=message
    )

    search_button.config(
        state="normal"
    )

    voice_button.config(
        state="normal"
    )

    print(message)


# =========================================================
# SEARCH BUTTON
# =========================================================

search_button = tk.Button(
    left_frame,
    text="Search",
    font=("Arial", 12),
    width=25,
    bg="#2196F3",
    fg="white",
    command=search_weather
)

search_button.pack(pady=10)
# =========================================================
# VOICE SEARCH
# =========================================================

recognizer = sr.Recognizer()

# Make voice recognition faster
recognizer.pause_threshold = 0.6
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.3


def voice_search():

    # Prevent multiple voice searches
    if voice_button["state"] == "disabled":
        return

    voice_button.config(state="disabled")
    search_button.config(state="disabled")

    status_label.config(
        text="🎤 Listening..."
    )

    # Run microphone in background
    threading.Thread(
        target=listen_for_city,
        daemon=True
    ).start()


def listen_for_city():

    try:

        with sr.Microphone() as source:

            print("Listening...")

            # Quickly adjust to background noise
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            # Listen for the user
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=4
            )

        # Tell user we are processing the voice
        root.after(
            0,
            lambda: status_label.config(
                text="🔎 Recognizing..."
            )
        )

        # Convert speech to text
        city = recognizer.recognize_google(audio)

        print("You said:", city)

        # Put the city into the search box
        root.after(
            0,
            set_voice_city,
            city
        )

    except sr.WaitTimeoutError:

        root.after(
            0,
            voice_error,
            "No speech detected. Please try again."
        )

    except sr.UnknownValueError:

        root.after(
            0,
            voice_error,
            "Sorry, I could not understand you."
        )

    except sr.RequestError:

        root.after(
            0,
            voice_error,
            "Speech recognition service is unavailable."
        )

    except Exception as e:

        # Show the REAL error in the terminal
        print("VOICE ERROR:", repr(e))

        root.after(
            0,
            voice_error,
            f"Voice error: {e}"
        )


def set_voice_city(city):

    # Put recognized city in search box
    city_entry.delete(
        0,
        tk.END
    )

    city_entry.insert(
        0,
        city
    )

    # Automatically search weather
    search_weather()


def voice_error(message):

    status_label.config(
        text=message
    )

    voice_button.config(
        state="normal"
    )

    search_button.config(
        state="normal"
    )

    print(message)




# =========================================================
# VOICE BUTTON
# =========================================================

voice_button = tk.Button(
    left_frame,
    text="Voice Assistant",
    font=("Arial", 12),
    width=25,
    bg="#2196F3",
    fg="white",
    command=voice_search
)

voice_button.pack(pady=10)

status_label = tk.Label(
    left_frame,
    text="Ready",
    font=("Arial", 11),
    fg="#555555",
    bg="white"
)

status_label.pack(
    pady=5
)


# =========================================================
# MAP
# =========================================================

map_widget = tkintermapview.TkinterMapView(
    left_frame,
    width=350,
    height=400,
    corner_radius=0
)

# Default location: Accra, Ghana
map_widget.set_position(
    5.6037,
    -0.1870
)

map_widget.set_zoom(10)

map_widget.pack(pady=20)


# =========================================================
# CENTER FRAME
# =========================================================

center_frame = tk.Frame(
    root,
    bg= "#0B1628"
)

center_frame.pack(
    side="left",
    fill="both",
    expand=True
)


# =========================================================
# WEATHER TITLE
# =========================================================

weather_title = tk.Label(
    center_frame,
    text="Today's Weather Information",
    font=("Arial", 22, "bold"),
    bg="#F5F5F5"
)

weather_title.pack(pady=10)


# =========================================================
# LOCATION
# =========================================================

location_label = tk.Label(
    center_frame,
    text="Search for a city",
    font=("Arial", 18, "bold"),
    bg="#F5F5F5"
)

location_label.pack(pady=5)


# =========================================================
# WEATHER DESCRIPTION
# =========================================================

description_label = tk.Label(
    center_frame,
    text="Weather: --",
    font=("Arial", 16),
    bg="#F5F5F5"
)

description_label.pack(pady=5)


# =========================================================
# TEMPERATURE
# =========================================================

temperature_label = tk.Label(
    center_frame,
    text="Temperature: -- °C",
    font=("Arial", 16),
    bg="#F5F5F5"
)

temperature_label.pack(pady=5)


# =========================================================
# HUMIDITY
# =========================================================

humidity_label = tk.Label(
    center_frame,
    text="Humidity: -- %",
    font=("Arial", 16),
    bg="#F5F5F5"
)

humidity_label.pack(pady=5)


# =========================================================
# WIND
# =========================================================

wind_label = tk.Label(
    center_frame,
    text="Wind Speed: -- m/s",
    font=("Arial", 16),
    bg="#F5F5F5"
)

wind_label.pack(pady=5)


# =========================================================
# WEATHER ICON
# =========================================================

def update_weather_icon(weather):

    try:

        if weather == "Clear":
            filename = "image/sun.png"

        elif weather == "Clouds":
            filename = "image/cloud.png"

        elif weather in ["Rain", "Drizzle"]:
            filename = "image/rain.png"

        elif weather in ["Thunderstorm"]:
            filename = "image/storm.png"

        else:
            filename = "image/cloud.png"

        image = Image.open(filename)

        image = image.resize(
            (100, 100)
        )

        image = ImageTk.PhotoImage(image)

        icon_label.config(
            image=image
        )

        icon_label.image = image

    except Exception as e:

        print("Could not load weather icon:", e)


weather_icon = Image.open(
    "image/sun.png"
)

weather_icon = weather_icon.resize(
    (100, 100)
)

weather_icon = ImageTk.PhotoImage(
    weather_icon
)


icon_label = tk.Label(
    center_frame,
    image=weather_icon,
    bg="#F5F5F5"
)

icon_label.image = weather_icon

icon_label.pack(pady=10)


# =========================================================
# WEATHER NEWS
# =========================================================

news_title = tk.Label(
    center_frame,
    text="📰 Weather News",
    font=("Arial", 24, "bold"),
    fg="white",
    bg="#0B1628"
)

news_title.pack(
    anchor="w",
    padx=25,
    pady=(15, 5)
)


news_status = tk.Label(
    center_frame,
    text="Search for a city to see weather news",
    font=("Arial", 11),
    fg="#9AA9BD",
    bg="#0B1628"
)

news_status.pack(
    anchor="w",
    padx=25,
    pady=(0, 10)
)


# ---------------------------------------------------------
# NEWS CONTAINER
# ---------------------------------------------------------

news_frame = tk.Frame(
    center_frame,
    bg="#0B1628"
)

news_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)


# Keep image references
news_images = []


# ---------------------------------------------------------
# CLEAR NEWS
# ---------------------------------------------------------

def clear_news():

    for widget in news_frame.winfo_children():
        widget.destroy()

    news_images.clear()


# ---------------------------------------------------------
# OPEN NEWS
# ---------------------------------------------------------

def open_news(url):

    if url:
        webbrowser.open(url)


# ---------------------------------------------------------
# GET NEWS IMAGE
# ---------------------------------------------------------

def get_news_image(url):

    try:

        response = requests.get(
            url,
            timeout=5,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        html = response.text

        # Look for Open Graph image
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            html,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

        # Alternative format
        match = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
            html,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    except Exception as e:

        print("Could not get news image:", e)

    return None


# ---------------------------------------------------------
# CREATE NEWS CARD
# ---------------------------------------------------------

def create_news_card(
    parent,
    title,
    source,
    date,
    link,
    image_url,
    row,
    column
):

    card = tk.Frame(
        parent,
        bg="#162337",
        highlightbackground="#263A52",
        highlightthickness=1
    )

    card.grid(
        row=row,
        column=column,
        padx=8,
        pady=8,
        sticky="nsew"
    )

    parent.grid_columnconfigure(
        column,
        weight=1
    )

    parent.grid_rowconfigure(
        row,
        weight=1
    )


    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image_label = tk.Label(
        card,
        text="Loading image...",
        font=("Arial", 10),
        fg="#AAB7C8",
        bg="#24344B",
        height=8
    )

    image_label.pack(
        fill="x"
    )


    # Load image from article
    if image_url:

        try:

            image_response = requests.get(
                image_url,
                timeout=5,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            image_data = image_response.content

            from io import BytesIO

            image = Image.open(
                BytesIO(image_data)
            )

            image = image.resize(
                (260, 140)
            )

            photo = ImageTk.PhotoImage(
                image
            )

            image_label.config(
                image=photo,
                text=""
            )

            news_images.append(photo)

        except Exception as e:

            print("Image error:", e)

            image_label.config(
                text="📰",
                font=("Arial", 35)
            )


    # -----------------------------------------------------
    # SOURCE + TIME
    # -----------------------------------------------------

    source_label = tk.Label(
        card,
        text=f"{source} • {date}",
        font=("Arial", 9),
        fg="#8FA4BF",
        bg="#162337"
    )

    source_label.pack(
        anchor="w",
        padx=12,
        pady=(10, 3)
    )


    # -----------------------------------------------------
    # HEADLINE
    # -----------------------------------------------------

    headline = tk.Label(
        card,
        text=title,
        font=("Arial", 12, "bold"),
        fg="white",
        bg="#162337",
        wraplength=250,
        justify="left"
    )

    headline.pack(
        anchor="w",
        padx=12,
        pady=5
    )


    # -----------------------------------------------------
    # READ MORE BUTTON
    # -----------------------------------------------------

    read_button = tk.Button(
        card,
        text="Read More  →",
        font=("Arial", 9, "bold"),
        fg="white",
        bg="#1D4F91",
        activebackground="#2868B8",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        command=lambda: open_news(link)
    )

    read_button.pack(
        anchor="e",
        padx=12,
        pady=(5, 12)
    )



# =========================================================
# RIGHT FRAME
# =========================================================

right_frame = tk.Frame(
    root,
    bg="white",
    width=350
)

right_frame.pack(
    side="right",
    fill="y"
)

right_frame.pack_propagate(False)


# =========================================================
# CALENDAR
# =========================================================

calendar_title = tk.Label(
    right_frame,
    text="Calendar",
    font=("Arial", 18, "bold"),
    bg="white"
)

calendar_title.pack(pady=20)


calendar = Calendar(
    right_frame,
    selectmode="day",
    year=2026,
    month=8,
    day=10,
    date_pattern="dd/mm/yyyy"
)

calendar.pack(pady=20)


# =========================================================
# GET DATE
# =========================================================

def get_date():

    selected_date = calendar.get_date()

    print(
        "Selected Date:",
        selected_date
    )


date_button = tk.Button(
    right_frame,
    text="Get Selected Date",
    font=("Arial", 12),
    width=25,
    bg="#2196F3",
    fg="white",
    command=get_date
)

date_button.pack(pady=10)


# =========================================================
# START CLOCK
# =========================================================

update_time()


def get_weather_news(city):

    news_status.config(
        text=f"Loading weather news for {city}..."
    )

    threading.Thread(
        target=fetch_weather_news,
        args=(city,),
        daemon=True
    ).start()






def fetch_weather_news(city):

    try:

        query = quote_plus(
            f"{city} weather"
        )

        url = (
            "https://news.google.com/rss/search?"
            f"q={query}&hl=en-US&gl=US&ceid=US:en"
        )

        response = requests.get(
            url,
            timeout=5
        )

        response.raise_for_status()

        root.after(
            0,
            display_weather_news,
            response.text,
            city
        )

    except requests.exceptions.Timeout:

        root.after(
            0,
            news_error,
            "Weather news request timed out."
        )

    except requests.exceptions.ConnectionError:

        root.after(
            0,
            news_error,
            "No internet connection."
        )

    except Exception as e:

        print("News error:", e)

        root.after(
            0,
            news_error,
            "Could not load weather news."
        )


def news_error(message):

    news_status.config(
        text=message
    )





def display_weather_news(xml_data, city):

    try:

        root_element = ET.fromstring(
            xml_data
        )

        articles = root_element.findall(
            ".//item"
        )

        # Clear previous cards
        clear_news()


        if not articles:

            news_status.config(
                text=f"No weather news found for {city}"
            )

            return


        # -------------------------------------------------
        # DISPLAY NEWS CARDS
        # -------------------------------------------------

        for index, article in enumerate(
            articles[:6]
        ):

            title_element = article.find(
                "title"
            )

            link_element = article.find(
                "link"
            )

            date_element = article.find(
                "pubDate"
            )


            title = (
                title_element.text
                if title_element is not None
                else "No title available"
            )


            link = (
                link_element.text
                if link_element is not None
                else ""
            )


            date = (
                date_element.text
                if date_element is not None
                else ""
            )


            # -------------------------------------------------
            # FIND SOURCE
            # -------------------------------------------------

            source = "Weather News"

            if " - " in title:

                parts = title.rsplit(
                    " - ",
                    1
                )

                title = parts[0]

                source = parts[1]


            # -------------------------------------------------
            # GET IMAGE
            # -------------------------------------------------

            image_url = None

            if link:

                image_url = get_news_image(
                    link
                )


            # -------------------------------------------------
            # GRID POSITION
            # -------------------------------------------------

            row = index // 3

            column = index % 3


            # -------------------------------------------------
            # CREATE CARD
            # -------------------------------------------------

            create_news_card(
                news_frame,
                title,
                source,
                date,
                link,
                image_url,
                row,
                column
            )


        news_status.config(
            text=f"Latest weather news for {city}"
        )


    except Exception as e:

        print(
            "News display error:",
            e
        )

        news_status.config(
            text="Could not display weather news."
        )







# =========================================================
# START APPLICATION
# =========================================================

root.mainloop()