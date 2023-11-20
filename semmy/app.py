# absolute imports
from vispy.app import use_app

# relative imports
from .main_window import MainWindow
from .data_handler import DataHandler

class App:

    def __init__(self, development_mode=False):

        self.app = use_app("pyqt6")
        self.app.create()
        self.data_handler = DataHandler()
        self.main_window = MainWindow(self.data_handler, 
                                      development_mode=development_mode)
        self.data_handler.main_ui = self.main_window.main_ui

    def run(self):
        
        self.main_window.show()
        self.app.run()

def run(development_mode=False):
    App(development_mode=development_mode).run()