from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QPushButton, QTableWidget, QWidget, QFileDialog

class MainUI(QWidget):

    def __init__(self, vispy_canvas_wrapper, file_handler, parent=None):
        super().__init__(parent)

        self.vispy_canvas_wrapper = vispy_canvas_wrapper
        self.file_handler = file_handler


        layout = QVBoxLayout()
        self.setMinimumWidth(200)

        # self.select_image_label = QtWidgets.QLabel("Select File:")
        # layout.addWidget(self.select_image_label)
        self.select_image_button = QPushButton("Select SEM File", self)
        layout.addWidget(self.select_image_button)
        self.select_image_button.clicked.connect(self.select_sem_file)

        self.center_image_button = QPushButton("Center Image", self)
        layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.vispy_canvas_wrapper.center_image)
        


        # add empty space
        layout.addStretch(1)
        self.setLayout(layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(2)
        layout.addWidget(self.table)

        
    
    def select_sem_file(self):
        self.file_handler.img_path = self.openFileNameDialog()
        self.vispy_canvas_wrapper.update_image()

    def openFileNameDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self,"Select SEM Image", "","All Files (*);;Python Files (*.py)")
        if fileName:
            return fileName
        
    def raise_error(self, error):        
        msg = QMessageBox.critical(None, "Error", str(error))
        msg.exec()

