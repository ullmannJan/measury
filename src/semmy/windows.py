# absolute imports
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, \
    QGroupBox, QPushButton, QCheckBox
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt


# relative imports
from . import __version__ as semmy_version
from . import semmy_path

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
        self.setWindowIcon(QIcon(str(semmy_path/"data/tape_measure_128.ico")))
        self.setMinimumSize(300,200)


class SaveWindow(SemmyWindow):
    """
    The window displayed to save the data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Save Dialog")
                
        #Save Options 
        self.options_box = QGroupBox("Options", self)
        self.options_layout = QVBoxLayout()
        self.options_box.setLayout(self.options_layout)
        self.layout.addWidget(self.options_box)
        
        self.save_img_checkbox = QCheckBox(text="Save Image")
        self.save_img_checkbox.setChecked(True)
        self.options_layout.addWidget(self.save_img_checkbox)

        # Save Button
        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.save)
        self.layout.addWidget(self.saveButton)

    def save(self):
        return self.parent.data_handler.save_storage_file(save_image=self.save_img_checkbox.isChecked())


class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.layout.addWidget(QLabel(f"Semmy v{semmy_version}"))

class DataWindow(SemmyWindow):
    """
    The window displaying the data results.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Measurements")
        
        label = QLabel(self.parent.data_handler.calculate_results_string())
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Make the text selectable
        self.layout.addWidget(label)

        # Copy Button
        self.copyButton = QPushButton("Copy", self)
        self.copyButton.clicked.connect(self.copy_to_clipboard)
        self.layout.addWidget(self.copyButton)
        # Save Button
        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.parent.data_handler.save_measurements_file)
        self.layout.addWidget(self.saveButton)
        
    def copy_to_clipboard(self):
        cb = QGuiApplication.clipboard()
        cb.clear()
        cb.setText(self.parent.data_handler.calculate_results_string())
        print(cb.text())