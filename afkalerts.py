from python_imagesearch.imagesearch import imagesearcharea
from python_imagesearch.imagesearch import imagesearch
from python_imagesearch.imagesearch import region_grabber
import tkinter as tk
import win32gui
import time

notificationIcon = "mellon.ico"

# This is the function that will always be called if an alert is detected. It's kinda janky.
def alertWindow(hwnd, alert, position=(0, 0)):    
    # Create a new window
    window = tk.Tk()
    window.title(alert)
    window.geometry("500x100")
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
    window.overrideredirect(True)

    window.lift()

    # Add a label to the window, size 20 with white text
    label = tk.Label(window, text=alert, font=("Arial Bold", 20), bg="blue", fg="white")
    label.pack()

    # If position is 0, 0, center the window
    if position == (0, 0):
        # Get the screen's size
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        # Calculate the window's position
        position = ((screen_width - window.winfo_width()) // 2, (screen_height - window.winfo_height()) // 2)

    # Set the window's position
    window.geometry("+%d+%d" % (position[0], position[1]))

    # Run the window loop for 5 seconds
    window.after(5000, window.destroy)
    window.mainloop()

# These are the images we're going to be using, could probably improve this later on
# Potential improvements: scan the /img/ folder and get all images and use a naming scheme to set them up
antiMacro = "img/antimacro.PNG"
lowHP = "img/lowhp.PNG"
lowPray = "img/lowprayer.PNG"
trivia = "img/trivia.PNG"

# Print that we're running
print("AFK Alerts is running...")

# We want the user to input part of the name of the window they want to check
windowName = input("Enter the name of the window you want to check: ")

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

# Scan every 1 second by default, but can be anything
SCAN_INTERVAL = 1

# If panic key is not pressed, loop every scan interval and check if the image is on screen
while True:
    # Print that we are scanning
    print("Scanning...")

    timeStarted = time.time()
    # We do everything here

    # Iterate through all the found windows
    for i in range(0, len(windowList)):
        # Get the current window's image
        currentWindow = windowList[i]
        # Print that we're scanning this window
        print("Scanning window: " + currentWindow)

        # Get window's position and size
        windowPos = win32gui.GetWindowRect(win32gui.FindWindow(None, currentWindow))

        # TODO actually figure out the region to scan
        # Generate the top right corner region of the window in a 200x200 box
        # This is where we will be scanning for the red pixels
        # cornerTuple = (windowPos[2] - 200, windowPos[1], windowPos[2], windowPos[1] + 200)
        # topRightCorner = region_grabber(cornerTuple)
        #lowHPPos = imagesearcharea(lowHP, 0.9, cornerTuple[0], cornerTuple[1], cornerTuple[2], cornerTuple[3], topRightCorner)
        #lowPrayPos = imagesearcharea(lowPray, 0.9, cornerTuple[0], cornerTuple[1], cornerTuple[2], cornerTuple[3], topRightCorner)

        # At 0.9 precision the low HP/prayer images are detected pretty consistently
        # Check if lowHP is on screen
        lowHPPos = imagesearch(lowHP, precision=0.9)
        if lowHPPos[0] != -1:
            alertWindow(win32gui.FindWindow(None, currentWindow), "Low HP")
            break
        
        # Check if lowPray is on screen
        lowPrayPos = imagesearch(lowPray, precision=0.9)
        if lowPrayPos[0] != -1:
            alertWindow(win32gui.FindWindow(None, currentWindow), "Low Prayer")
            break
        
        # Check if antiMacro is on screen
        antiMacroPos = imagesearch(antiMacro, precision=0.9)
        if antiMacroPos[0] != -1:
            alertWindow(win32gui.FindWindow(None, currentWindow), "Answer Anti-Macro")
            break

        continue # Continuing here because the trivia check is needs better handling than this
        # Check if trivia is on screen
        triviaPos = imagesearch(trivia, precision=0.9)
        if triviaPos[0] != -1:
            alertWindow(win32gui.FindWindow(None, currentWindow), "Answer Trivia")
            break

    # Print how long it took to scan; this includes the window live time though
    print("Scanned in " + str(time.time() - timeStarted) + " seconds.", flush=True)
    time.sleep(SCAN_INTERVAL)