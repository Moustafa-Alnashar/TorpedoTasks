import sys
import numpy as np
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, 
                             QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton)
from PySide6.QtGui import QImage, QPixmap, QMouseEvent, QKeyEvent
from PySide6.QtCore import QTimer

class Tab2(QWidget):
    def __init__(self, source=None, parent=None) -> None: 
        super().__init__(parent) 

        self.temp = cv2.imread("C:/Users/moustafa/Desktop/depth.tiff", cv2.IMREAD_UNCHANGED)
        print(self.temp.shape, self.temp.dtype)

        self.cvframe_container = [None]
        self.k = 0
        self.arr = [None, None]

        self.cap = cv2.VideoCapture(source)

        self.imgLabel1 = QLabel(self)
        self.imgLabel1.setFixedSize(640, 480)
        self.imgLabel1.setScaledContents(True)

        self.imgLabel2 = QLabel(self)
        # self.imgLabel2.setFixedSize(640, 480)
        self.imgLabel2.setFixedSize(960, 1280)###############################
        self.imgLabel2.setScaledContents(True)
        self.imgLabel2.mousePressEvent = lambda event: self.mousePressFunction(event)

        self.distLabel = QLabel(self)
        self.distLabel.setFixedSize(200,50)
        self.distLabel.setText("Not Initialized")

        self.button = QPushButton("Capture",self)
        self.button.setFixedSize(150,100)
        # self.button.clicked.connect(lambda: self.update_frame(self.imgLabel2, cap=self.cap, retframe=self.cvframe_container))
        self.button.clicked.connect(lambda: self.update_frame(self.imgLabel2, drawFrame=cv2.imread(source), retframe=self.cvframe_container))

        # self.timer = QTimer(self)
        # self.timer.timeout.connect(lambda: self.update_frame(self.imgLabel1, cap=self.cap))
        # self.timer.start(30)

        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.distLabel)

        pageLayout = QHBoxLayout()
        pageLayout.addWidget(self.imgLabel1)
        pageLayout.addWidget(self.imgLabel2)
        pageLayout.addLayout(layout)
        self.setLayout(pageLayout)  

    def update_frame(self, imgLabel : QLabel, drawFrame : cv2.typing.MatLike = None, cap : cv2.VideoCapture = None, 
                     retframe : list = None) -> None:
        frame = None
        ret = False

        if cap is not None:
            ret, frame = cap.read()
        elif drawFrame is not None :
            ret, frame = True, drawFrame
            print(frame.shape)

        if ret:
            pixmap = self.cvframe_to_pixmap(frame)
            imgLabel.setPixmap(pixmap)
            
            if retframe is not None:
                retframe.clear()
                retframe.append(frame)

    def drawPoints(self):
        frame = self.cvframe_container[0].copy()
        colors = [(0,200,0),(200,0,0)]
        i=0
        for pos in self.arr:
            if pos is not None:
                cv2.drawMarker(
                    frame, 
                    position=pos, 
                    color=colors[i],
                    markerType=cv2.MARKER_STAR,
                    markerSize=20,
                    thickness=2
                )
                i += 1
        self.update_frame(self.imgLabel2, drawFrame=frame)

    def mousePressFunction(self, event : QMouseEvent) -> None: 
        if self.cvframe_container[0] is not None:
            pos = event.position()

            label_width = self.imgLabel2.width()
            label_height = self.imgLabel2.height()
            frame_height, frame_width, _ = self.cvframe_container[0].shape

            x_ratio = frame_width / label_width
            y_ratio = frame_height / label_height

            mapped_x = int(pos.x() * x_ratio)
            mapped_y = int(pos.y() * y_ratio)

            self.arr[self.k] = (mapped_x, mapped_y)

            print(f"{label_width = }, {label_height = }")
            print(f"{frame_width = }, {frame_height = }")
            print(f"{pos.x() = }, {x_ratio = }, {pos.x() * x_ratio= }")
            print(f"{pos.y() = }, {y_ratio = }, {pos.y() * y_ratio = }")
            d = self.temp[mapped_y, mapped_x]
            print(f"depth = {d * 100}")   

            if not None in self.arr:
                p1 = self.arr[0]
                p2 = self.arr[1]
                dist_pixel = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
                self.distLabel.setText(str(dist_pixel) + " pixel")
            
            self.drawPoints()

    def keyPressEvent(self, event : QKeyEvent):
        key = event.text()
        if key == '1':
            self.k = 0
        elif key == '2':
            self.k = 1

    def pixmap_to_cvframe(self, pixmap : QPixmap)  -> cv2.typing.MatLike:
        # Convert QPixmap to QImage
        qimage = pixmap.toImage()
        qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)

        # Obtain raw data as a NumPy array
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
        arr = np.array(ptr).reshape((height, width, 4))  # Reshape to HxWx4 (RGBA)

        # Convert RGBA to BGR (OpenCV format)
        cv_frame = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        return cv_frame

    def cvframe_to_pixmap(self, cvframe : cv2.typing.MatLike) -> QPixmap:
        frame = cv2.cvtColor(cvframe, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        return pixmap 

class MainWindow(QMainWindow): 
    def __init__(self): 
        super().__init__()
        self.setWindowTitle("My GUI")
        self.setGeometry(0, 0, 500, 500)      

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        # self.tab2 = Tab2(source="C:/Users/moustafa/Videos/Captures/Honkai_ Star Rail 2025-02-19 00-35-59.mp4")


        self.tab2 = Tab2(source="C:/Users/moustafa/Downloads/depthcali150_2.jpeg")

        # Add tabs to the QTabWidget
        self.tabs.addTab(self.tab2, "Tab 2")

def main(args=None):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()