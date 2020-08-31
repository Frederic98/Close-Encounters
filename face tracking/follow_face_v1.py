import cv2
import sys
import logging as log
import datetime as dt
from time import sleep
import eyes
import threading

log.basicConfig(filename='webcam.log',level=log.INFO)



def detect_face():
    cascPath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascPath)

    video_capture = cv2.VideoCapture(0)
    anterior = 0

    while True:
        if not video_capture.isOpened():
            print('Unable to load camera.')
            sleep(5)
            continue

        # Capture frame-by-frame
        ret, frame = video_capture.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces):
            print('Face!')
            faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
            face = faces[0]
            fh,fw,_ = frame.shape
            x,y,w,h = face
            xc = x + w/2
            yc = y + h/2
            xn = (xc - fw/2) / (fw/2)
            yn = (yc - fh/2) / (fh/2)
            print(xn, yn)
            eye.watchDirection(xn, yn)
        else:
            print('No face!')


        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        if anterior != len(faces):
            anterior = len(faces)
            log.info("faces: "+str(len(faces))+" at "+str(dt.datetime.now()))

        video.show_image(frame)
        #
        #
        # # Display the resulting frame
        # cv2.imshow('Video', frame)
        #
        #
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        #
        # # Display the resulting frame
        # cv2.imshow('Video', frame)

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()


video = eyes.DisplayImageWidget()
video.show()
eye = eyes.Eyes()
eye.show()
face_thread = threading.Thread(target=detect_face, daemon=True)
face_thread.start()
eyes.app.exec()

