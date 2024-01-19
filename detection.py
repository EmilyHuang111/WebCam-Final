# Importing the 'cv2' module for computer vision tasks.
import cv2 as cv
# Importing the 'numpy' module for numerical operations and array handling.
import numpy as np
# Importing the 'tkinter' module for creating GUI applications.
import tkinter as tk
# Importing the PIL library for image processing.
from PIL import Image, ImageTk
# Importing the 'datetime' module for working with dates and times.
from datetime import datetime
# Importing the 'logging' module for generating log messages.
import logging
# Importing the 'pytz' module for working with time zones.
import pytz
# Importing the 'threading' module for creating and managing threads.
import threading


# Root Menu for user registration and login
root = tk.Tk()
root.title("User Login")

# Set up logging with US/Eastern timezone
eastern = pytz.timezone('US/Eastern')

# Update the lable for log file
def update_label(image, label): #Function to update the label with the image
    photo = ImageTk.PhotoImage(image=image) #Convert the image to a PhotoImage object
    label.config(image=photo) #Update the label with the new image
    label.image = photo  # Keep a reference to the image to prevent garbage collection

#Create a log file to track activities
# Set up logging
logging.basicConfig(
    filename='activity_log.txt',
    level=logging.INFO,
    format='%(message)s',
)

# Function for the log information including date and time and message
def log_activity(message):
  current_time = datetime.now(eastern).strftime('%Y-%m-%d %I:%M:%S %p') #Get the current date and time in US/Eastern timezone
  logging.info(f"{current_time} - {message}") #Log the message with the current date and time

#Set up global variables for video streaming control
stop_video_raw = threading.Event() 
stop_video_processed = threading.Event() 


webcam = cv.VideoCapture("http://192.168.1.28:4444/video_feed") #Connect to the webcam
webcam_lock = threading.Lock() #Lock for controlling access to the webcam

def getCanny(frame): #Function to get the canny image from the webcam

    gray = cv.cvtColor(frame, cv.COLOR_RGB2GRAY) #Convert the frame to grayscale

    blur = cv.GaussianBlur(gray, (5, 5), 0) #Apply Gaussian blur to the grayscale image

    canny = cv.Canny(blur, 50, 150) #Apply Canny edge detection to the blurred image
    return canny #Return the canny image

def getSegment(frame): #Function to get the segmented image from the webcam
    height = frame.shape[0] #Get the height of the frame

    polygons = np.array([
                            [(0, height), (800, height), (380, 290)]
                        ]) #Define the polygon coordinates

    mask = np.zeros_like(frame) #Create a mask of zeros with the same shape as the frame

    cv.fillPoly(mask, polygons, 255) #Fill the mask with the polygon coordinates

    segment = cv.bitwise_and(frame, mask) #Apply the mask to the frame to get the segmented image
    return segment #Return the segmented image

def generateLines(frame, lines): #Function to generate the lines on the frame
    left = [] #List to store the left line coordinates
    right = [] #List to store the right line coordinates
    if lines is not None: #Check if lines are detected
        for line in lines: #Loop through each line
            x1, y1, x2, y2 = line.reshape(4) #Get the coordinates of the line
            parameters = np.polyfit((x1, x2), (y1, y2), 1) #Fit a line to the coordinates
            slope = parameters[0] #Get the slope of the line
            y_intercept = parameters[1] #Get the y-intercept of the line
            if slope < 0: #Check if the slope is negative
                left.append((slope, y_intercept)) #Append the slope and y-intercept to the left line list
            else:
                right.append((slope, y_intercept)) #Add the slope and y-intercept to the appropriate list

    if left and right:  #Check if both left and right lines are detected
        left_avg = np.average(left, axis=0) #Get the average of the left lines
        right_avg = np.average(right, axis=0) #Get the average of the right lines
        left_line = generateCoordinates(frame, left_avg) #Generate the left line coordinates
        right_line = generateCoordinates(frame, right_avg) #Generate the right line coordinates
        return np.array([left_line, right_line]) #Return the lines as a numpy array
    return None

def generateCoordinates(frame, parameters): #Function to generate the coordinates of the lines
    slope, intercept = parameters #Get the slope and y-intercept of the line

    y1 = frame.shape[0] #Get the height of the frame

    y2 = int(y1 - 150) #Get the y-coordinate of the bottom of the frame

    x1 = int((y1 - intercept) / slope) #Get the x-coordinate of the left edge of the frame

    x2 = int((y2 - intercept) / slope) #Get the x-coordinate of the right edge of the frame
    return np.array([x1, y1, x2, y2]) #Return the coordinates as a numpy array

# Function to visualize the lines on the frame, including the centerline
def showLines(frame, lines): #
    lines_visualize = np.zeros_like(frame) #Create a copy of the frame with zeros

    if lines is not None: #Check if lines are detected
        for x1, y1, x2, y2 in lines: #Loop through each line
            cv.line(lines_visualize, (x1, y1), (x2, y2), (0, 255, 0), 5)  # Draw lane lines in green

        # Calculate and draw the centerline
        left_line, right_line = lines
        center_line = (left_line + right_line) // 2
        x1, y1, x2, y2 = center_line
        cv.line(lines_visualize, (x1, y1), (x2, y2), (0, 0, 255), 5)  # Draw centerline in red

    return lines_visualize

def load_video_raw(currentState, userName, frame, stop_event): #Function to load the raw video stream
    global webcam, webcam_lock #Declare the global variables
    currentState.config(text="Current State: Camera loaded") #Update the current state label
    log_activity(f"{userName} clicked load camera button.") #Log the activity
    video_label2 = tk.Label(frame) #Create a label for the video stream
    video_label2.grid(row=2, column=0, columnspan=2) #Grid the label in the frame

    if not webcam.isOpened(): #Check if the webcam is not opened
        currentState.config(text="Current State: No Connection") #Update the current state label
    else:
        while not stop_event.is_set(): #Loop until the stop event is set
            with webcam_lock: #Lock the webcam
               ret, frame = webcam.read() #Read the frame from the webcam
            if ret: #Check if the frame is read successfully
                rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB) #Convert the frame to RGB format
                rgb_frame = cv.resize(rgb_frame, (256, 256)) #Resize the frame to 256x256
                image = Image.fromarray(rgb_frame) #Convert the frame to an image
                photo = ImageTk.PhotoImage(image=image) #Convert the image to a PhotoImage object
                video_label2.config(image=photo) #Update the label with the new image
                video_label2.image = photo  # Keep a reference to the image to prevent garbage collection
                root.after(0, update_label, Image.fromarray(rgb_frame), video_label2) #Update the label with the new image


def load_video_processed(currentState, userName, frame, stop_event): #Function to load the processed video stream
    global webcam, webcam_lock #Declare the global variables
    currentState.config(text="Current State: Overlay Loaded") #Update the current state label
    log_activity(f"{userName} clicked load overlay button.") #Log the activity
    video_label1 = tk.Label(frame) #Create a label for the video stream
    video_label1.grid(row=2, column=0, columnspan=2) #Grid the label in the frame

    if not webcam or not webcam.isOpened(): #Check if the webcam is not opened
        currentState.config(text="Current State: No Connection") #Update the current state label
        return
    else:
        while not stop_event.is_set(): #Loop until the stop event is set
            with webcam_lock: #Lock the webcam
                ret, frame = webcam.read() #Read the frame from the webcam
            if ret:
                canny = getCanny(frame) #Get the canny image from the webcam
                segment = getSegment(canny) #Get the segmented image from the webcam
                hough = cv.HoughLinesP(segment, 2, np.pi / 180, 100, np.array([]), minLineLength=100, maxLineGap=50) #Get the lines from the segmented image
                lines = generateLines(frame, hough) #Generate the lines on the frame
                if lines is not None and lines.all(): #Check if lines are detected
                    processed_frame = showLines(frame, lines) #Show the lines on the frame
                else:
                    processed_frame = frame #Keep the original frame
                rgb_frame = cv.cvtColor(processed_frame, cv.COLOR_BGR2RGB) #Convert the frame to RGB format
                rgb_frame = cv.resize(rgb_frame, (256, 256)) #Resize the frame to 256x256
                image = Image.fromarray(rgb_frame) #Convert the frame to an image
                photo = ImageTk.PhotoImage(image=image) #Convert the image to a PhotoImage object
                video_label1.config(image=photo) #Update the label with the new image
                video_label1.image = photo  
                root.after(0, update_label, Image.fromarray(rgb_frame), video_label1)