# absolute imports
from vispy.app import use_app
from sys import argv

# relative imports
from .main_window import MainWindow
from .data_handler import DataHandler

class App:

    def __init__(self, img_path=None):

        self.app = use_app("pyqt6")
        self.app.create()
        self.data_handler = DataHandler(img_path=img_path)
        self.main_window = MainWindow(self.data_handler)
        self.data_handler.main_ui = self.main_window.main_ui

    def run(self):
        
        self.main_window.show()
        # update axis because when creating the qt application the transformations change implicitely
        self.main_window.vispy_canvas.center_image()
        self.app.run()

def run(img_path=None):
    if len(argv) > 1:
        App(img_path=argv[1]).run()
    else:
        App(img_path=img_path).run()
        
