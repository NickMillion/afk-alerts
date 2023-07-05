from python_imagesearch.imagesearch import region_grabber
import tkinter as tk
import win32gui
import time
from PIL import Image # Only if debugging is on
import random

notificationIcon = "mellon.ico"

debugging = False

# This is the function that will always be called if an alert is detected. It's kinda janky.
# Would be fantastic to have it run on a separate thread, based on what I've read? Unsure how to implement that currently.
def alertWindow(hwnd, alert, position=(0, 0)):    
    # Create a new window
    window = tk.Tk()
    window.title(alert)
    window.overrideredirect(True)
    # If position is 0, 0, center the window
    if position == (0, 0):
        # Get the screen's size
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        # Calculate the window's position
        position = ((screen_width - window.winfo_width()) // 2, (screen_height - window.winfo_height()) // 2)

    # Set the window's position
    window.geometry("+%d+%d" % (position[0], position[1]))
    window.geometry("700x700")
    window.configure(bg="blue")
    window.iconbitmap(notificationIcon)
    # Make the window always on top
    window.attributes("-topmost", True)
    # 50% opacity
    window.wm_attributes("-alpha", 0.75)
    # Tool window
    window.wm_attributes("-toolwindow", True)
    window.wm_attributes("-transparentcolor", "blue")
    # Remove the topbar

    window.lift()

    alertColors = ["red", "white", "yellow"]

    # Add a label to the window with a randomly selected alert color
    selectedColor = random.choice(alertColors)
    label = tk.Label(window, text=alert, font=("Arial Bold", 78), bg="blue", fg=selectedColor)
    label.pack()


    # Run the window loop for 500 ms
    window.after(500, window.destroy)
    window.mainloop()

# Print that we're running
print("AFK Alerts is running...")

# We want the user to input part of the name of the window they want to check
# windowName = input("Enter the name of the window you want to check: ")
windowName = "Velheim"

# If the user didn't input anything, print that we're exiting and exit
if windowName == "":
    print("No window name entered, exiting...")
    exit()

# Make an empty list to store the names of the windows
windowList = []

# Scan all windows and add the ones that match the input to the list
def winEnumHandler(hwnd, ctx):
    if win32gui.IsWindowVisible(hwnd):
        if windowName.lower() in win32gui.GetWindowText(hwnd).lower():
            windowList.append(win32gui.GetWindowText(hwnd))
win32gui.EnumWindows(winEnumHandler, None)

# Print all the windows we found that match input
print("Found " + str(len(windowList)) + " windows that match input.", flush=True)
# Print them all
print(windowList)

# Scan every 1 second by default, but can be anything. The tiny pixel scan alerts take ~0.05 seconds to run
SCAN_INTERVAL = 0.1

# If panic key is not pressed, loop every scan interval and check if the image is on screen
while True:
    # Iterate through all the found windows
    for i in range(0, len(windowList)):
        # Get the current window's image
        currentWindow = windowList[i]
        # Print that we're scanning this window
        print("Scanning window: " + currentWindow)

        # Get window's position and size
        window = win32gui.FindWindow(None, currentWindow)
        windowPos = win32gui.GetWindowRect(window)
        # Check if the window is focused
        if win32gui.GetForegroundWindow() == window:
            # Skip if it's focused
            continue

        # windowRegion = region_grabber(windowPos)
        hp = region_grabber((windowPos[2] - 225, windowPos[1] + 82, windowPos[2] - 195, windowPos[1] + 98))
        prayer = region_grabber((windowPos[2] - 230, windowPos[1] + 118, windowPos[2] - 203, windowPos[1] + 132))

        # Use Pillow to convert the Screenshot of the regions into a file for debugging
        if debugging:
            Image.frombytes('RGB', hp.size, hp.bgra, 'raw', 'BGRX').save("debug/hp" + str(i) + ".png")
            Image.frombytes('RGB', prayer.size, prayer.bgra, 'raw', 'BGRX').save("debug/prayer" + str(i) + ".png")

        # Get a random value between 350 and 400
        randVal = random.randint(250, 450)
        alertPosition = (windowPos[0] + 25, windowPos[1] + randVal)
        alerted = False
        # Iterate through all the pixels in hp to determine if there are any red
        for x in range(0, hp.size[0]):
            for y in range(0, hp.size[1]):
                # Get the pixel's RGB value
                pixel = hp.pixel(x, y)
                # If the pixel is red, alert
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    alertWindow(win32gui.FindWindow(None, currentWindow), "HP LOW", alertPosition)
                    alerted = True
                    break
            if alerted:
                break
        # Same thing for prayer
        for x in range(0, prayer.size[0]):
            for y in range(0, prayer.size[1]):
                pixel = prayer.pixel(x, y)
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    alertWindow(win32gui.FindWindow(None, currentWindow), "PRAYER LOW", alertPosition)
                    alerted = True
                    break
            if alerted:
                break
                
    if debugging:
        exit()

    time.sleep(SCAN_INTERVAL)