#!/usr/bin/python

# Import the required modules
import cv2, os
import numpy as np
import time
import argparse
import time
import yaml

# Construct the argument parser and parse the arguments.
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", type=str, default=None,
	help="Unique name of 'class' belonging to images.")
ap.add_argument("-c", "--count", type=int, default=100,
	help="umber of training examples to take.")
args = vars(ap.parse_args())

names = None
try:
    names = yaml.load(open("./lib/names.yaml", 'r'))
except yaml.YAMLError as e:
    print(e)
    exit(0)

if args["name"] is None:
    print("No name supplied.")
    exit(0)

# Load classifiers
face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')

# Initialize the video stream and allow the cammera sensor to warmup.
video_stream = cv2.VideoCapture(0)
video_stream.set(3, 640)
video_stream.set(4, 480)
video_stream.set(cv2.CAP_PROP_FPS, 90)
time.sleep(2.0)

# For face recognition we will the the LBPH Face Recognizer.
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Load previous models.
try:
    recognizer.read('./lib/models.yaml')
except cv2.error as e:
    print(e)

def get_frame():
    ok, frame = video_stream.read()
    if not ok:
        print("Error reading frame.")
        # TODO: try and recover.
        video_stream.release()
        exit(0)
    return frame

def get_exemplars(name, exemplar_count):
    print("Begining training.")
    exemplar = 0
    images = []
    # labels will contains the label that is assigned to the image
    labels = []
    label = names[name]
    while exemplar < exemplar_count:
        print("Processed %i exemplars" % exemplar)
        frame = get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Image labels must be unique.
        faces = face_cascade.detectMultiScale(gray)
        # If face is detected, append the face to images and the label to labels
        # There should only exist 1 face during training.
        # TODO Take the largest if there more than 1 face.
        if len(faces) == 1:
            for (x, y, w, h) in faces:
                images.append(gray[y: y + h, x: x + w])
                labels.append(label)
                cv2.imshow("Adding faces to traning set...", gray[y: y + h, x: x + w])
                exemplar += 1
                cv2.waitKey(50)
    cv2.destroyAllWindows()
    # return the images list and labels list
    return images, labels

images, labels = get_exemplars(args["name"], args["count"])

# Perform the tranining
recognizer.train(images, np.array(labels))

# Save the models.
recognizer.write('./lib/models.yaml')
