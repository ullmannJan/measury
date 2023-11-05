
from semmy.main_ui import MainUI
from semmy.vispy_canvas import VispyCanvas
from PyQt6.QtGui import QAction, QIcon, QWindow
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from semmy.windows import AboutWindow

class MainWindow(QMainWindow):
    def __init__(self, data_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data_handler = data_handler
        self.vispy_canvas = VispyCanvas(self.data_handler)
        self.main_ui = MainUI(self.vispy_canvas, self.data_handler)
        self.vispy_canvas.main_ui = self.main_ui

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon("img/logo/tape_measure_125.png"))
        self.setMinimumSize(300,200)
        # self.setStyleSheet("background-color: white") 

        # Create actions for menu bar
        openAction = QAction(QIcon('open.png'), '&Open File', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(self.main_ui.select_sem_file)
        
        centerAction = QAction(QIcon('open.png'), '&Center Image', self)
        centerAction.setShortcut('Ctrl+P')
        centerAction.setStatusTip('Center Image')
        centerAction.triggered.connect(self.vispy_canvas.center_image)

        aboutAction = QAction(QIcon('open.png'), '&About', self)
        aboutAction.setStatusTip('Show information about Semmy')
        aboutAction.triggered.connect(self.open_about_page)

        # Create menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        settingsMenu = menuBar.addMenu('&Settings')
        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(centerAction)
        miscMenu = menuBar.addMenu('&Misc')
        miscMenu.addAction(aboutAction)

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # controls
        splitter.addWidget(self.main_ui)
        # vispy canvas
        splitter.addWidget(self.vispy_canvas.native)

        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    

    def open_about_page(self):
        self.about_window = AboutWindow(parent=self)
        self.about_window.show()