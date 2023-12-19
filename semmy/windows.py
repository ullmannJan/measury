# absolute imports
import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, \
    QGroupBox, QLineEdit, QPushButton
from PyQt6.QtGui import QIcon


# relative imports
from . import __version__ as semmy_version
from . import run_path

class SemmyWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setWindowTitle("Semmy: Output window")
        self.setWindowIcon(QIcon(str(run_path/"img/logo/tape_measure_128.ico")))
        self.setMinimumSize(300,200)


class OutputWindow(SemmyWindow):
    """
    The window displayed to output the data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Output Dialog")
        # Output
        self.output_box = QGroupBox("Output", self)
        self.output_layout = QVBoxLayout()

        self.structure_edit = QLineEdit(self, placeholderText="Enter structure name")
        self.output_layout.addWidget(self.structure_edit)

        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.parent.data_handler.save_output_file)
        self.output_layout.addWidget(self.saveButton)


        self.output_box.setLayout(self.output_layout)
        self.layout.addWidget(self.output_box)


class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.layout.addWidget(QLabel(f"Semmy v{semmy_version}"))
