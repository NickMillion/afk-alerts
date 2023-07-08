from python_imagesearch.imagesearch import region_grabber
import tkinter as tk
import win32gui
import time
from PIL import Image # Only used if debugging is on to take screenshot of scanned regions
import random
from playsound import playsound # Make sure you're using version 1.2.2 or it'll error out
import pytesseract

# How often to scan the windows, in seconds. Should probably be above 0.05 but can otherwise be anything.
SCAN_INTERVAL = 0.1
# How many iterations to wait between checking HP and Prayer. Should be at least 1, but can be anything.
ITERATIONS_BETWEEN_HPPRAY_CHECK = 5
# How many iterations to wait between checking Chat. This is slightly more intensive than HP and Prayer, so it should be higher.
ITERATIONS_BETWEEN_CHAT_CHECK = 60

# If debugging is on, it will only do the first scan and print out some results and take screenshots of scanned regions before exiting
DEBUGGING = False
# How many seconds before printing the "Running for x minutes." message
TIME_BETWEEN_PRINTS = 60
# How long to keep the alert visible, in ms
ALERT_DURATION = 750
# Default window name
DEFAULT_WINDOW_NAME = "718/925"
# Audio files. These WILL play at whatever volume your python console is set to, so be careful.
MAJOR_ALERT = "major_alert.mp3"
MINOR_ALERT = "minor_alert.mp3"
# A dictionary of the alert types and their responses
ALERTS = {
    "Oh dear, you are dead!" : "YOU DIED",
}

# This is the function that will always be called if an alert is detected. It's kinda janky but works for our purposes.
# Would be fantastic to have it run on a separate thread, based on what I've read? Unsure how to implement that currently.
def alertWindow(hwnd, alert = "", position=(0, 0), windowSize=(700, 700), alert_audio=MAJOR_ALERT):    
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
    # Make the window always on top
    window.attributes("-topmost", True)
    # 50% opacity
    window.wm_attributes("-alpha", 0.75)
    # Tool window
    window.wm_attributes("-toolwindow", True)

    # Black will be transparent
    window.wm_attributes("-transparentcolor", "black")
    window.configure(bg="black")

    # Lift the window to the top so it's always visible, since it's an alert, duh
    window.lift()

    # List of colors to randomly select from, should be bright and varied to be attention-grabbing
    alertColors = ["red", "white", "yellow", "blue"]

    # Add a label to the window with a randomly selected alert color
    selectedColor = random.choice(alertColors)

    # Text size must be at least 64, divide by the length of the alert to get the size
    # This will make it take up basically the entire window
    textSize = int(windowSize[0] / len(alert))
    if textSize < 64:
        textSize = 64

    # Finally, add the label
    tk.Label(window, text=alert, font=("Arial Bold", textSize), bg="black", fg=selectedColor).pack()

    # Play audio
    if alert_audio != "":
        playsound(alert_audio, block=False)

    # Run the window loop for 500 ms
    window.after(ALERT_DURATION, window.destroy)
    window.mainloop()


    print("Alerted " + alert + " for window " + str(hwnd), flush=True)

def checkHPPray(windowPos, currentWindow, i):
    # Grab the regions of the screen that we want to check. These are hardcoded.
    hp = region_grabber((windowPos[2] - 225, windowPos[1] + 82, windowPos[2] - 195, windowPos[1] + 98))
    prayer = region_grabber((windowPos[2] - 230, windowPos[1] + 118, windowPos[2] - 203, windowPos[1] + 132))
    # Use Pillow to convert the Screenshot of the regions into a file for debugging
    if DEBUGGING:
        Image.frombytes('RGB', hp.size, hp.bgra, 'raw', 'BGRX').save("debug/hp" + str(i) + ".png")
        Image.frombytes('RGB', prayer.size, prayer.bgra, 'raw', 'BGRX').save("debug/prayer" + str(i) + ".png")
    # Iterate through all the pixels in hp and prayer to determine if there are any red
    # While the functionality is the same, I'm keeping them separate in case I want to add more alerts later that do something else
    for x in range(0, hp.size[0]):
        for y in range(0, hp.size[1]):
            # Get the pixel's RGB value
            pixel = hp.pixel(x, y)
            # If the pixel is red, alert
            if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                alertWindow(win32gui.FindWindow(None, currentWindow), "HP LOW", alertPosition, windowSize, MAJOR_ALERT)
                return True
    for x in range(0, prayer.size[0]):
        for y in range(0, prayer.size[1]):
            pixel = prayer.pixel(x, y)
            if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                alertWindow(win32gui.FindWindow(None, currentWindow), "PRAYER LOW", alertPosition, windowSize, MINOR_ALERT)
                return True

    return False

def checkChat(windowPos, currentWindow, i):
    # Grab the bottom left corner of the window in a 550x150 region
    chatBox = region_grabber((windowPos[0] + 5, windowPos[3] - 150, windowPos[0] + 555, windowPos[3] - 5))
    if DEBUGGING:
        Image.frombytes('RGB', chatBox.size, chatBox.bgra, 'raw', 'BGRX').save("debug/chatBox" + str(i) + ".png")

    # Use pytesseract to convert the image to text
    chatText = pytesseract.image_to_string(chatBox)
    if DEBUGGING:
        print(chatText, flush=True)
    # Check the text for any alerts
    for alert in ALERTS:
        if alert in chatText:
            alertWindow(win32gui.FindWindow(None, currentWindow), ALERTS[alert], alertPosition, windowSize, MAJOR_ALERT)
            return True

    return False

# Print that we're running
print("AFK Alerts has started!", flush=True)

# We want the user to input part of the name of the window they want to check
windowName = input("Hit enter to use default or enter the name of the window you want to check: ")

# If the user didn't input anything, print that we're exiting and exit
if windowName == "":
    print("No window name entered, assuming default.")
    windowName = DEFAULT_WINDOW_NAME

# Make an empty list to store the names of the windows and the time since they were last focused
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
# Loop through and print them all separately because the one long line is ugly and hard to read
for i in range(0, len(windowList)):
    print("Window " + str(i) + ": " + windowList[i], flush=True)

# If we didn't find any windows, exit
if len(windowList) == 0:
    print("No windows found, exiting.")
    exit()

# Initializing timing variables
timeElapsed = 0
startTime = time.time()
minutes = 0
iteration = 0

# The actual program loop
while True:
    # Get how much time has elapsed
    timeElapsed = time.time() - startTime
    # If it's been more than 60 seconds, print that we're still running
    if timeElapsed > TIME_BETWEEN_PRINTS:
        minutes += 1
        print("Running for " + str(minutes) + " minutes.", flush=True)
        startTime = time.time()

    # Iterate through all the found windows
    for i in range(0, len(windowList)):
        # Get the current window position and size
        currentWindow = windowList[i]
        window = win32gui.FindWindow(None, currentWindow)
        windowPos = win32gui.GetWindowRect(window)
        windowSize = (windowPos[2] - windowPos[0], windowPos[3] - windowPos[1])

        # Check if the window is focused
        if win32gui.GetForegroundWindow() == window:
            timeSinceLastFocused[i] = time.time()
        
        if DEBUGGING:
            print("Time since last focused for index " + str(i) + ": " + str(timeSinceLastFocused[i]), flush=True)

        # Put the alertPosition in the center of the window. In some cases it might be a little low, but this is nitpicking
        alertPosition = (windowPos[0], windowPos[1] + (windowSize[1] / 2))

        # If it's been more than ~4 mins since the window was focused, alert AFK. This value is in seconds
        if timeSinceLastFocused[i] - time.time() > 240:
            alertWindow(win32gui.FindWindow(None, currentWindow), "AFK", alertPosition, windowSize, MINOR_ALERT)
            continue
        
        if (iteration % ITERATIONS_BETWEEN_HPPRAY_CHECK) == 0:
            if checkHPPray(windowPos, currentWindow, i):
                continue

        iteration += 1
                
    if DEBUGGING:
        exit()

    time.sleep(SCAN_INTERVAL)