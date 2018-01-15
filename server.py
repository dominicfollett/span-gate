#!/usr/bin/env python

from flask import Flask, render_template, Response, redirect, request, session, url_for, jsonify
from flask_oauthlib.client import OAuth
import os

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

def run(queue, port=80, debug=False):
    app.queue = queue
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=False)

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
    user = github.get('user')
    print(dir(user))
    session['github_token'] = (resp['access_token'], '')
    return redirect(url_for('index'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def gen():
    PROCESS_FRAME = 0
    # Loop over the frames from the video stream.
    while True:
        frame = app.queue.get()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
