#!/usr/bin/env python

import cv2
import face_recognition
import datetime
import time

# TODO load all SPAN faces here.
obama_image = face_recognition.load_image_file("./pics/obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

dom_image = face_recognition.load_image_file("./pics/dom.jpg")
dom_face_encoding = face_recognition.face_encodings(dom_image)[0]

# Load classifiers
face_cascade = cv2.CascadeClassifier('./lib/haarcascade_frontalface_default.xml')
video_stream = cv2.VideoCapture(0)
# Initialize the video stream and allow the cammera sensor to warmup.
video_stream.set(3, 1280)
video_stream.set(4, 720)
video_stream.set(cv2.CAP_PROP_FPS, 24)

class Stream:

    def __init__(self):
        pass

    def run(self, queue):
        PROCESS_FRAME = 1
        # Wait for the stream to start up.
        time.sleep(2.0)
        while True:
            frame = self.get_frame()

            # Convert to greyscale for the classifier.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            face_locations = list()
            
            # Convert to RGB for face_recognition.
            rgb_frame = frame[:, :, ::-1]

            for (x,y,w,h) in faces:
                # If a face is detected, try and determine who it is, but keep tracking the face.
                # Don't do anymore facial encodings.
                face_locations.append((y.item(), (x+w).item(), (y+h).item(), x.item()))

                # Draw an initial rectangle.
                #cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

                if PROCESS_FRAME % 3 == 0:
                    start = time.clock()
                    frame = self.process_frame(frame, rgb_frame, face_locations)
                    print(time.clock() - start)
                PROCESS_FRAME = PROCESS_FRAME % 24 + 1

            frame = self.jpeg_byte_array(self.affix_timestamp(frame))
            queue.put(frame)

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
        ok, frame = video_stream.read()
        if not ok:
            print("Error reading frame.")
            # TODO: try and recover.
            video_stream.release()
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
            #cv2.rectangle(frame, (top, right), (bottom, left), (255, 0, 0), 2)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return frame
