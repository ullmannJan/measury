
from MainUI import MainUI
from VispyCanvasWrapper import VispyCanvasWrapper
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QSplitterHandle
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._canvas_wrapper = VispyCanvasWrapper()
        self._controls = MainUI(self._canvas_wrapper)
        self._canvas_wrapper.main_ui = self._controls

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon("img/black.png"))
        self.setMinimumSize(300,200)
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

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # controls
        splitter.addWidget(self._controls)
        # vispy canvas
        splitter.addWidget(self._canvas_wrapper.canvas.native)

        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    
    def openCall(self):
        print("tada")