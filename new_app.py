#imports packages
from flask import *
import sqlite3
import bcrypt
import time
from adafruit_motorkit import MotorKit
from flask_cors import CORS
import cv2
import numpy as np
from flask import Response

#creates new motor kit
kit = MotorKit(0x40)

 #creates flask app
app = Flask(__name__)
CORS(app)

#used for session
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Global variable for control
is_running = False

#gets database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#navigates to homepage
@app.route('/')
def index():  
    if 'username' in session:
        return render_template('index.html',firstname=session['username'])
    return render_template('login.html')

#navigates to login page
@app.route('/login', methods = ['GET', 'POST'])
def login():
    #checks user credentials
    if request.method == 'POST':
      conn = get_db_connection()
      user = conn.execute('SELECT * from user where username = ? ',
                          (str(request.form['username']),)).fetchone()
      conn.close()
      #checks password
      if bcrypt.checkpw(request.form["password"].encode("utf-8"),str(user["password"]).encode("utf-8")):
          session['username'] = user["first_name"]
          return redirect(url_for('index'))    
      else:
         print("User/ Password Error")

    return render_template('login.html')

#creates registration page
@app.route('/registration',methods=['GET', 'POST'])
def registration():
    #saves user information
    if request.method == 'POST':
        firstname=request.form["fname"]
        lastname=request.form["lname"]
        username=request.form["username"]
        #encrypts password
        salt = bcrypt.gensalt()
        password = (bcrypt.hashpw(request.form["password"].encode("utf-8"),salt).decode(encoding= "utf-8"))
        conn = get_db_connection()
        user = conn.execute('SELECT * from user where username = ? ',
                          (str(request.form['username']),)).fetchone()
        #checks if user is in the database
        if user is None:
             conn.execute('INSERT INTO user (username,password,first_name,last_name) VALUES (?, ?,?,?)',                          
                         (username,password, firstname, lastname ))
        else:
            print(f"User {username} already exist!")
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    else:
     return render_template('registration.html')

#logs out and redirects to login page
@app.route('/logout')
def logout():
    #removes the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))

#Routes for controlling the robot
@app.route('/start', methods = ['GET', 'POST'])
def start():
  global is_running, kit, webcam
  #starts robot and let the robot to move following a lane with webcam
  return jsonify("start")

 #Move the robor right    
@app.route('/right', methods = ['GET', 'POST'])
def right():
  #moves robot right
  kit.motor1.throttle = -0.72
  kit.motor2.throttle = 0.72
  #runs both motors for 0.3 seconds
  time.sleep(0.3)
  return jsonify("right")

 #Move the robot forward
@app.route('/forward', methods = ['GET', 'POST'])
def forward():
  #moves robot forward
  kit.motor1.throttle = 0.732
  kit.motor2.throttle = 0.7
  #runs both motors for 0.3 seconds
  time.sleep(0.3)
  return jsonify("forward")

@app.route('/backward', methods = ['GET', 'POST'])
#Move the robot backward
def backward():
  #moves robot backwards
  kit.motor1.throttle = -0.81
  kit.motor2.throttle = -0.7
  #runs both motors for 0.3 seconds
  time.sleep(0.3)
  return jsonify("backward")

@app.route('/left', methods = ['GET', 'POST'])
#Move the robot left
def left():
  #moves robot left
  kit.motor1.throttle = 0.72
  kit.motor2.throttle = -0.75
  #runs both motors for 0.3 seconds
  time.sleep(0.3)
  return jsonify("left")

#Stop the robot
@app.route('/stop', methods = ['GET', 'POST'])
def stop():
  global is_running,webcam
  is_running = False
  #stops both motors
  kit.motor1.throttle = 0
  kit.motor2.throttle = 0
  # Release the webcam 
  webcam.release()
  return jsonify("stop")

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#Allows app to run
if __name__ == '__main__':
    app.run(host='192.168.1.20', port=4444)