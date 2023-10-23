from vispy.app import use_app
from MainWindow import MainWindow
from FileHandler import FileHandler

class Semmy:

    version = "v0.0.1"

    def __init__(self):

        self.app = use_app("pyqt6")
        self.app.create()
        self.file_handler = FileHandler()
        self.main_window = MainWindow(self.file_handler)

    def run(self):
        self.main_window.show()
        self.app.run()
        

if __name__ == "__main__":
    S = Semmy()
    S.run()