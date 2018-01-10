#!/usr/bin/env python

from flask import Flask, render_template, Response, redirect, request, session, url_for, jsonify
from flask_oauthlib.client import OAuth
from stream import Stream

import argparse
import os

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

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

if CLIENT_ID is None or CLIENT_SECRET is None:
    print("Exiting: Oauth client ID and secret is not set in the environment...")
    exit(0)

app = Flask(__name__)
app.debug = True
app.secret_key = 'development-secret-span-rocks'
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
    # Check the username is allowed.
    session['github_token'] = (resp['access_token'], '')
    me = github.get('user')
    return redirect(url_for('index'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def gen(video_stream):
    PROCESS_FRAME = 0
    # Loop over the frames from the video stream.
    while True:
        ok, frame = video_stream.read()
        if not ok:
            video_stream.stop()
            exit(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + byteArr + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_stream),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__server__':
    app.run(host='0.0.0.0', port=args["port"], debug=args["debug"], threaded=False)
