# absolute imports
from vispy.app import use_app
from sys import argv

# relative imports
from .main_window import MainWindow
from .data_handler import DataHandler

class App:

    def __init__(self, file_path=None):

        self.app = use_app("pyqt6")
        self.app.create()
        self.data_handler = DataHandler()
        self.main_window = MainWindow(self.data_handler)
        self.data_handler.main_ui = self.main_window.main_ui
        self.data_handler.open_file(file_path=file_path, 
                                    vispy_instance=self.main_window.vispy_canvas)

    def run(self):
        
        self.main_window.show()
        # update axis because when creating the qt application the transformations change implicitely
        self.main_window.vispy_canvas.center_image()
        self.app.run()

def run(file_path=None):
    if len(argv) > 1:
        App(file_path=argv[1]).run()
    else:
        App(file_path=file_path).run()
        
