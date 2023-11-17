from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QComboBox, QListWidget, QMessageBox
from PyQt6.QtGui import QIcon
from semmy import __version__ as semmy_version

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
        self.setWindowIcon(QIcon("img/logo/tape_measure_640.png"))
        self.setMinimumSize(300,200)


class OutputWindow(SemmyWindow):
    """
    The window displayed to output the data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dd_select_object = QComboBox(self)
        self.dd_select_object.addItems(self.parent.data_handler.output_data.keys())
        self.layout.addWidget(self.dd_select_object)

        self.object_list = QListWidget()
        if self.dd_select_object.currentText() != "":
            objects = self.parent.data_handler.output_data[self.dd_select_object.currentText()]
            types = [type(obj).__name__ for obj in objects]
            self.object_list.insertItems(0, types)

        self.dd_select_object.currentTextChanged.connect(self.update_object_list)
        self.layout.addWidget(self.object_list)

        self.object_data_list = QListWidget()
        if self.dd_select_object.currentText() != "" and self.object_list.currentItem() != None:
            self.object_data_list.insertItems(0, types)

        self.object_list.currentItemChanged.connect(self.update_object_data_list)
        self.layout.addWidget(self.object_data_list)

    
    def update_object_list(self):
        self.object_list.clear()
        if self.dd_select_object.currentText() != "":
            objects = self.parent.data_handler.output_data[self.dd_select_object.currentText()]
            types = [type(obj).__name__ for obj in objects]
            self.object_list.insertItems(0, types)

    def update_object_data_list(self):
        self.object_data_list.clear()
        if self.dd_select_object.currentText() != "" and self.object_list.currentItem() != None:
            object = self.parent.data_handler.output_data[self.dd_select_object.currentText()][self.object_list.currentRow()]
            self.object_data_list.insertItem(0, object.output_properties())

class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.layout.addWidget(QLabel(f"Semmy v{semmy_version}"))
