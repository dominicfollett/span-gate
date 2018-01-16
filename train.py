#!/usr/bin/python

# 'train' uses the LBPH face recongizer, it loads existing models and improves
# them with more exemplars and saves it to ./lib/models.yaml. When training,
# try and keep the count low: minimum of 10, maximum of 100.

import cv2, os
import numpy as np
import time
import argparse
import time
import yaml

# Parse the arguments.
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", type=str, default=None,
	help="Unique name of 'class' belonging to images.")
ap.add_argument("-c", "--count", type=int, default=100,
	help="Number of training examples to take.")
args = vars(ap.parse_args())

# A name for training must be supplied.
if args["name"] is None:
    print("No name supplied.")
    exit(0)

# Get unique name mappings - which are used as machine learning labels.
names = None
try:
    names = yaml.load(open("./lib/names.yaml", 'r'))
except yaml.YAMLError as e:
    print(e)
    exit(0)

# Load facial classifier.
face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')

# Initialize the video stream and allow the cammera sensor to warmup.
video_stream = cv2.VideoCapture(0)
video_stream.set(3, 640)
video_stream.set(4, 480)
video_stream.set(cv2.CAP_PROP_FPS, 90)
time.sleep(2.0)

# Create the LBPH Face Recognizer.
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Load previous models.
try:
    recognizer.read('./lib/models.yaml')
except cv2.error as e:
    # Just warn us if the model is empty.
    print(e)

# Using the camera get training faces.
images, labels = get_exemplars(names[args["name"]], args["count"])

# Perform the tranining.
recognizer.train(images, np.array(labels))

# Save the training data.
recognizer.save()

# Save the models.
recognizer.write('./lib/models.yaml')

def get_frame():
    ok, frame = video_stream.read()
    if not ok:
        print("Error reading frame.")
        # TODO: try and recover.
        video_stream.release()
        exit(0)
    return frame

def get_exemplars(label, count):

    exemplar = 0
    images = []
    labels = [ label for i in count ]

    while exemplar < count:
        print("Processed %i exemplars" % exemplar)
        
        frame = get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray)
        
        # If a face is detected, append the face to images and the label to
        # labels. There should only exist 1 face during training. If there is
        # more than one, take the largest frame (TODO).
        if len(faces) is 1:
            for (x, y, w, h) in faces:
                images.append(gray[y: y + h, x: x + w])
                # Uncomment to watch facial capture.
                # cv2.imshow("Adding faces to traning set...", gray[y: y + h, x: x + w])
                #cv2.waitKey(50)
                exemplar += 1
    cv2.destroyAllWindows()
    return images, labels