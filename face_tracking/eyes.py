import threading
import time
import numpy as np

from PyQt5.QtCore import Qt, QPropertyAnimation, QPointF, pyqtSignal, pyqtProperty, QTimer
from PyQt5.QtGui import QColor, QPainter, QBrush, QImage, QPixmap, QCloseEvent, QKeyEvent, QResizeEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel


class Eyes(QWidget):
    onClose = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.eyes = [Eye() for _ in range(2)]
        for eye in self.eyes:
            self.main_layout.addWidget(eye)
        self.grabKeyboard()

    def set_watch_direction(self, x, y):
        for eye in self.eyes:
            eye.set_watch_direction(x,y)
        # self.eyes[0].set_watch_direction(x,y)
        # self.eyes[1].set_watch_direction(-1*x,y)

    def set_pupil_size(self, size: float):
        for eye in self.eyes:
            eye.set_pupil_size(size)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.onClose.emit()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()
        else:
            super().keyPressEvent(event)


class Eye(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.body_color = QColor(0xffffff)
        self.border_color = QColor(0x000000)
        self.border_size = 0.02

        self.iris_size = 0.4
        self.watch_direction = (0.0, 0.0)

        self.iris = Iris(QColor(0x00aa00), parent=self)
        self.iris_move_anim = QPropertyAnimation(self.iris, b'pos')         # Animation for iris position
        self.iris_move_anim.setDuration(100)
        self.iris_size_anim = QPropertyAnimation(self.iris, b'pupil_size')  # Animation for pupil size
        self.iris_size_anim.setDuration(500)
        self.resize_iris()

    def resize_iris(self):
        pupil_size = int(min(self.width(), self.height()) * self.iris_size)
        self.iris.setFixedSize(pupil_size, pupil_size)
        self.set_watch_direction(*self.watch_direction, animate=False)

    def resizeEvent(self, event: QResizeEvent):
        self.resize_iris()

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)

        # draw border around eye
        painter.setBrush(QBrush(self.border_color))
        painter.drawEllipse(QPointF(0, 0), size/2, size/2)

        # draw sclera (white part of eyes)
        painter.setBrush(QBrush(self.body_color))
        body_size = size * (1 - self.border_size) * 0.5
        painter.drawEllipse(QPointF(0,0), body_size, body_size)

    @property
    def radius(self):
        return min(self.width(), self.height()) / 2

    @property
    def body_radius(self):
        return self.radius * (1 - self.border_size)

    @staticmethod
    def cart2pol(x, y):
        """Convert cartesian coordinate to polar"""
        # https://stackoverflow.com/a/26757297/8181134
        mag = np.sqrt(x ** 2 + y ** 2)
        angle = np.arctan2(y, x)
        return (mag, angle)

    @staticmethod
    def pol2cart(mag, angle):
        """Convert polar coordinate to cartesian"""
        # https://stackoverflow.com/a/26757297/8181134
        x = mag * np.cos(angle)
        y = mag * np.sin(angle)
        return (x, y)

    def set_watch_direction(self, horizontal, vertical, animate=True):
        """ Move the eyes to the specified direction
        :param horizontal: float [-1 1]
        :param vertical: float [-1 1]
        """
        self.watch_direction = (horizontal, vertical)
        mag, angle = self.cart2pol(horizontal, vertical)
        mag = np.clip(mag, 0, 1)                            # Limit the magnitude to max 1
        mag *= (self.body_radius - self.iris.radius)   # Max value for mag is so the edge of iris hits edge of eye
        x, y = self.pol2cart(mag, angle)

        x += (self.width() / 2) - self.iris.radius         # Position of top-left corner of iris
        y += (self.height() / 2) - self.iris.radius

        if self.iris_move_anim.state() != QPropertyAnimation.Stopped:
            self.iris_move_anim.stop()
        if animate:
            self.iris_move_anim.setStartValue(self.iris.pos())
            self.iris_move_anim.setEndValue(QPointF(x, y))
            QTimer.singleShot(0, self.iris_move_anim.start)
        else:
            QTimer.singleShot(0, lambda x=x, y=y: self.iris.move(x, y))

    def set_pupil_size(self, size: float):
        """Set the pupil size
        :arg size: Size of the pupil [0..1]
        """
        self.iris_size_anim.stop()
        self.iris_size_anim.setStartValue(self.iris.pupil_size)
        self.iris_size_anim.setEndValue(size)
        QTimer.singleShot(0, self.iris_size_anim.start)


class Iris(QWidget):
    def __init__(self, color, size=0.6, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.color_iris = color
        self.color_pupil = QColor(0x000000)
        self._pupil_size = size

    @property
    def radius(self):
        return min(self.width(), self.height()) / 2

    @pyqtProperty(float)
    def pupil_size(self):
        return self._pupil_size

    @pupil_size.setter
    def pupil_size(self, size: float):
        self._pupil_size = max(0.0, min(size, 1.0))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)

        # draw iris
        painter.setBrush(QBrush(self.color_iris))
        painter.drawEllipse(QPointF(0, 0), self.radius, self.radius)

        # draw pupil
        painter.setBrush(QBrush(self.color_pupil))
        pupil_radius = self.radius * self.pupil_size
        painter.drawEllipse(QPointF(0, 0), pupil_radius, pupil_radius)


class DisplayImageWidget(QWidget):
    def __init__(self, parent=None):
        super(DisplayImageWidget, self).__init__(parent)
        self.image_frame = QLabel()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_frame)
        self.setLayout(self.layout)

    def show_image(self, image: np.ndarray):
        # image = image.copy()
        if image.base is not None:      # This doesn't work with a numpy `view` of an array
            image = image.copy()        # So make a copy of the data if it is a view
        image = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888).rgbSwapped()
        self.image_frame.setPixmap(QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QApplication([])

    def move_pupil():
        while True:
            x, y = (np.random.rand() * 2 - 1 for _ in range(2))
            main_widget.set_watch_direction(x, y)
            time.sleep(2)

    def vary_size():
        def remap(x, inlow, inhigh, outlow, outhigh):
            return ((x-inlow) / (inhigh-inlow)) * (outhigh - outlow) + outlow
        while True:
            s = np.random.rand()
            main_widget.set_pupil_size(remap(s, 0, 1, 0.3, 0.9))
            time.sleep(2)

    main_widget = Eyes()
    main_widget.showFullScreen()
    main_widget.setFixedSize(app.primaryScreen().size())
    main_widget.setCursor(Qt.BlankCursor)
    main_widget.show()

    tp = threading.Thread(target=move_pupil, daemon=True)
    ts = threading.Thread(target=vary_size, daemon=True)
    tp.start()
    ts.start()
    app.exec()

