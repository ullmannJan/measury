import numpy as np
import cv2
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QSplitter, QTableWidget, QVBoxLayout
from PyQt6.QtGui import QAction, QIcon

from vispy.scene import SceneCanvas, visuals, AxisWidget, Label
from vispy.app import use_app
from vispy.io import load_data_file, read_png



class Semmy():
    def __init__(self, *args, **kwargs):
        self.version = "v0.0.1"
        self.img = read_png("img/black.png")

        self.main_window = None

    def run(self):
        app = use_app("pyqt6")
        app.create()
        self.main_window = MainWindow()
        self.main_window.show()
        app.run()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon("img/black.png"))
        # self.setStyleSheet("background-color: white") 

        # Create actions for menu bar
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(self.openCall)

        # Create menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        settingsMenu = menuBar.addMenu('&Settings')

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # controls
        self._controls = Controls()
        splitter.addWidget(self._controls)

        # vispy canvas
        self._canvas_wrapper = CanvasWrapper()
        splitter.addWidget(self._canvas_wrapper.canvas.native)

        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    
    def openCall(self):
        print("tada")

class Controls(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()


        # self.select_image_label = QtWidgets.QLabel("Select File:")
        # layout.addWidget(self.select_image_label)
        self.select_image_button = QtWidgets.QPushButton("Select SEM File", self)
        layout.addWidget(self.select_image_button)
        self.select_image_button.clicked.connect(self.select_sem_file)

        self.center_image_button = QtWidgets.QPushButton("Recenter Image", self)
        layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.center_image)
        
        # add empty space
        layout.addStretch(1)
        self.setLayout(layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(2)
        layout.addWidget(self.table)

        
    
    def select_sem_file(self):
        file = self.openFileNameDialog()
        img_data = cv2.imread(file)

    def openFileNameDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self,"Select SEM Image", "","All Files (*);;Python Files (*.py)")
        if fileName:
            return fileName

    def center_image(self):
        return

class CanvasWrapper():
    def __init__(self):

        self.img = np.flipud(read_png("img/2023-04-24_PTB_D5_10-01.jpg"))
        self.canvas = SceneCanvas(size=(self.img.shape[1], 
                                        self.img.shape[0]), 
                                        bgcolor=(240/255, 240/255, 240/255,1))

        self.grid = self.canvas.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(1, 1, bgcolor='black')
        self.image = visuals.Image(
            self.img,
            texture_format="auto",
            interpolation='nearest',
            cmap="viridis",
            parent=self.view.scene,
        )

        # title
        title = Label("SEM-Image", color='black', font_size=14)
        title.height_max = 50
        self.grid.add_widget(title, row=0, col=0, col_span=3)
        
        # y axis
        yaxis = AxisWidget(orientation='left',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        yaxis.width_max = 80
        self.grid.add_widget(yaxis, row=1, col=0)
        
        # x axis
        xaxis = AxisWidget(orientation='bottom',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        xaxis.height_max = 50
        self.grid.add_widget(xaxis, row=2, col=1)

        # padding right
        right_padding = self.grid.add_widget(row=1, col=2, row_span=2)
        right_padding.width_max =25

        # camera
        self.view.camera = "panzoom"
        self.view.camera.set_range(x=(0,self.image.size[0]),
                                   y=(0,self.image.size[1]), 
                                   margin=0)
        self.view.camera.aspect = 1

        xaxis.link_view(self.view)
        yaxis.link_view(self.view)
    
    def update_image(self, img):
        self.img = img
        self.image = visuals.Image(
            self.img,
            texture_format="auto",
            interpolation='nearest',
            cmap="viridis",
            parent=self.view.scene,
        )


        

if __name__ == "__main__":
    S = Semmy()
    S.run()