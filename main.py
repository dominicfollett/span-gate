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

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--picamera", type=int, default=-1,
	help="whether or not the Raspberry Pi camera should be used")
args = vars(ap.parse_args())
 
# initialize the video stream and allow the cammera sensor to warmup
vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
time.sleep(2.0)

app = Flask(__name__)
app.debug = True
app.secret_key = 'development-secret'
oauth = OAuth(app)

github = oauth.remote_app(
    'github',
    consumer_key='6761c48074347fb52a23',
    consumer_secret='bb9b033f40b9ff33cf217cf1741923cfd4905115',
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
    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # draw the timestamp on the frame
        timestamp = datetime.datetime.now()
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (0, 0, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', frame)
        byteArr = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + byteArr + b'\r\n\r\n')
#    while True:
#        frame = camera.get_frame()
#        yield (b'--frame\r\n'
#               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(vs),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # picamera will not work with debugging enabled.
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
