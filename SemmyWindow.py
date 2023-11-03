from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtGui import QIcon

class SemmyWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setWindowTitle("Semmy: Output window")
        self.setWindowIcon(QIcon("img/logo/tape_measure_640.png"))
        self.setMinimumSize(300,200)


class OutputWindow(SemmyWindow):
    """
    The window displayed to output the data.
    """
    def __init__(self):
        super().__init__()

class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, version):
        super().__init__()
        
        self.layout.addWidget(QLabel(f"Semmy v{version}"))