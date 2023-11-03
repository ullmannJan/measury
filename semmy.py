from vispy.app import use_app
from MainWindow import MainWindow
from DataHandler import DataHandler

class Semmy:

    def __init__(self):

        self.version = "0.1.0" 

        self.app = use_app("pyqt6")
        self.app.create()
        self.data_handler = DataHandler(version=self.version)
        self.main_window = MainWindow(self.data_handler)

    def run(self):
        self.main_window.show()
        self.app.run()
        

if __name__ == "__main__":
    S = Semmy()
    S.run()