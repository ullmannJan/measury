# absolute imports
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QAction, QIcon, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow,
                             QWidget, QHBoxLayout, QSplitter,
                             QMessageBox, QToolButton, 
                             QSizePolicy)
from PyQt6.QtCore import Qt
from sys import modules as sys_modules


# relative imports
from . import semmy_path
from .main_ui import MainUI
from .right_ui import RightUI
from .vispy_canvas import VispyCanvas
from .windows import AboutWindow, DataWindow, SettingsWindow
from .settings import Settings

class MainWindow(QMainWindow):
    """Qt MainWindow of Application.

    This class represents the Main Window of the application and 
    contains several subclasses:
        main_ui : Qt UI interface
        vispy_canvas: vispy_implementation into Qt
        data_handler: data structure
    """

    def __init__(self, data_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # settings
        self.data_handler = data_handler

        self.settings = Settings(self, "Semmy", "Semmy")
        self.settings.load_settings()
        
        self.setAcceptDrops(True)

        self.vispy_canvas = VispyCanvas(self)
        self.native_vispy_canvas = DropEnabledQOpenGLWidget(self.vispy_canvas, parent=self)
        
        self.right_ui = RightUI(self)
        self.main_ui = MainUI(self, parent=self)
        self.vispy_canvas.main_window = self
        self.vispy_canvas.main_ui = self.main_ui
        

        self.initUI()        

    def initUI(self):
        self.setWindowTitle("Semmy")
        self.setWindowIcon(QIcon(str(semmy_path/"data/tape_measure_128.ico")))
        self.setMinimumSize(600,600)
        # self.setStyleSheet("background-color: white") 

        # Create actions for menu bar
        openAction = QAction(QIcon('open.png'), 'Open File', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(lambda : self.main_ui.select_sem_file(file_path=None))
        
        imageFromClipboardAction = QAction(QIcon('open.png'), 'Image from Clipboard', self)
        imageFromClipboardAction.setShortcut('Ctrl+V')
        imageFromClipboardAction.setStatusTip('Open image from clipboard')
        imageFromClipboardAction.triggered.connect(lambda : self.data_handler.open_image_from_clipboard(self.vispy_canvas))
        
        saveAction = QAction(QIcon('save.png'), 'Save File', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.main_ui.open_save_window)
        
        centerAction = QAction(QIcon('open.png'), 'Center Image', self)
        centerAction.setShortcut('Ctrl+P')
        centerAction.setStatusTip('Center Image')
        centerAction.triggered.connect(self.vispy_canvas.center_image)
        
        # Settings
        settingsAction = QAction(QIcon('open.png'), 'Settings', self)
        settingsAction.setShortcut('Ctrl+I')
        settingsAction.setStatusTip('Open settings page')
        settingsAction.triggered.connect(self.open_settings_page)
        
        resetSettingsAction = QAction(QIcon('open.png'), 'Reset Settings', self)
        resetSettingsAction.setStatusTip('Clear Settings')
        resetSettingsAction.triggered.connect(self.settings.clear)

        # About
        aboutAction = QAction(QIcon('open.png'), 'About', self)
        aboutAction.setStatusTip('Show information about Semmy')
        aboutAction.triggered.connect(self.open_about_page)
        
        measurementAction = QAction(QIcon('open.png'), 'Data Overview', self)
        measurementAction.setShortcut('Ctrl+D')
        measurementAction.setStatusTip('Show an overview of all measured data')
        measurementAction.triggered.connect(self.open_data_page)
        
        delete_all_objects_action = QAction(QIcon('open.png'), 'Clear Objects', self)
        delete_all_objects_action.setStatusTip('Delete all objects')
        delete_all_objects_action.triggered.connect(self.data_handler.delete_all_objects)
        
        # Create menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(imageFromClipboardAction)
        fileMenu.addAction(saveAction)
        settingsMenu = menuBar.addMenu('&Settings')
        settingsMenu.addAction(settingsAction)
        settingsMenu.addAction(resetSettingsAction)
        measurementsMenu = menuBar.addMenu('&Measurements')
        measurementsMenu.addAction(measurementAction)
        measurementsMenu.addAction(delete_all_objects_action)
        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(centerAction)
        miscMenu = menuBar.addMenu('&Misc')
        miscMenu.addAction(aboutAction)

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # controls
        self.splitter.addWidget(self.main_ui)
        # vispy canvas
        self.splitter.addWidget(self.native_vispy_canvas)
        # right ui
        self.splitter.addWidget(self.right_ui)

        # The slim bar (tool button)
        self.open_right_ui_button = QToolButton()
        self.open_right_ui_button.setText("<")
        self.open_right_ui_button.clicked.connect(self.right_ui.show_ui)

        self.open_right_ui_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        # Hide the right panel by default
        self.right_ui.hide()
        
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.open_right_ui_button)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def open_about_page(self):
        self.about_window = AboutWindow(parent=self)
        self.about_window.show()
        
    def open_settings_page(self):
        self.about_window = SettingsWindow(parent=self)
        self.about_window.show()

    def open_data_page(self):
        if self.data_handler.drawing_data:
            self.data_window = DataWindow(parent=self)
            self.data_window.show()
        
    def closeEvent(self, event):
        QApplication.closeAllWindows()
        
    def raise_error(self, error):  
        if 'pytest' in sys_modules:
            raise Exception(error)
        else:   
            QMessageBox.critical(self, "Error", str(error))
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if not self.vispy_canvas.start_state:
                if self.vispy_canvas.selected_object is not None:
                    reply = QMessageBox.warning(self, "Warning",
                        "Do you want to delete the selected object?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes)

                    if reply == QMessageBox.StandardButton.Yes:
                        self.vispy_canvas.delete_object()
                        
        
class DropEnabledQOpenGLWidget(QOpenGLWidget):
    def __init__(self, vispy_canvas, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.vispy_canvas = vispy_canvas
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.addWidget(vispy_canvas.native)

    def dragEnterEvent(self, event):
        if len(event.mimeData().urls()) == 1:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if len(event.mimeData().urls()) == 1:
            img_path = event.mimeData().urls()[0].toLocalFile()
            self.vispy_canvas.data_handler.open_file(img_path, self.vispy_canvas)
                  