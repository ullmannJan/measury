
from MainUI import MainUI
from VispyCanvas import VispyCanvas
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self, file_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file_handler = file_handler
        self.vispy_canvas = VispyCanvas(self.file_handler)
        self.qt_controls = MainUI(self.vispy_canvas, self.file_handler)
        self.vispy_canvas.main_ui = self.qt_controls

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon("img/logo/tape_measure_640.png"))
        self.setMinimumSize(300,200)
        # self.setStyleSheet("background-color: white") 

        # Create actions for menu bar
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(self.qt_controls.select_sem_file)
        
        centerAction = QAction(QIcon('open.png'), '&Center', self)
        centerAction.setShortcut('Ctrl+P')
        centerAction.setStatusTip('Center Image')
        centerAction.triggered.connect(self.vispy_canvas.center_image)

        # Create menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        settingsMenu = menuBar.addMenu('&Settings')
        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(centerAction)

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # controls
        splitter.addWidget(self.qt_controls)
        # vispy canvas
        splitter.addWidget(self.vispy_canvas.native)

        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
