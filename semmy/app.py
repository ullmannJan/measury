from vispy.app import use_app
from semmy.main_window import MainWindow
from semmy.data_handler import DataHandler

class App:

    def __init__(self):

        self.app = use_app("pyqt6")
        self.app.create()
        self.data_handler = DataHandler()
        self.main_window = MainWindow(self.data_handler)

    def run(self):
        self.main_window.show()
        self.app.run()

def run():
    App().run()