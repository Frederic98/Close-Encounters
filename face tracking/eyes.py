import threading
import time

from PyQt5.QtCore import Qt, QPointF, QPropertyAnimation, QPointF, pyqtSignal

from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QImage, QPixmap, QCloseEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
import numpy as np

app = QApplication([])


class Eyes(QWidget):
    onClose = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.eyes = [Eye() for _ in range(2)]
        for eye in self.eyes:
            self.main_layout.addWidget(eye)

        self.setFixedSize(1000, 500)

    def watchDirection(self, x, y):
        for eye in self.eyes:
            eye.watchDirection(x,y)

    def closeEvent(self, evnt: QCloseEvent) -> None:
        self.onClose.emit()
        evnt.accept()


class Eye(QWidget):
    PupilMoveSignal = pyqtSignal(object)

    def __init__(self):
        QWidget.__init__(self)

        self.color_edge = QColor(0x000000)
        self.color_body = QColor(0xffffff)
        self.edge_size = 0.02
        self.pupil_size = 0.4
        pupil_size = min(self.width(), self.height()) * self.pupil_size
        self.pupil = Pupil(QColor(0x00aa00), parent=self)
        self.pupil.setFixedSize(pupil_size, pupil_size)
        self.pupil.move(self.width()/2, self.height()/2)

    def resizeEvent(self, event):
        pupil_size = min(self.width(), self.height()) * self.pupil_size
        self.pupil.setFixedSize(pupil_size, pupil_size)
        self.update()
        self.pupil.move(self.width()/2 - self.pupil.width()/2, self.height()/2 - self.pupil.height()/2)

    def paintEvent(self, event):
        size = min(self.width(), self.height())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)

        painter.setBrush(QBrush(self.color_edge))
        painter.drawEllipse(QPointF(0, 0), size/2, size/2)

        painter.setBrush(QBrush(self.color_body))
        body_size = size*(1-self.edge_size)*0.5
        painter.drawEllipse(QPointF(0,0), body_size, body_size)

    def radius(self):
        return min(self.width(), self.height()) / 2

    def body_radius(self):
        return min(self.width(), self.height()) / 2 * (1-self.edge_size)

    @staticmethod
    def cart2pol(x, y):
        # https://stackoverflow.com/a/26757297/8181134
        mag = np.sqrt(x ** 2 + y ** 2)
        angle = np.arctan2(y, x)
        return (mag, angle)

    @staticmethod
    def pol2cart(mag, angle):
        # https://stackoverflow.com/a/26757297/8181134
        x = mag * np.cos(angle)
        y = mag * np.sin(angle)
        return (x, y)

    def watchDirection(self, horizontal, vertical):
        """ Move the eyes to the specified direction
        :param horizontal: float [-1 1]
        :param vertical: float [-1 1]
        """
        mag, angle = self.cart2pol(horizontal, vertical)
        mag = np.clip(mag, 0, 1)                            # Limit the magnitude to max 1
        mag *= (self.body_radius() - self.pupil.radius())   # Max value for mag is so the edge of pupil hits edge of eye
        x, y = self.pol2cart(mag, angle)
        x += self.width() / 2                               # Position pupil around center of eye
        y += self.height() / 2                              # ...
        self.PupilMoveSignal.emit((x,y))                    # Use QtSignal to allow update outside of UI thread


class Pupil(QWidget):
    def __init__(self, color, parent, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)

        self.color_iris = color
        self.color_pupil = QColor(0x000000)
        self.iris_size = 0.6
        parent.PupilMoveSignal.connect(lambda p: self.move(*p))

    def radius(self):
        return min(self.width(), self.height()) / 2

    def move(self, x, y):
        """ Move the pupil to a specified position
        :param x: Vertical position of center of the pupil
        :param y: Horizontal position of center of the pupil
        """
        x -= self.width()/2         # Get position of top-right corner
        y -= self.height()/2        # ...
        self.pos_anim = QPropertyAnimation(self, b'pos')    # Animation for position
        self.pos_anim.setDuration(100)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPointF(x, y))
        self.pos_anim.start()
        # QWidget.move(self, x, y)

    def resizeEvent(self, event):
        self.update()

    def paintEvent(self, event):
        size = min(self.width(), self.height())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)

        painter.setBrush(QBrush(self.color_iris))
        painter.drawEllipse(QPointF(0, 0), size/2, size/2)

        painter.setBrush(QBrush(self.color_pupil))
        iris_size = size*(1-self.iris_size)*0.5
        painter.drawEllipse(QPointF(0,0), iris_size, iris_size)


class DisplayImageWidget(QWidget):
    def __init__(self, parent=None):
        super(DisplayImageWidget, self).__init__(parent)
        self.image_frame = QLabel()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_frame)
        self.setLayout(self.layout)

    def show_image(self, image: np.ndarray):
        image = image.copy()
        if image.base is not None:      # This doesn't work with a numpy `view` of an array
            image = image.copy()        # So make a copy of the data if it is a view
        image = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888).rgbSwapped()
        self.image_frame.setPixmap(QPixmap.fromImage(image))


if __name__ == "__main__":
    def move_pupil():
        while True:
            x, y = (np.random.rand() * 2 - 1 for _ in range(2))
            for eye in eyes:
                eye.watchDirection(x, y)
            # main_widget.watchDirection(x,y)
            # main_widget.watchDirection(1,1)
            time.sleep(2)

    main_widget = QWidget()
    main_layout = QHBoxLayout(main_widget)
    eyes = [Eye() for _ in range(2)]
    for eye in eyes:
        main_layout.addWidget(eye)

    main_widget.setFixedSize(1000,500)
    t = threading.Thread(target=move_pupil, daemon=True)
    # main_widget = Eye()
    main_widget.show()
    # main_widget.
    t.start()
    app.exec()

