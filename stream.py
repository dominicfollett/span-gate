#!/usr/bin/env python

import cv2
import face_recognition
import time
import datetime

# TODO load all SPAN faces here.
obama_image = face_recognition.load_image_file("./pics/obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

dom_image = face_recognition.load_image_file("./pics/dom.jpg")
dom_face_encoding = face_recognition.face_encodings(dom_image)[0]

class Stream:
    
    def __init__(self, resolution=(640, 480), framerate=50):
        # Load classifiers
        self.face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')

        # Initialize the video stream and allow the cammera sensor to warmup.
        self.video_stream = cv2.VideoCapture(0)
        self.video_stream.set(3, resolution[0])
        self.video_stream.set(4, resolution[1])
        self.video_stream.set(cv2.CAP_PROP_FPS, framerate)
        time.sleep(2.0)

    def run(self):
        PROCESS_FRAME = True
        while True:
            frame = self.get_frame()

            # Convert to greyscale for the classifier.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            face_locations = list()
            
            # Convert to RGB for face_recognition.
            rgb_frame = frame[:, :, ::-1]

            for (x,y,w,h) in faces:
                # If a face is detected, try and determine who it is, but keep tracking the face.
                # Don't do anymore facial encodings.
                face_locations.append((x.item(), y.item(), (x+w).item(), (y+h).item()))
                # Draw an initial rectangle.
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

                frame = self.process_frame(frame, rgb_frame, face_locations) if PROCESS_FRAME else frame
                PROCESS_FRAME = not PROCESS_FRAME

            frame = self.jpeg_byte_array(self.affix_timestamp(frame))

    def jpeg_byte_array(self, frame):
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def affix_timestamp(self, frame):
        # draw the timestamp on the frame
        timestamp = datetime.datetime.now()
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (0, 0, 255), 1)
        return frame

    def get_frame(self):
        ok, frame = self.video_stream.read()
        if not ok:
            print("Error reading frame.")
            # TODO: try and recover.
            self.video_stream.release()
            exit(0)
        return frame

    def process_frame(self, frame, rgb_frame, face_locations):
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
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
        return self.display(face_locations, face_names, frame)

    def display(self, face_locations, face_names, frame):
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return frame
