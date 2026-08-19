import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import tkintermapview
import pyttsx3
import speech_recognition as sr
import threading
import requests
import webbrowser
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from config import API_KEY




# =========================================================
# THEME SETTINGS
# =========================================================

dark_mode = False

LIGHT_THEME = {
    "bg": "#F4F7FB",
    "fg": "#1F2937",
    "card": "#FFFFFF",
    "button": "#2563EB",
    "button_fg": "#FFFFFF",
    "entry": "#FFFFFF",
}

DARK_THEME = {
    "bg": "#111827",
    "fg": "#F9FAFB",
    "card": "#1F2937",
    "button": "#3B82F6",
    "button_fg": "#FFFFFF",
    "entry": "#374151",
}


# =========================================================
# SETTINGS
# =========================================================

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
NEWS_URL = "https://news.google.com/rss/search"

BG = "#0B1628"
CARD_BG = "#162337"
BLUE = "#2196F3"
LIGHT = "#F5F5F5"
MUTED = "#9AA9BD"
WHITE = "white"


# =========================================================
# THREAD POOL
# =========================================================

executor = ThreadPoolExecutor(max_workers=8)


# =========================================================
# HTTP SESSION
# =========================================================

request_session = requests.Session()

request_session.headers.update({
    "User-Agent": "Smart Weather Assistant/1.0"
})


# =========================================================
# TEXT TO SPEECH
# =========================================================

try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)

    speech_lock = threading.Lock()

except Exception as e:
    engine = None
    speech_lock = threading.Lock()

    print("Text-to-speech initialization error:", e)


def speak(text):
    """Speak without freezing the Tkinter interface."""

    if engine is None:
        print("Text-to-speech engine is unavailable.")
        return

    def worker():
        try:
            with speech_lock:
                engine.say(text)
                engine.runAndWait()

        except Exception as e:
            print("Speech error:", repr(e))

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()

root.title("Smart Weather Assistant")
root.geometry("1400x850")
root.minsize(1100, 700)

# Start in LIGHT MODE
root.configure(bg=LIGHT_THEME["bg"])

try:
    root.state("zoomed")
except tk.TclError:
    pass


# =========================================================
# DARK / LIGHT MODE
# =========================================================

def toggle_theme():
    global dark_mode

    dark_mode = not dark_mode

    theme = DARK_THEME if dark_mode else LIGHT_THEME

    # Change main window
    root.configure(bg=theme["bg"])

    def update_widget(widget):

        try:
            widget_class = widget.winfo_class()

            # Frames
            if widget_class in ("Frame", "Labelframe"):
                widget.configure(
                    bg=theme["card"]
                )

            # Labels
            elif widget_class == "Label":
                widget.configure(
                    bg=theme["card"],
                    fg=theme["fg"]
                )

            # Buttons
            elif widget_class == "Button":
                widget.configure(
                    bg=theme["button"],
                    fg=theme["button_fg"],
                    activebackground=theme["button"],
                    activeforeground=theme["button_fg"]
                )

            # Entry boxes
            elif widget_class == "Entry":
                widget.configure(
                    bg=theme["entry"],
                    fg=theme["fg"],
                    insertbackground=theme["fg"]
                )

            # Text boxes
            elif widget_class == "Text":
                widget.configure(
                    bg=theme["entry"],
                    fg=theme["fg"],
                    insertbackground=theme["fg"]
                )

        except tk.TclError:
            pass

        # Update child widgets
        for child in widget.winfo_children():
            update_widget(child)

    update_widget(root)

    # Change button text
    if dark_mode:
        theme_button.config(text="☀ Light Mode")
    else:
        theme_button.config(text="🌙 Dark Mode")


# =========================================================
# THEME BUTTON
# =========================================================

theme_button = tk.Button(
    root,
    text="🌙 Dark Mode",
    command=toggle_theme,
    font=("Arial", 11, "bold"),
    padx=10,
    pady=5
)

theme_button.pack(pady=10)





# =========================================================
# GLOBAL STATE
# =========================================================

search_lock = threading.Lock()

search_in_progress = False
voice_listening = False

icon_cache = {}
news_images = []


# =========================================================
# SAFE TKINTER CALLBACK
# =========================================================

def safe_after(function, *args):
    """
    Safely call a Tkinter function from a worker thread.
    """

    try:
        if root.winfo_exists():
            root.after(
                0,
                function,
                *args
            )

    except tk.TclError:
        pass


# =========================================================
# IMAGE HELPER
# =========================================================

def image_from_file(path, size):
    """
    Load and resize an image.
    """

    try:
        image = Image.open(path)

        image.thumbnail(
            size,
            Image.Resampling.LANCZOS
        )

        return ImageTk.PhotoImage(image)

    except Exception as e:

        print(
            f"Could not load image {path}:",
            repr(e)
        )

        return None


# =========================================================
# TOP FRAME
# =========================================================

top_frame = tk.Frame(
    root,
    bg=BLUE,
    height=90
)

top_frame.pack(
    fill="x"
)

top_frame.pack_propagate(False)


# =========================================================
# LOGO
# =========================================================

logo = image_from_file(
    "image/logo.png",
    (60, 60)
)

if logo:

    logo_label = tk.Label(
        top_frame,
        image=logo,
        bg=BLUE
    )

    logo_label.image = logo

    logo_label.pack(
        side="left",
        padx=15
    )


# =========================================================
# TITLE
# =========================================================

title = tk.Label(
    top_frame,
    text="Smart Weather Assistant",
    font=("Arial", 24, "bold"),
    fg=WHITE,
    bg=BLUE
)

title.pack(
    side="left",
    padx=15
)


# =========================================================
# DATE AND TIME
# =========================================================

time_label = tk.Label(
    top_frame,
    text="Date: --\nTime: --",
    font=("Arial", 13),
    fg=WHITE,
    bg=BLUE,
    justify="right"
)

time_label.pack(
    side="right",
    padx=20
)


def update_time():
    """
    Update date and time every second.
    """

    try:

        now = datetime.now()

        time_label.config(
            text=(
                f"Date: {now.strftime('%A, %B %d, %Y')}\n"
                f"Time: {now.strftime('%I:%M:%S %p')}"
            )
        )

        root.after(
            1000,
            update_time
        )

    except tk.TclError:
        pass


# =========================================================
# MAIN LAYOUT
# =========================================================

left_frame = tk.Frame(
    root,
    bg=WHITE,
    width=350
)

left_frame.pack(
    side="left",
    fill="y"
)

left_frame.pack_propagate(False)


right_frame = tk.Frame(
    root,
    bg=WHITE,
    width=350
)

right_frame.pack(
    side="right",
    fill="y"
)

right_frame.pack_propagate(False)


center_frame = tk.Frame(
    root,
    bg=BG
)

center_frame.pack(
    side="left",
    fill="both",
    expand=True
)


# =========================================================
# LEFT FRAME - SEARCH
# =========================================================

search_label = tk.Label(
    left_frame,
    text="Search Location",
    font=("Arial", 14, "bold"),
    bg=WHITE,
    fg="#222222"
)

search_label.pack(
    pady=(15, 7)
)


city_entry = tk.Entry(
    left_frame,
    font=("Arial", 14),
    width=25,
    relief="solid",
    bd=1
)

city_entry.pack(
    pady=5,
    padx=15,
    fill="x"
)


# Enter key search
city_entry.bind(
    "<Return>",
    lambda event: search_weather()
)


# =========================================================
# SEARCH BUTTON
# =========================================================

search_button = tk.Button(
    left_frame,
    text="Search",
    font=("Arial", 12, "bold"),
    bg=BLUE,
    fg=WHITE,
    activebackground="#1976D2",
    activeforeground=WHITE,
    relief="flat",
    cursor="hand2",
    command=lambda: search_weather()
)

search_button.pack(
    pady=8,
    padx=15,
    fill="x"
)


# =========================================================
# VOICE BUTTON
# =========================================================

voice_button = tk.Button(
    left_frame,
    text="🎤 Voice Assistant",
    font=("Arial", 12, "bold"),
    bg=BLUE,
    fg=WHITE,
    activebackground="#1976D2",
    activeforeground=WHITE,
    relief="flat",
    cursor="hand2",
    command=lambda: voice_search()
)

voice_button.pack(
    pady=4,
    padx=15,
    fill="x"
)


# =========================================================
# STATUS
# =========================================================

status_label = tk.Label(
    left_frame,
    text="Ready",
    font=("Arial", 10),
    fg="#555555",
    bg=WHITE,
    wraplength=310
)

status_label.pack(
    pady=5,
    padx=15
)


# =========================================================
# LEFT FRAME - MAP
# =========================================================

map_title = tk.Label(
    left_frame,
    text="📍 Location Map",
    font=("Arial", 14, "bold"),
    bg=WHITE,
    fg="#222222"
)

map_title.pack(
    pady=(12, 5)
)


map_widget = tkintermapview.TkinterMapView(
    left_frame,
    width=330,
    height=390,
    corner_radius=0
)

map_widget.pack(
    padx=10,
    pady=5,
    fill="both",
    expand=True
)


# Default Accra location
map_widget.set_position(
    5.6037,
    -0.1870
)

map_widget.set_zoom(10)


# =========================================================
# CENTER FRAME - WEATHER HEADER
# =========================================================

weather_header = tk.Frame(
    center_frame,
    bg=LIGHT
)

weather_header.pack(
    fill="x",
    padx=15,
    pady=(15, 5)
)


weather_title = tk.Label(
    weather_header,
    text="Today's Weather Information",
    font=("Arial", 21, "bold"),
    bg=LIGHT,
    fg="#172033"
)

weather_title.pack(
    pady=(12, 3)
)


location_label = tk.Label(
    weather_header,
    text="Search for a city",
    font=("Arial", 18, "bold"),
    bg=LIGHT,
    fg="#172033"
)

location_label.pack(
    pady=3
)


description_label = tk.Label(
    weather_header,
    text="Weather: --",
    font=("Arial", 14),
    bg=LIGHT,
    fg="#344054"
)

description_label.pack(
    pady=(3, 12)
)


# =========================================================
# WEATHER INFORMATION
# =========================================================

weather_info = tk.Frame(
    center_frame,
    bg=BG
)

weather_info.pack(
    fill="x",
    padx=20,
    pady=5
)


icon_label = tk.Label(
    weather_info,
    bg=BG
)

icon_label.pack(
    pady=3
)


temperature_label = tk.Label(
    weather_info,
    text="Temperature: -- °C",
    font=("Arial", 18, "bold"),
    fg=WHITE,
    bg=BG
)

temperature_label.pack(
    pady=3
)


humidity_label = tk.Label(
    weather_info,
    text="Humidity: -- %",
    font=("Arial", 13),
    fg=MUTED,
    bg=BG
)

humidity_label.pack(
    pady=2
)


wind_label = tk.Label(
    weather_info,
    text="Wind Speed: -- m/s",
    font=("Arial", 13),
    fg=MUTED,
    bg=BG
)

wind_label.pack(
    pady=2
)


# =========================================================
# WEATHER ICON
# =========================================================

def update_weather_icon(weather):

    files = {
        "Clear": "image/sun.png",
        "Clouds": "image/cloud.png",
        "Rain": "image/rain.png",
        "Drizzle": "image/rain.png",
        "Thunderstorm": "image/storm.png",
        "Snow": "image/cloud.png",
        "Mist": "image/cloud.png",
        "Fog": "image/cloud.png",
        "Haze": "image/cloud.png"
    }

    filename = files.get(
        weather,
        "image/cloud.png"
    )

    if filename not in icon_cache:

        photo = image_from_file(
            filename,
            (110, 110)
        )

        if photo:
            icon_cache[filename] = photo

    photo = icon_cache.get(filename)

    if photo:

        icon_label.config(
            image=photo,
            text=""
        )

        icon_label.image = photo

    else:

        icon_label.config(
            image="",
            text="🌤️",
            font=("Arial", 50)
        )


update_weather_icon("Clear")


# =========================================================
# WEATHER NEWS TITLE
# =========================================================

news_title = tk.Label(
    center_frame,
    text="📰 Weather News",
    font=("Arial", 20, "bold"),
    fg=WHITE,
    bg=BG
)

news_title.pack(
    anchor="w",
    padx=25,
    pady=(10, 2)
)


news_status = tk.Label(
    center_frame,
    text="Search for a city to see weather news",
    font=("Arial", 10),
    fg=MUTED,
    bg=BG
)

news_status.pack(
    anchor="w",
    padx=25,
    pady=(0, 5)
)


# =========================================================
# SCROLLABLE NEWS AREA
# =========================================================

news_container = tk.Frame(
    center_frame,
    bg=BG
)

news_container.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)


# Canvas
news_canvas = tk.Canvas(
    news_container,
    bg=BG,
    highlightthickness=0,
    bd=0
)

news_canvas.pack(
    side="left",
    fill="both",
    expand=True
)


# Scrollbar
news_scrollbar = tk.Scrollbar(
    news_container,
    orient="vertical",
    command=news_canvas.yview
)

news_scrollbar.pack(
    side="right",
    fill="y"
)


news_canvas.configure(
    yscrollcommand=news_scrollbar.set
)


# Inner frame
news_frame = tk.Frame(
    news_canvas,
    bg=BG
)


news_window = news_canvas.create_window(
    (0, 0),
    window=news_frame,
    anchor="nw"
)


def update_news_scroll_region(event=None):
    """
    Update scrollable region whenever news cards change.
    """

    news_canvas.configure(
        scrollregion=news_canvas.bbox("all")
    )


def resize_news_frame(event):
    """
    Make the news frame fit the canvas width.
    """

    news_canvas.itemconfig(
        news_window,
        width=event.width
    )


news_frame.bind(
    "<Configure>",
    update_news_scroll_region
)

news_canvas.bind(
    "<Configure>",
    resize_news_frame
)


def news_mousewheel(event):
    """
    Scroll news using mouse wheel.
    """

    news_canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


# Mouse wheel
news_canvas.bind(
    "<MouseWheel>",
    news_mousewheel
)


# =========================================================
# NEWS CLEAR
# =========================================================

def clear_news():

    for widget in news_frame.winfo_children():
        widget.destroy()

    news_images.clear()

    news_canvas.yview_moveto(0)


# =========================================================
# OPEN NEWS
# =========================================================

def open_news(url):

    if url:

        try:
            webbrowser.open_new_tab(url)

        except Exception as e:

            print(
                "Could not open news link:",
                repr(e)
            )


# =========================================================
# BUTTON STATE
# =========================================================

def set_search_state(disabled):

    state = "disabled" if disabled else "normal"

    search_button.config(
        state=state
    )

    voice_button.config(
        state=state
    )


# =========================================================
# SEARCH WEATHER
# =========================================================

def search_weather():

    global search_in_progress

    city = city_entry.get().strip()

    if not city:

        status_label.config(
            text="Please enter a city."
        )

        return

    with search_lock:

        if search_in_progress:

            status_label.config(
                text="A search is already running..."
            )

            return

        search_in_progress = True

    set_search_state(True)

    status_label.config(
        text=f"Searching for {city}..."
    )

    news_status.config(
        text=f"Loading weather news for {city}..."
    )

    # Run weather and news at the same time
    executor.submit(
        get_weather,
        city
    )

    executor.submit(
        fetch_weather_news,
        city
    )


# =========================================================
# GET WEATHER
# =========================================================

def get_weather(city):

    try:

        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = request_session.get(
            WEATHER_URL,
            params=params,
            timeout=8
        )

        try:
            data = response.json()

        except ValueError:
            data = {}

        if response.status_code != 200:

            message = data.get(
                "message",
                "Location not found."
            )

            safe_after(
                search_failed,
                message
            )

            return

        main = data.get(
            "main",
            {}
        )

        weather = data.get(
            "weather",
            [{}]
        )[0]

        wind = data.get(
            "wind",
            {}
        )

        coord = data.get(
            "coord",
            {}
        )

        system = data.get(
            "sys",
            {}
        )

        result = {

            "city": data.get(
                "name",
                city
            ),

            "country": system.get(
                "country",
                ""
            ),

            "temperature": float(
                main.get(
                    "temp",
                    0
                )
            ),

            "feels_like": float(
                main.get(
                    "feels_like",
                    0
                )
            ),

            "humidity": int(
                main.get(
                    "humidity",
                    0
                )
            ),

            "pressure": int(
                main.get(
                    "pressure",
                    0
                )
            ),

            "visibility": int(
                data.get(
                    "visibility",
                    0
                )
            ),

            "wind": float(
                wind.get(
                    "speed",
                    0
                )
            ),

            "description": weather.get(
                "description",
                "Unknown"
            ),

            "main": weather.get(
                "main",
                "Clouds"
            ),

            "lat": float(
                coord.get(
                    "lat",
                    0
                )
            ),

            "lon": float(
                coord.get(
                    "lon",
                    0
                )
            ),

            "sunrise": system.get(
                "sunrise",
                0
            ),

            "sunset": system.get(
                "sunset",
                0
            )
        }

        # Air quality
        air_result = get_air_quality(
            result["lat"],
            result["lon"]
        )

        result["air_quality"] = air_result

        safe_after(
            update_weather_display,
            result
        )

    except requests.exceptions.Timeout:

        safe_after(
            search_failed,
            "The weather service took too long to respond."
        )

    except requests.exceptions.ConnectionError:

        safe_after(
            search_failed,
            "No internet connection."
        )

    except Exception as e:

        print(
            "Weather error:",
            repr(e)
        )

        safe_after(
            search_failed,
            "Something went wrong while loading weather."
        )


# =========================================================
# AIR QUALITY
# =========================================================

def get_air_quality(lat, lon):

    try:

        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY
        }

        response = request_session.get(
            AIR_URL,
            params=params,
            timeout=6
        )

        if response.status_code != 200:

            return None

        data = response.json()

        item = data.get(
            "list",
            [{}]
        )[0]

        aqi = item.get(
            "main",
            {}
        ).get(
            "aqi"
        )

        components = item.get(
            "components",
            {}
        )

        labels = {
            1: "Good",
            2: "Fair",
            3: "Moderate",
            4: "Poor",
            5: "Very Poor"
        }

        return {

            "aqi": aqi,

            "label": labels.get(
                aqi,
                "Unknown"
            ),

            "pm25": components.get(
                "pm2_5"
            ),

            "pm10": components.get(
                "pm10"
            )
        }

    except Exception as e:

        print(
            "Air quality error:",
            repr(e)
        )

        return None


# =========================================================
# TIMESTAMP
# =========================================================

def format_timestamp(timestamp):

    if not timestamp:
        return "--"

    try:

        return datetime.fromtimestamp(
            timestamp
        ).strftime(
            "%I:%M %p"
        )

    except Exception:

        return "--"


# =========================================================
# UPDATE WEATHER DISPLAY
# =========================================================

def update_weather_display(result):

    global search_in_progress

    city = result["city"]
    country = result["country"]

    temperature = result["temperature"]
    feels_like = result["feels_like"]

    humidity = result["humidity"]
    wind = result["wind"]

    description = result["description"]
    weather_main = result["main"]

    lat = result["lat"]
    lon = result["lon"]

    location_label.config(
        text=(
            f"{city}, {country}"
            if country
            else city
        )
    )

    description_label.config(
        text=description.title()
    )

    temperature_label.config(
        text=f"Temperature: {temperature:.1f} °C"
    )

    humidity_label.config(
        text=f"Humidity: {humidity}%"
    )

    wind_label.config(
        text=f"Wind Speed: {wind:.1f} m/s"
    )

    update_weather_icon(
        weather_main
    )

    # Update map
    try:

        map_widget.set_position(
            lat,
            lon
        )

        map_widget.set_zoom(10)

    except Exception as e:

        print(
            "Map update error:",
            repr(e)
        )

    # Climate panel
    update_climate_panel(
        result
    )

    status_label.config(
        text=(
            f"Weather updated successfully "
            f"for {city}."
        )
    )

    with search_lock:
        search_in_progress = False

    set_search_state(False)

    # Text to speech
    speak(
        f"The current weather in {city} is "
        f"{description}. "
        f"The temperature is "
        f"{temperature:.1f} degrees Celsius."
    )


# =========================================================
# SEARCH FAILED
# =========================================================

def search_failed(message):

    global search_in_progress

    status_label.config(
        text=message
    )

    with search_lock:
        search_in_progress = False

    set_search_state(False)

    print(
        "Search failed:",
        message
    )


# =========================================================
# CLIMATE INFORMATION
# =========================================================

climate_title = tk.Label(
    right_frame,
    text="🌍 Climate Information",
    font=("Arial", 18, "bold"),
    bg=WHITE,
    fg="#172033"
)

climate_title.pack(
    pady=(20, 5)
)


climate_location = tk.Label(
    right_frame,
    text="Search for a city",
    font=("Arial", 12, "bold"),
    bg=WHITE,
    fg="#555555",
    wraplength=310
)

climate_location.pack(
    pady=(0, 12)
)


# =========================================================
# CLIMATE ROW
# =========================================================

def make_climate_row(
    parent,
    title_text,
    value_text="--"
):

    row = tk.Frame(
        parent,
        bg="#F3F6FA"
    )

    row.pack(
        fill="x",
        padx=15,
        pady=4
    )

    title_label = tk.Label(
        row,
        text=title_text,
        font=("Arial", 10, "bold"),
        bg="#F3F6FA",
        fg="#555555",
        anchor="w"
    )

    title_label.pack(
        side="left",
        padx=10,
        pady=8
    )

    value_label = tk.Label(
        row,
        text=value_text,
        font=("Arial", 10),
        bg="#F3F6FA",
        fg="#172033",
        anchor="e"
    )

    value_label.pack(
        side="right",
        padx=10,
        pady=8
    )

    return value_label


feels_like_value = make_climate_row(
    right_frame,
    "Feels Like"
)

pressure_value = make_climate_row(
    right_frame,
    "Pressure"
)

visibility_value = make_climate_row(
    right_frame,
    "Visibility"
)

sunrise_value = make_climate_row(
    right_frame,
    "Sunrise"
)

sunset_value = make_climate_row(
    right_frame,
    "Sunset"
)

aqi_value = make_climate_row(
    right_frame,
    "Air Quality"
)

pm25_value = make_climate_row(
    right_frame,
    "PM2.5"
)

pm10_value = make_climate_row(
    right_frame,
    "PM10"
)


# =========================================================
# UPDATE CLIMATE PANEL
# =========================================================

def update_climate_panel(result):

    climate_location.config(
        text=(
            f"Current climate details "
            f"for {result['city']}"
        )
    )

    feels_like_value.config(
        text=(
            f"{result['feels_like']:.1f} °C"
        )
    )

    pressure_value.config(
        text=(
            f"{result['pressure']} hPa"
        )
    )

    visibility_km = (
        result["visibility"] / 1000
    )

    visibility_value.config(
        text=(
            f"{visibility_km:.1f} km"
        )
    )

    sunrise_value.config(
        text=format_timestamp(
            result["sunrise"]
        )
    )

    sunset_value.config(
        text=format_timestamp(
            result["sunset"]
        )
    )

    air = result.get(
        "air_quality"
    )

    if air:

        aqi_value.config(
            text=(
                f"{air['aqi']} - "
                f"{air['label']}"
            )
        )

        pm25 = air.get(
            "pm25"
        )

        pm10 = air.get(
            "pm10"
        )

        pm25_value.config(
            text=(
                f"{pm25:.1f} µg/m³"
                if pm25 is not None
                else "--"
            )
        )

        pm10_value.config(
            text=(
                f"{pm10:.1f} µg/m³"
                if pm10 is not None
                else "--"
            )
        )

    else:

        aqi_value.config(
            text="Unavailable"
        )

        pm25_value.config(
            text="Unavailable"
        )

        pm10_value.config(
            text="Unavailable"
        )


# =========================================================
# VOICE SEARCH
# =========================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

recognizer.pause_threshold = 0.8
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5


def voice_search():

    global voice_listening

    with search_lock:

        if search_in_progress:

            status_label.config(
                text=(
                    "Please wait for the "
                    "current search to finish."
                )
            )

            return

    if voice_listening:
        return

    voice_listening = True

    voice_button.config(
        state="disabled",
        text="🎤 Listening..."
    )

    search_button.config(
        state="disabled"
    )

    status_label.config(
        text="🎤 Speak the city name now..."
    )

    executor.submit(
        listen_for_city
    )


# =========================================================
# LISTEN FOR CITY
# =========================================================

def listen_for_city():

    global voice_listening

    try:

        # -------------------------------------------------
        # Check microphones
        # -------------------------------------------------

        microphones = (
            sr.Microphone
            .list_microphone_names()
        )

        if not microphones:

            raise Exception(
                "No microphone was found."
            )

        print(
            "Available microphones:"
        )

        for index, name in enumerate(
            microphones
        ):

            print(
                index,
                name
            )

        # -------------------------------------------------
        # Open microphone
        # -------------------------------------------------

        with sr.Microphone() as source:

            safe_after(
                status_label.config,
                text=(
                    "🎤 Adjusting microphone..."
                )
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            safe_after(
                status_label.config,
                text=(
                    "🎤 Listening... "
                    "Say a city name."
                )
            )

            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=5
            )

        # -------------------------------------------------
        # Recognition
        # -------------------------------------------------

        safe_after(
            status_label.config,
            text="🔎 Recognizing your voice..."
        )

        city = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        city = city.strip()

        print(
            "Recognized speech:",
            city
        )

        if not city:

            raise Exception(
                "No city name was recognized."
            )

        safe_after(
            set_voice_city,
            city
        )

    except sr.WaitTimeoutError:

        safe_after(
            voice_error,
            (
                "⏱️ No speech detected. "
                "Please try again."
            )
        )

    except sr.UnknownValueError:

        safe_after(
            voice_error,
            (
                "❌ I could not understand "
                "the city name."
            )
        )

    except sr.RequestError as e:

        print(
            "Google speech recognition error:",
            repr(e)
        )

        safe_after(
            voice_error,
            (
                "❌ Speech service unavailable. "
                "Check your internet connection."
            )
        )

    except AttributeError as e:

        print(
            "PyAudio/microphone error:",
            repr(e)
        )

        safe_after(
            voice_error,
            (
                "❌ Microphone support is missing. "
                "Install PyAudio."
            )
        )

    except OSError as e:

        print(
            "Microphone OS error:",
            repr(e)
        )

        safe_after(
            voice_error,
            (
                "❌ Could not access the microphone. "
                "Check Windows microphone permissions."
            )
        )

    except Exception as e:

        print(
            "VOICE ERROR:",
            repr(e)
        )

        safe_after(
            voice_error,
            f"❌ Voice error: {e}"
        )


# =========================================================
# SET VOICE CITY
# =========================================================

def set_voice_city(city):

    global search_in_progress
    global voice_listening

    voice_listening = False

    city_entry.delete(
        0,
        tk.END
    )

    city_entry.insert(
        0,
        city
    )

    status_label.config(
        text=f"Voice recognized: {city}"
    )

    with search_lock:
        search_in_progress = False

    voice_button.config(
        state="normal",
        text="🎤 Voice Assistant"
    )

    search_button.config(
        state="normal"
    )

    # Automatically search
    search_weather()


# =========================================================
# VOICE ERROR
# =========================================================

def voice_error(message):

    global voice_listening
    global search_in_progress

    voice_listening = False

    status_label.config(
        text=message
    )

    with search_lock:
        search_in_progress = False

    voice_button.config(
        state="normal",
        text="🎤 Voice Assistant"
    )

    search_button.config(
        state="normal"
    )

    print(
        message
    )


# =========================================================
# NEWS FUNCTIONS
# =========================================================

def fetch_weather_news(city):

    try:

        params = {
            "q": f"{city} weather",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en"
        }

        response = request_session.get(
            NEWS_URL,
            params=params,
            timeout=8
        )

        response.raise_for_status()

        articles = parse_news_xml(
            response.text
        )

        if not articles:

            safe_after(
                news_error,
                f"No weather news found for {city}."
            )

            return

        prepared_articles = []

        # Load article metadata
        for article in articles[:6]:

            image_url = get_news_image(
                article["link"]
            )

            article["image_url"] = image_url

            prepared_articles.append(
                article
            )

        safe_after(
            display_weather_news,
            prepared_articles,
            city
        )

    except requests.exceptions.Timeout:

        safe_after(
            news_error,
            "Weather news request timed out."
        )

    except requests.exceptions.ConnectionError:

        safe_after(
            news_error,
            "No internet connection."
        )

    except Exception as e:

        print(
            "News error:",
            repr(e)
        )

        safe_after(
            news_error,
            "Could not load weather news."
        )


# =========================================================
# PARSE NEWS XML
# =========================================================

def parse_news_xml(xml_data):

    try:

        root_element = ET.fromstring(
            xml_data
        )

    except ET.ParseError as e:

        print(
            "News XML error:",
            repr(e)
        )

        return []

    articles = []

    for item in root_element.findall(
        ".//item"
    ):

        title = item.findtext(
            "title",
            default="No title available"
        )

        link = item.findtext(
            "link",
            default=""
        )

        date = item.findtext(
            "pubDate",
            default=""
        )

        source = "Weather News"

        if " - " in title:

            title, source = title.rsplit(
                " - ",
                1
            )

        articles.append({

            "title": title.strip(),

            "source": source.strip(),

            "date": date.strip(),

            "link": link.strip(),

            "image_url": None

        })

    return articles


# =========================================================
# GET NEWS IMAGE
# =========================================================

def get_news_image(url):

    if not url:
        return None

    try:

        response = request_session.get(
            url,
            timeout=4
        )

        html = response.text

        patterns = [

            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',

            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image'

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.IGNORECASE
            )

            if match:

                return match.group(1)

    except Exception as e:

        print(
            "Could not get news image:",
            repr(e)
        )

    return None


# =========================================================
# DOWNLOAD NEWS IMAGE
# =========================================================

def download_news_image(image_url):

    if not image_url:
        return None

    try:

        response = request_session.get(
            image_url,
            timeout=4
        )

        response.raise_for_status()

        image = Image.open(
            BytesIO(
                response.content
            )
        ).convert("RGB")

        image = image.resize(
            (250, 125),
            Image.Resampling.LANCZOS
        )

        return ImageTk.PhotoImage(
            image
        )

    except Exception as e:

        print(
            "News image error:",
            repr(e)
        )

        return None


# =========================================================
# DISPLAY WEATHER NEWS
# =========================================================

def display_weather_news(
    articles,
    city
):

    clear_news()

    if not articles:

        news_status.config(
            text=(
                f"No weather news found "
                f"for {city}."
            )
        )

        return

    # Create news cards
    for index, article in enumerate(
        articles
    ):

        row = index // 3
        column = index % 3

        create_news_card(
            news_frame,
            article["title"],
            article["source"],
            article["date"],
            article["link"],
            row,
            column
        )

    news_status.config(
        text=(
            f"Latest weather news for {city} "
            f"• Scroll to see all articles"
        )
    )

    # Load images in background
    for index, article in enumerate(
        articles
    ):

        if article["image_url"]:

            executor.submit(
                load_news_card_image,
                index,
                article["image_url"]
            )

    # Reset scroll position
    news_canvas.yview_moveto(0)


# =========================================================
# CREATE NEWS CARD
# =========================================================

def create_news_card(
    parent,
    title_text,
    source,
    date,
    link,
    row,
    column
):

    card = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightbackground="#263A52",
        highlightthickness=1
    )

    card.grid(
        row=row,
        column=column,
        padx=7,
        pady=7,
        sticky="nsew"
    )

    parent.grid_columnconfigure(
        column,
        weight=1
    )

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image_label = tk.Label(
        card,
        text="📰",
        font=("Arial", 32),
        fg="#AAB7C8",
        bg="#24344B",
        width=26,
        height=5
    )

    image_label.pack(
        fill="x"
    )

    # Save label reference
    card.image_label = image_label

    # -----------------------------------------------------
    # SOURCE
    # -----------------------------------------------------

    source_label = tk.Label(
        card,
        text=f"{source} • {date}",
        font=("Arial", 8),
        fg="#8FA4BF",
        bg=CARD_BG,
        anchor="w"
    )

    source_label.pack(
        anchor="w",
        padx=10,
        pady=(8, 2)
    )

    # -----------------------------------------------------
    # HEADLINE
    # -----------------------------------------------------

    headline = tk.Label(
        card,
        text=title_text,
        font=("Arial", 11, "bold"),
        fg=WHITE,
        bg=CARD_BG,
        wraplength=250,
        justify="left",
        anchor="w"
    )

    headline.pack(
        fill="x",
        padx=10,
        pady=4
    )

    # -----------------------------------------------------
    # READ MORE
    # -----------------------------------------------------

    read_button = tk.Button(
        card,
        text="Read More →",
        font=("Arial", 9, "bold"),
        fg=WHITE,
        bg="#1D4F91",
        activebackground="#2868B8",
        activeforeground=WHITE,
        relief="flat",
        cursor="hand2",
        command=lambda url=link: open_news(url)
    )

    read_button.pack(
        anchor="e",
        padx=10,
        pady=(4, 10)
    )


# =========================================================
# FIND NEWS CARD LABELS
# =========================================================

def find_news_card_labels():

    labels = []

    for card in news_frame.winfo_children():

        label = getattr(
            card,
            "image_label",
            None
        )

        labels.append(
            label
        )

    return labels


# =========================================================
# LOAD NEWS CARD IMAGE
# =========================================================

def load_news_card_image(
    index,
    image_url
):

    photo = download_news_image(
        image_url
    )

    if photo is None:
        return

    safe_after(
        update_news_card_image,
        index,
        photo
    )


# =========================================================
# UPDATE NEWS CARD IMAGE
# =========================================================

def update_news_card_image(
    index,
    photo
):

    labels = find_news_card_labels()

    if (
        index >= len(labels)
        or labels[index] is None
    ):
        return

    label = labels[index]

    label.config(
        image=photo,
        text=""
    )

    label.image = photo

    news_images.append(
        photo
    )


# =========================================================
# NEWS ERROR
# =========================================================

def news_error(message):

    clear_news()

    news_status.config(
        text=message
    )


# =========================================================
# CLOSE WINDOW CLEANLY
# =========================================================

def on_close():

    print(
        "Closing Smart Weather Assistant..."
    )

    try:

        executor.shutdown(
            wait=False,
            cancel_futures=True
        )

    except Exception as e:

        print(
            "Executor shutdown error:",
            repr(e)
        )

    try:

        request_session.close()

    except Exception:
        pass

    try:

        if engine is not None:
            engine.stop()

    except Exception:
        pass

    try:

        root.destroy()

    except tk.TclError:
        pass


root.protocol(
    "WM_DELETE_WINDOW",
    on_close
)


# =========================================================
# START APPLICATION
# =========================================================

update_time()

# Default location
city_entry.insert(
    0,
    "Accra"
)

# Put cursor in search box
city_entry.focus_set()

root.mainloop()