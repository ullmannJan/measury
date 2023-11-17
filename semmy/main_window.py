
from semmy.main_ui import MainUI
from semmy.vispy_canvas import VispyCanvas
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QAction, QIcon, QWindow
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox
from PyQt6.QtCore import Qt

from semmy.windows import AboutWindow

class MainWindow(QMainWindow):
    def __init__(self, data_handler, development_mode=False, img=r"img/2023-06-29-D5-11-01.tif", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

        self.data_handler = data_handler
        if development_mode:
            self.vispy_canvas = VispyCanvas(self.data_handler, img=img)
        else:
            self.vispy_canvas = VispyCanvas(self.data_handler)

        self.native_vispy_canvas = DropEnabledQOpenGLWidget(self.vispy_canvas, parent=self)
        self.main_ui = MainUI(self.vispy_canvas, self.data_handler)
        self.vispy_canvas.main_ui = self.main_ui

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon("img/logo/tape_measure_128.png"))
        self.setMinimumSize(700,700)
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
        splitter.addWidget(self.native_vispy_canvas)

        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    

    def open_about_page(self):
        self.about_window = AboutWindow(parent=self)
        self.about_window.show()

class DropEnabledQOpenGLWidget(QOpenGLWidget):
    def __init__(self, vispy_canvas, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.vispy_canvas = vispy_canvas
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.addWidget(vispy_canvas.native)

    def dragEnterEvent(self, event):
        print('entered')
        if len(event.mimeData().urls()) == 1:
            print('accepted')
            print(event.mimeData().urls())
            event.accept()
        else:
            print('denied')
            event.ignore()

    def dropEvent(self, event):
        if len(event.mimeData().urls()) == 1:
            img_path = event.mimeData().urls()[0].toLocalFile()

            update = True

            # if there is a file loaded, ask if the user wants to load a new picture
            if not self.vispy_canvas.start_state:
                reply = QMessageBox.warning(self, "Warning",
                        "Do you want to load a new image?\n\nThis will replace the current image.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.Yes:
                    update = True
                else:
                    update = False

            if update:
                self.vispy_canvas.data_handler.img_path = img_path
                self.vispy_canvas.update_image()
            
                  