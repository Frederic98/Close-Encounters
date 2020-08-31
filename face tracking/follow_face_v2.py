from typing import List
import face_recognition
import cv2
import eyes
import threading

### Install
# OpenCV: pip install opencv-python
# face_recognition: https://github.com/ageitgey/face_recognition
# PyQt5: pip install PyQt5
# NumPy: pip install numpy


video_capture = cv2.VideoCapture(0)
shrink_factor = 2


class FaceLocation:
    def __new__(cls, location):
        self = object.__new__(cls)
        self.top, self.right, self.bottom, self.left = location
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.area = self.width * self.height
        return self

    # Make class backward compatible with list of top-right-bottom-left locations
    def __getitem__(self, index):
        return (self.top, self.right, self.bottom, self.left)[index]

    @classmethod
    def sort(cls, faces: List["FaceLocation"]) -> List["FaceLocation"]:
        """Sorts list of faces by descending pixel area"""
        return sorted(faces, key=lambda fl: fl.area, reverse=True)

    def __mul__(self, factor):
        return FaceLocation([self.top * factor,
                             self.right * factor,
                             self.bottom * factor,
                             self.left * factor])

    def __truediv__(self, factor):
        return FaceLocation([self.top // factor,
                             self.right // factor,
                             self.bottom // factor,
                             self.left // factor])

    def __floordiv__(self, factor):
        return self.__truediv__(factor)


def detect_face():
    known_faces = []
    face_names = []

    i = 0
    while True:
        i += 1
        # Grab a single frame of video
        ret, frame = video_capture.read()
        frame = cv2.flip(frame, 1)

        # Resize frame of video for faster face detection processing
        small_frame = cv2.resize(frame, (0, 0), fx=1/shrink_factor, fy=1/shrink_factor)

        # Find all the faces and face encodings in the current frame of video
        face_locations = [FaceLocation(loc) for loc in face_recognition.face_locations(small_frame)]

        if len(face_locations) > 0:
            # print('Face!')
            face = FaceLocation.sort(face_locations)[0]
            face *= shrink_factor
            fh, fw, _ = frame.shape             # rows, columns, color

            xc = face.left + face.width/2       # X center of face
            yc = face.top + face.height/2       # Y center of face
            xn = (xc - fw/2) / (fw/2)           # Normalised face location in frame
            yn = (yc - fh/2) / (fh/2)           # [-1 ... 1]
            eye.watchDirection(xn, yn)

            face_image = frame[face.top:face.bottom, face.left:face.right, :].copy()
            cv2.imwrite('tmp/{}.png'.format(i), face_image)
            # video.show_image(face_image)

            for face in face_locations:
                face *= shrink_factor
                face_image = frame[face.top:face.bottom, face.left:face.right].copy()
                cv2.rectangle(frame, (face.left, face.top), (face.right, face.bottom), (0,255,0), 2)
                try:
                    encoding = face_recognition.face_encodings(face_image)[0]
                    matches = face_recognition.compare_faces(known_faces, encoding)
                    if any(matches):
                        name = face_names[matches.index(True)]
                        print('Found face {} - {}'.format(name, i))
                    else:
                        name = str(len(known_faces))
                        print('New face: ' + name + ' - ' + str(i))
                        face_names.append(name)
                        known_faces.append(encoding)
                    cv2.rectangle(frame, (face.left, face.bottom), (face.right, face.bottom + 35), (0, 255, 0), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, 'face ' + name, (face.left + 6, face.bottom - 6 + 35), font, 1.0, (255, 255, 255), 1)
                except IndexError:
                    pass

        else:
            # print('No face!')
            pass
        video.show_image(frame)

    video_capture.release()
    cv2.destroyAllWindows()


video = eyes.DisplayImageWidget()
video.show()
eye = eyes.Eyes()
eye.show()
eye.onClose.connect(video.close)
face_thread = threading.Thread(target=detect_face, daemon=True)
face_thread.start()
eyes.app.exec()
