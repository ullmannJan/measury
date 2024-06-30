# absolute imports
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QAction, QIcon, QUndoStack, QPalette
from PyQt6.QtWidgets import (QApplication, QMainWindow,
                             QWidget, QHBoxLayout, QSplitter,
                             QMessageBox, QToolButton, 
                             QSizePolicy, QStyle)
from PyQt6.QtCore import Qt
from sys import modules as sys_modules


# relative imports
from . import measury_path
from .main_ui import MainUI
from .right_ui import RightUI
from .vispy_canvas import VispyCanvas
from .windows import AboutWindow, DataWindow, SettingsWindow, XMLWindow
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


        self.data_handler = data_handler

        # settings
        self.settings = Settings(self, "Measury", "Measury")
        self.settings.load_settings()
        
        # set style
        QApplication.setStyle(self.settings.value("graphics/style"))
        
        self.setAcceptDrops(True)

        self.vispy_canvas = VispyCanvas(self)
        self.native_vispy_canvas = DropEnabledQOpenGLWidget(self.vispy_canvas, parent=self)
        
        self.right_ui = RightUI(self)
        self.main_ui = MainUI(self, parent=self)
        self.vispy_canvas.main_window = self
        self.vispy_canvas.main_ui = self.main_ui

        # create undo stack
        self.undo_stack = QUndoStack(self)

        self.initUI()        

    def initUI(self):
        self.setWindowTitle("Measury")
        self.setWindowIcon(QIcon(str(measury_path/"data/tape_measure_128.ico")))
        self.setMinimumSize(700,700)
        # self.setStyleSheet("background-color: white") 

        # Create actions for menu bar
        openAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
                             'Open File', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(lambda : self.main_ui.select_file(file_path=None))
        
        imageFromClipboardAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), 
                                           'Image from Clipboard', self)
        imageFromClipboardAction.setShortcut('Ctrl+V')
        imageFromClipboardAction.setStatusTip('Open image from clipboard')
        imageFromClipboardAction.triggered.connect(lambda : self.data_handler.open_image_from_clipboard(self.vispy_canvas))
        
        saveAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), 
                            'Save File', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.main_ui.open_save_window)

        seeXMLAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView),
                                 'See XML', self)
        seeXMLAction.setShortcut('Ctrl+U')
        seeXMLAction.setStatusTip('See XML of opened file')
        seeXMLAction.triggered.connect(self.open_xml_window)
        
        # edit actions
        undoAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), 
                             'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.setStatusTip('Undo last action')
        undoAction.triggered.connect(self.undo_stack.undo)
        
        redoAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), 
                             'Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.setStatusTip('Redo last action')
        redoAction.triggered.connect(self.undo_stack.redo)
        
        # view
        centerAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), 
                               'Center Image', self)
        centerAction.setShortcut('Ctrl+P')
        centerAction.setStatusTip('Center Image')
        centerAction.triggered.connect(self.vispy_canvas.center_image)
        
        hideAction = QAction(QIcon(str(measury_path/"data/ghost_icon.png")), 
                             'Hide Objects', self)
        hideAction.setShortcut('Ctrl+H')
        hideAction.setStatusTip('Hide Objects')
        hideAction.triggered.connect(self.vispy_canvas.hide_all_objects_w_undo)
        
        showAction = QAction(QIcon(str(measury_path/"data/show_icon.png"))
                             , 'Show Objects', self)
        showAction.setShortcut('Ctrl+Shift+H')
        showAction.setStatusTip('Show Objects')
        showAction.triggered.connect(self.vispy_canvas.show_all_objects_w_undo)
        
        # Settings
        settingsAction = QAction(QIcon(str(measury_path/"data/gear_icon.png")), 'Settings', self)
        settingsAction.setShortcut('Ctrl+I')
        settingsAction.setStatusTip('Open settings page')
        settingsAction.triggered.connect(self.open_settings_page)
        
        resetSettingsAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton), 
                                      'Reset Settings', self)
        resetSettingsAction.setStatusTip('Clear Settings')
        resetSettingsAction.triggered.connect(self.settings.clear)

        # About
        aboutAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation), 
                              'About', self)
        aboutAction.setStatusTip('Show information about Measury')
        aboutAction.triggered.connect(self.open_about_page)
        
        measurementAction = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), 
                                    'Data Overview', self)
        measurementAction.setShortcut('Ctrl+D')
        measurementAction.setStatusTip('Show an overview of all measured data')
        measurementAction.triggered.connect(self.open_data_page)
        
        delete_all_objects_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton), 
                                            'Delete all Objects', self)
        delete_all_objects_action.setStatusTip('Delete all objects')
        delete_all_objects_action.triggered.connect(self.data_handler.delete_all_objects_w_undo)
        
        # Create menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(imageFromClipboardAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(seeXMLAction)

        editMenu = menuBar.addMenu('&Edit')
        editMenu.addAction(delete_all_objects_action)
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)
        settingsMenu = menuBar.addMenu('&Settings')
        settingsMenu.addAction(settingsAction)
        settingsMenu.addAction(resetSettingsAction)
        measurementsMenu = menuBar.addMenu('&Measurements')
        measurementsMenu.addAction(measurementAction)
        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(centerAction)
        viewMenu.addAction(hideAction)
        viewMenu.addAction(showAction)
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
        self.about_window.activateWindow()
        
    def open_settings_page(self):
        self.get_bg_color()
        self.about_window = SettingsWindow(parent=self)
        self.about_window.show()
        self.about_window.activateWindow()

    def open_data_page(self):
        if self.data_handler.drawing_data:
            self.data_window = DataWindow(parent=self)
            self.data_window.show()
            self.data_window.activateWindow()
        
    def closeEvent(self, event):
        QApplication.closeAllWindows()
        
    def raise_error(self, error):  
        self.data_handler.logger.error(error)
        if 'pytest' in sys_modules:
            raise Exception(error)
        else:   
            QMessageBox.critical(self, "Error", str(error))
            
    def reset_undo_stack(self):
        self.undo_stack.clear()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if not self.vispy_canvas.start_state:
                if self.vispy_canvas.selected_object is not None:
                    # reply = QMessageBox.warning(self, "Warning",
                    #     "Do you want to delete the selected object?",
                    #     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    #     QMessageBox.StandardButton.Yes)

                    # if reply == QMessageBox.StandardButton.Yes:
                        self.vispy_canvas.delete_object_w_undo()

    def open_xml_window(self):
        self.data_window = XMLWindow(parent=self)
        self.data_window.show()

    def update_style(self):
        self.data_handler.logger.info("Updating style to " + self.settings.value("graphics/style") + f" dark_mode = {self.is_dark_mode()}")
        QApplication.setStyle(self.settings.value("graphics/style"))

    def is_dark_mode(self):
        app = QApplication.instance()  # Ensures it works with the current QApplication instance
        if not app:  # If the application does not exist, create a new instance
            app = QApplication([])
        return app.palette().color(QPalette.ColorRole.Window).lightness() < 128
    
    def get_bg_color(self):
        QApplication.processEvents()
        color = self.palette().color(QPalette.ColorRole.Window)
        return color

                        
        
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
                  