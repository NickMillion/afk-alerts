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
def alertWindow(hwnd, alert = "", position=(0, 0), windowSize=(700, 700)):    
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
    window.geometry(str(windowSize[0]) + "x" + str(windowSize[1]))
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
    # Text size must be at least 64, divide by the length of the alert to get the size
    # This will make it take up basically the entire window
    textSize = int(windowSize[0] / len(alert))
    if textSize < 64:
        textSize = 64
    label = tk.Label(window, text=alert, font=("Arial Bold", textSize), bg="blue", fg=selectedColor)
    label.pack()


    # Run the window loop for 500 ms
    window.after(500, window.destroy)
    window.mainloop()

# Print that we're running
print("AFK Alerts is running...")

# We want the user to input part of the name of the window they want to check
windowName = input("Enter the name of the window you want to check: ")

# If the user didn't input anything, print that we're exiting and exit
if windowName == "":
    print("No window name entered, assuming default.")
    windowName = "718/925"

# Make an empty list to store the names of the windows
windowList = []
timeSinceLastFocused = []

# Scan all windows and add the ones that match the input to the list
def winEnumHandler(hwnd, ctx):
    if win32gui.IsWindowVisible(hwnd):
        if windowName.lower() in win32gui.GetWindowText(hwnd).lower():
            windowList.append(win32gui.GetWindowText(hwnd))
            timeSinceLastFocused.append(0)
win32gui.EnumWindows(winEnumHandler, None)

# Print all the windows we found that match input
print("Found " + str(len(windowList)) + " windows that match input.", flush=True)
# Print them all
print(windowList)

# If we didn't find any windows, exit
if len(windowList) == 0:
    print("No windows found, exiting.")
    exit()

# Scan every 1 second by default, but can be anything. The tiny pixel scan alerts take ~0.05 seconds to run
SCAN_INTERVAL = 0.1
timeElapsed = 0
# If panic key is not pressed, loop every scan interval and check if the image is on screen
while True:
    startTime = time.time()
    # Iterate through all the found windows
    for i in range(0, len(windowList)):
        # Get the current window's image
        currentWindow = windowList[i]

        # Get window's position and size
        window = win32gui.FindWindow(None, currentWindow)
        windowPos = win32gui.GetWindowRect(window)
        windowSize = (windowPos[2] - windowPos[0], windowPos[3] - windowPos[1])
        # Check if the window is focused
        if win32gui.GetForegroundWindow() == window:
            timeSinceLastFocused[i] = 0
        
        # If it's not focused, increment the time since it was focused. Pretty sure this is wrong but it doesn't really matter.
        timeSinceLastFocused[i] += timeElapsed + SCAN_INTERVAL
        if debugging:
            print("Time since last focused for index " + str(i) + ": " + str(timeSinceLastFocused[i]), flush=True)

        # Put the alertPosition in the center of the window
        alertPosition = (windowPos[0], windowPos[1] + (windowSize[1] / 2))

        # If it's been more than ~180 seconds since the window was focused, alert AFK
        if timeSinceLastFocused[i] > 180:
            alertWindow(win32gui.FindWindow(None, currentWindow), "AFK", alertPosition, windowSize)
            continue


        # windowRegion = region_grabber(windowPos)
        hp = region_grabber((windowPos[2] - 225, windowPos[1] + 82, windowPos[2] - 195, windowPos[1] + 98))
        prayer = region_grabber((windowPos[2] - 230, windowPos[1] + 118, windowPos[2] - 203, windowPos[1] + 132))

        # Use Pillow to convert the Screenshot of the regions into a file for debugging
        if debugging:
            Image.frombytes('RGB', hp.size, hp.bgra, 'raw', 'BGRX').save("debug/hp" + str(i) + ".png")
            Image.frombytes('RGB', prayer.size, prayer.bgra, 'raw', 'BGRX').save("debug/prayer" + str(i) + ".png")

        alerted = False
        # Iterate through all the pixels in hp to determine if there are any red
        for x in range(0, hp.size[0]):
            for y in range(0, hp.size[1]):
                # Get the pixel's RGB value
                pixel = hp.pixel(x, y)
                # If the pixel is red, alert
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    alertWindow(win32gui.FindWindow(None, currentWindow), "HP LOW", alertPosition, windowSize)
                    alerted = True
                    break
            if alerted:
                break
        # Same thing for prayer
        for x in range(0, prayer.size[0]):
            for y in range(0, prayer.size[1]):
                pixel = prayer.pixel(x, y)
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    alertWindow(win32gui.FindWindow(None, currentWindow), "PRAYER LOW", alertPosition, windowSize)
                    alerted = True
                    break
            if alerted:
                break
                
    if debugging:
        exit()

    timeElapsed = time.time() - startTime

    time.sleep(SCAN_INTERVAL)