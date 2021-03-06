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
from pathlib import Path
from subprocess import call


OPENFACE_PATH = '~/openface'

class Capture:

    def __init__(self):
        # Load facial classifier.
        self.face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')
        # Initialize the video stream and allow the cammera sensor to warmup.
        self.video_stream = cv2.VideoCapture(0)
        self.video_stream.set(3, 640)
        self.video_stream.set(4, 480)
        self.video_stream.set(cv2.CAP_PROP_FPS, 90)
        time.sleep(2.0)

    def get_frame(self):
        ok, frame = self.video_stream.read()
        return frame if ok else handle_err("Error reading frame.")

    def process(self, count, name):
        # Get unique name mappings - which are used as machine-learning labels.
        label = None
        exemplar = 0

        try:
            label = yaml.load(open("./lib/ids.yaml", 'r'))[name]
        except KeyError as e:
            handle_err("Name does not exist.")
        except yaml.YAMLError as e:
            handle_err(e)

        while exemplar < count:
            print("Processed {} exemplar(s)".format(exemplar + 1))
            
            frame = self.get_frame()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray)
            
            # If a face is detected, append the face to images and the label to
            # labels. There should only exist 1 face during training. If there is
            # more than one, take the largest frame (TODO).
            if len(faces) is 1:
                for (x, y, w, h) in faces:
                    image = gray[y: y + h, x: x + w]
                    Path("./lib/images/{}".format(name)).mkdir(parents=True, exist_ok=True)
                    cv2.imwrite("./lib/images/{}/{}_{}.png".format(name, exemplar, label), image)
                    #np.save("./lib/images/{}/{}_{}.npy".format(name,
                    #    exemplar, label), image)
                    # Uncomment to watch facial capture.
                    cv2.imshow("Adding faces to traning set...", gray[y: y + h, x: x + w])
                    cv2.waitKey(50)
                    exemplar += 1
        cv2.destroyAllWindows()

    def handle_err(self, err):
        if self.video_stream is not None:
            self.video_stream.release()
        print(err)
        exit(0)

# Parse the arguments.
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
capture_parser = subparsers.add_parser('capture', help="Take training data from camera.")
train_parser = subparsers.add_parser('train', help="Retrain model with what is captured in ./lib/images")
capture_parser.set_defaults(cmd='capture')
train_parser.set_defaults(cmd='train')

capture_parser.add_argument("-n", "--name", type=str, required=True,
	help="Unique name of 'class' belonging to images.")
capture_parser.add_argument("-c", "--count", type=int, default=100,
	help="Number of training examples to take.")
train_parser.add_argument('-a', '--algorithm', type=str, required=True,
    help="LBPH or OpenFace (deep learning).")
args = parser.parse_args()

DIR = './lib/images/'
if args.cmd == 'capture':
    # Using the camera save images to file.
    Capture().process(args.count, args.name)
    print("Image capture completed.")
elif args.cmd == 'train':
    if args.algorithm == 'LBPH':
        labels = []
        images = []
        # Load all images and labels.
        for f in os.listdir(DIR):
            file = os.path.join(DIR,f)
            if os.path.isfile(file):
                images.append(np.load(os.path.join(DIR,f)))
                labels.append(int(f.strip(".npy").split("_")[3]))
        # Create the LBPH Face Recognizer.
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        # Perform the tranining.
        recognizer.train(images, np.array(labels))
        # Save the training data.
        recognizer.save('./lib/model.yaml')
        print("Training model completed.")
    if args.algorithm == 'OpenFace':
        # Perform pose detection and alignment
        home = str(Path.home())
        call(["python3", "{}/openface/util/align-dlib.py".format(home), "./lib/images", "align", "outerEyesAndNose", "./lib/aligned-images", "--size", "96"])
        call(["{}/openface/batch-represent/main.lua".format(home), "-outDir", "./lib/generated-embeddings", "-data", "./lib/aligned-images"])
        call(["python3", "./classifier.py", "--dlibFacePredictor", "{}/openface/models/dlib/shape_predictor_68_face_landmarks.dat".format(home), "train", "./lib/generated-embeddings"])
