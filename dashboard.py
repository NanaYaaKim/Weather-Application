#dashboard/ main window
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk
from config import API_KEY
print("API_KEY:", API_KEY)  # Print the API key to verify it's being imported correctly



def update_time():
    current_time = datetime.now()

    date = current_time.strftime("%A, %B %d, %Y")
    time = current_time.strftime("%I:%M:%S %p")
    time_label.config(text=f"Date: {date} \nTime: {time}")
    root.after(1000, update_time) 
    update_time()  # Update every second

root = tk.Tk()
root.title("Smart Weather Assistant")
root.geometry("1400x850")
root.configure(bg="white")
root.state("zoomed")  # Maximize the window


#top_frame to hold the title,date,logo and profile
top_frame = tk.Frame(root, bg="#2196F3", height=100)
top_frame.pack(fill="x")

#logo image
logo = Image.open("logo.png")
logo = logo.resize((60, 60))
logo = ImageTk.PhotoImage(logo)

logo_label = tk.Label(top_frame, image=logo, bg="#2196F3")
logo_label.image = logo  # Keep a reference to avoid garbage collection
logo_label.pack(side="left", padx=15, pady=10)



#title
title = tk.Label(
    top_frame,
      text="Smart Weather Assistant",
      font=("Arial" , 24, "bold"),
      fg="white"
)
title.pack(side="left", padx=20, pady=20)

time_label = tk.Label(
    top_frame,
    text="Time: 12:00 PM",
    font=("Arial", 12),
    fg="white",
    bg="#2196F3"
)
time_label.pack(side="right", padx=20, pady=20)


#left frame to place the search bar,voice assistant and map
left_frame = tk.Frame(root, bg="white", width=350)
left_frame.pack(side="left", fill="y")


#search bar to search the location
search_label = tk.Label(
    left_frame,
    text="Search Location:",
    font=("Arial", 14),
    width=25,
)
search_label.pack(pady=10)

city_entry = tk.Entry(
    left_frame,
    font=("Arial", 14),
    width=25,
)
city_entry.pack(pady=5)

#search button to search the location
search_button = tk.Button(
    left_frame,
    text="Search",
    font=("Arial", 12),
    width=25,
    bg="#2196F3",
    fg="white",
    # width=18
)
search_button.pack(pady=10)

#voice assistant button to search the location
voice_button = tk.Button(
    left_frame,
    text="Voice Assistant",
    font=("Arial", 12),
    width=25,
    bg="#2196F3",
    fg="white",
    # width=18
)
voice_button.pack(pady=5)

#center frame  to display the weather information
center_frame = tk.Frame(root, bg="#F5F5F5")
center_frame.pack(side="left", fill="both", expand=True)

#weather information area
weather_title = tk.Label(
    center_frame,
    text="Today's Weather Information",
    font=("Arial", 22, "bold"),
    bg="#F5F5F5"
)
weather_title.pack(pady=10)

#placeholder for weather information
temperature = tk.Label(
    center_frame,
    text="Temperature:-- °C",
    font=("Arial", 16),
    bg="#F5F5F5"
)

temperature.pack(pady=5)

humidity = tk.Label(
    center_frame,
    text="Humidity:-- %",
    font=("Arial", 16),
    bg="#F5F5F5"
)
humidity.pack(pady=5)

wind = tk.Label(
    center_frame,
    text="Wind Speed:-- km/h",
    font=("Arial", 16),
    bg="#F5F5F5"
)
wind.pack(pady=5)


#right_frame to display the calendar, Al assistant ,notifications and news
right_frame = tk.Frame(root, bg="white", width=350)
right_frame.pack(side="right", fill="y")  

#calendar area
calendar_title = tk.Label(
    right_frame,
    text="Calendar",
    font=("Arial", 18, "bold"),
    bg="white"
)
calendar_title.pack(pady=20)

  












root.mainloop()