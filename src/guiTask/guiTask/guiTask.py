#!/home/moustafa/ros2_ws/venv/bin/python3
import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, 
                             QTabWidget, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QPushButton)
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent, QKeyEvent
from PyQt5.QtCore import QTimer, Qt

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SubscriberNode(Node):
    def __init__(self, label):
        super().__init__('subscriber_node')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.label = label

    def listener_callback(self, msg):
        self.label.setText(f"Reading: {msg.data}")

class Tab1(QWidget):
    def __init__(self, source1=None, source2=None, parent=None): 
        super().__init__(parent) 

        self.cap1 = cv2.VideoCapture(source1)
        self.imgLabel1 = QLabel(self)
        self.imgLabel1.setFixedSize(640, 480)
        self.imgLabel1.setScaledContents(True)

        self.cap2 = cv2.VideoCapture(source2)
        self.imgLabel2 = QLabel(self)
        self.imgLabel2.setFixedSize(640, 480)
        self.imgLabel2.setScaledContents(True)

        self.sensorLabel = QLabel("Waiting for connection")
        self.sensorLabel.setFixedSize(150,100)
        self.sensorLabel.setScaledContents(True)

        rclpy.init()
        self.node = SubscriberNode(self.sensorLabel)

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_frame(self.cap1,self.imgLabel1))
        self.timer.timeout.connect(lambda: self.update_frame(self.cap2,self.imgLabel2))
        self.timer.timeout.connect(self.spin_ros)
        self.timer.start(30)

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        layout.addWidget(self.imgLabel1,0,0)
        layout.addWidget(self.imgLabel2,0,1)
        layout.addWidget(self.sensorLabel,1,0)
        self.setLayout(layout)

    def spin_ros(self):
        rclpy.spin_once(self.node, timeout_sec=0.01)

    def update_frame(self, cap : cv2.VideoCapture, imgLabel : QLabel) -> None:
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            imgLabel.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.node.destroy_node()
        rclpy.shutdown()
        event.accept()

class Tab2(QWidget):
    def __init__(self, source=None, parent=None): 
        super().__init__(parent) 

        self.count = 0

        self.cap = cv2.VideoCapture(source)
        self.imgLabel = QLabel(self)
        self.imgLabel.setFixedSize(640, 480)
        self.imgLabel.setScaledContents(True)

        self.button = QPushButton("Capture",self)
        self.button.setFixedSize(150,100)
        self.button.clicked.connect(lambda: self.capture(self.cap))

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_frame(self.cap,self.imgLabel))
        self.timer.start(30)

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.addWidget(self.imgLabel)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def capture(self, cap : cv2.VideoCapture):
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("src/guiTask/Capture/cap" + str(self.count) + ".jpg", frame)
            self.count += 1

    def update_frame(self, cap : cv2.VideoCapture, imgLabel : QLabel) -> None:
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            imgLabel.setPixmap(QPixmap.fromImage(qt_image))    

class Tab3(QWidget):
    def __init__(self, source=None, parent=None): 
        super().__init__(parent) 
        self.setFocusPolicy(Qt.StrongFocus)

        self.contoursToDraw = {"Circles" : [], "Rectangles" : [], "Triangles" : [], "Crosses" : []}
        self.colors = {"Circles" : (0,0,255), "Rectangles" : (0,255,0), "Triangles" : (255,0,0), "Crosses" : (255,255,0)}

        self.img = cv2.imread(source)
        self.img = cv2.resize(self.img, (640, 480))
        self.count = {"Circles" : 0, "Rectangles" : 0, "Triangles" : 0, "Crosses" : 0}
        self.shapes = {"Circles" : [], "Rectangles" : [], "Triangles" : [], "Crosses" : []}

        contours = self.temp(self.img)
        for contour in contours:
            self.shapes[self.classify_shape(self.img, contour)].append(contour)

        self.imgLabel = QLabel(self)
        self.imgLabel.setFixedSize(640, 480)
        self.imgLabel.mousePressEvent = (lambda event : self.update_img(self.img,self.imgLabel, event))

        self.circleLabel = QLabel("Circles: 0")
        self.rectangleLabel = QLabel("Rectangles: 0")
        self.triangleLabel = QLabel("Triangles: 0")
        self.crossLabel = QLabel("Crosses: 0")
        self.modeLabel = QLabel("Mode: All")

        self.mode = "All"

        self.initUI()

    def initUI(self):

        self.initImgLabel(self.img, self.imgLabel)

        tabLayout = QHBoxLayout()
        tabLayout.addWidget(self.imgLabel)
        self.setLayout(tabLayout)

        labelLayout = QVBoxLayout()

        for label in [self.circleLabel, self.rectangleLabel, self.triangleLabel, self.crossLabel, self.modeLabel]:
            label.setStyleSheet("font-size: 16px; padding: 5px;")
            labelLayout.addWidget(label)

        tabLayout.addLayout(labelLayout)

    def initImgLabel(self, img, imgLabel : QLabel):
        h, w, ch = img.shape
        bytes_per_line = ch * w
        qt_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        imgLabel.setPixmap(QPixmap.fromImage(qt_image))

    def temp(self, img) -> list:
        img_filtered = cv2.medianBlur(img, 5) 

        sharpening_kernel = np.array([[-1, -1, -1], 
                                    [-1, 9, -1], 
                                    [-1, -1, -1]]) 
        
        img_sharpened = cv2.filter2D(img_filtered, -1, sharpening_kernel) 

        img_gray = cv2.cvtColor(img_sharpened, cv2.COLOR_BGR2GRAY) 

        img_blur = cv2.GaussianBlur(img_gray, (5,5), 0) 

        MorphologyKernel = np.ones((5,5), np.uint8) 
        img_morph = cv2.morphologyEx(img_blur, cv2.MORPH_CLOSE, MorphologyKernel) 
        img_morph = cv2.morphologyEx(img_morph, cv2.MORPH_OPEN, MorphologyKernel) 

        edges = cv2.Canny(img_morph, 50, 100) 

        kernel = np.ones((5, 5), np.uint8) 
        closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel) 

        contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

        MeanArea = np.mean([cv2.contourArea(contour) for contour in contours])
        MedianArea = np.median([cv2.contourArea(contour) for contour in contours])

        criteria = MedianArea if MedianArea > MeanArea else MeanArea
        criteria *= 0.5

        filter_By_Area_contours = [] 
        for contour in contours: 
            if cv2.contourArea(contour) > criteria: 
                filter_By_Area_contours.append(contour) 
            else: 
                hull = cv2.convexHull(contour) 
                if cv2.contourArea(hull) > criteria: 
                    filter_By_Area_contours.append(hull)

        filter_By_ArcLength_contours = [contour for contour in filter_By_Area_contours if cv2.arcLength(contour,False) < cv2.contourArea(contour)*0.4]

        filtered_contours = [contour for contour in filter_By_ArcLength_contours if cv2.contourArea(contour) < criteria*4] 

        return filtered_contours

    def is_circle(self, contour, center):
        distances = [cv2.norm(point[0] - np.array(center)) for point in contour]
        mean_distance = np.mean(distances)
        variance = np.var(distances)

        return variance < (0.01 * mean_distance ** 2)

    def classify_shape(self, img, contour) -> str:
        img_copy = img.copy()

        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        (x, y), radius = cv2.minEnclosingCircle(contour)
        center = (int(x), int(y))

        if len(approx) == 3:
            return "Triangles"
        elif len(approx) == 4:
            return "Rectangles"
        elif self.is_circle(contour, center):
            return "Circles"
        else:
            return "Crosses"

    def updateLabels(self):
        self.circleLabel.setText("Circles: " + str(self.count['Circles']))
        self.rectangleLabel.setText("Rectangles: " + str(self.count['Rectangles']))
        self.triangleLabel.setText("Triangles: " + str(self.count['Triangles']))
        self.crossLabel.setText("Crosses: " + str(self.count['Crosses']))

    def drawContours(self):
        img = self.img.copy()
        for key in self.contoursToDraw:
            contours = self.contoursToDraw[key]
            for contour in contours:
                cv2.drawContours(img, [contour], -1, self.colors[key], 2) 

        h, w, ch = img.shape
        bytes_per_line = ch * w
        qt_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.imgLabel.setPixmap(QPixmap.fromImage(qt_image))

    def updateContoursToDraw(self, key, point):
        for contour in self.shapes[key]:
            result = cv2.pointPolygonTest(contour, point, False)
            if result < 0:
                continue

            if any(contour is stored_contour for stored_contour in self.contoursToDraw[key]):
                self.count[key] -= 1
                self.contoursToDraw[key] = [c for c in self.contoursToDraw[key] if c is not contour]
            else:
                self.count[key] += 1
                self.contoursToDraw[key].append(contour)

    def update_img(self, img, imgLabel : QLabel, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            point = (int(event.pos().x()), int(event.pos().y()))
            if self.mode == "All":
                for key in self.shapes:
                    self.updateContoursToDraw(key,point)
            else:
                self.updateContoursToDraw(self.mode,point)

            self.updateLabels()
            self.drawContours()
     

    def keyPressEvent(self, event: QKeyEvent):
        key = event.text()
        if key == 'a':
            self.mode = "All"
        elif key == 'c':
            self.mode = "Circles"
        elif key == 't':
            self.mode = "Triangles"
        elif key == 'r':
            self.mode = "Rectangles"
        elif key == 'x':
            self.mode = "Crosses"
        self.modeLabel.setText("Mode: " + self.mode)

class MainWindow(QMainWindow): 
    def __init__(self): 
        super().__init__()
        self.setWindowTitle("My GUI")
        self.setGeometry(0, 0, 500, 500)      

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.tab1 = Tab1(source1='/home/moustafa/Downloads/Kendrick Lamar - Not Like Us.mp4',
                         source2='/home/moustafa/Downloads/Kendrick Lamar - Not Like Us.mp4')
        self.tab2 = Tab2(source='/home/moustafa/Downloads/Kendrick Lamar - Not Like Us.mp4')
        self.tab3 = Tab3(source='/home/moustafa/Downloads/original.jpeg')

        # Add tabs to the QTabWidget
        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")
        self.tabs.addTab(self.tab3, "Tab 3")

def main(args=None):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()