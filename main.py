#!/usr/bin/env python
#
# Project: Video Streaming with Flask
# Author: Log0 <im [dot] ckieric [at] gmail [dot] com>
# Date: 2014/12/21
# Website: http://www.chioka.in/
# Description:
# Modified to support streaming out with webcams, and not just raw JPEGs.
# Most of the code credits to Miguel Grinberg, except that I made a small tweak. Thanks!
# Credits: http://blog.miguelgrinberg.com/post/video-streaming-with-flask
#
# Usage:
# 1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
# 2. Run "python main.py".
# 3. Navigate the browser to the local webpage.
from flask import Flask, render_template, Response, redirect, request, session, url_for, jsonify
from flask_oauthlib.client import OAuth

#from camera import VideoCamera
from imutils.video import VideoStream
import datetime
import argparse
import imutils
import time
import cv2
import os
import face_recognition

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

if CLIENT_ID is None or CLIENT_SECRET is None:
    print("Exiting: Oauth client ID and secret is not set in the environment...")
    exit(0)

# TODO load all SPAN faces here.
# Load a sample picture and learn how to recognize it.
obama_image = face_recognition.load_image_file("./lib/obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

dom_image = face_recognition.load_image_file("./lib/dom.jpg")
dom_face_encoding = face_recognition.face_encodings(dom_image)[0]

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-pi", "--picamera", type=bool, default=False,
	help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-p", "--port", type=int, default=80,
	help="port to serve service over")
ap.add_argument("-d", "--debug", type=bool, default=False,
	help="Run service in debug mode.")
args = vars(ap.parse_args())

if args["debug"] and args["picamera"]:
    print("Picamera will not work with debugging enabled.")
    exit(0)

# Load classifiers
face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')

# initialize the video stream and allow the cammera sensor to warmup
vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
time.sleep(2.0)

app = Flask(__name__)
app.debug = True
app.secret_key = 'development-secret'
oauth = OAuth(app)

github = oauth.remote_app(
    'github',
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)

@app.route('/')
def index():
    if 'github_token' in session:
        me = github.get('user')
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.pop('github_token', None)
    return redirect(url_for('index'))

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason=%s error=%s resp=%s' % (
            request.args['error'],
            request.args['error_description'],
            resp
        )
    session['github_token'] = (resp['access_token'], '')
    me = github.get('user')
    return redirect(url_for('index'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def gen(vs):
    PROCESS_FRAME = True
    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        #frame = imutils.resize(frame, width=500)
        
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # TODO: detect the face first, and only then do recognition on that part?
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        #for (x,y,w,h) in faces:
        #    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
        #    # Send frame off for recognition.

        # Perhaps have each CPU process a frame - or a separate process doing the processing.
        # Or run flask server on one process, and image recongition on another process?
        if PROCESS_FRAME:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                match = face_recognition.compare_faces([obama_face_encoding, dom_face_encoding], face_encoding)
                name = "Unknown"

                if match[0]:
                    name = "Barack"
                if match[1]:
                    name = "Dom"

                face_names.append(name)

        PROCESS_FRAME = not PROCESS_FRAME

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # draw the timestamp on the frame
        timestamp = datetime.datetime.now()
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (0, 0, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', frame)
        byteArr = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + byteArr + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(vs),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args["port"], debug=args["debug"], threaded=True)
