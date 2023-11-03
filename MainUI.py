from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, \
    QPushButton, QTableWidget, QWidget, QFileDialog, QComboBox, QLabel, \
        QButtonGroup, QSlider, QLineEdit, QGroupBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from OutputWindow import OutputWindow

class MainUI(QWidget):
    
    def __init__(self, vispy_canvas_wrapper, file_handler, parent=None):
        

        super().__init__(parent)

        self.vispy_canvas_wrapper = vispy_canvas_wrapper
        self.file_handler = file_handler


        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(175)

        # sem settings
        self.sem_label = QLabel("Select SEM", self)
        self.layout.addWidget(self.sem_label)

        self.dd_select_sem = QComboBox(self)
        self.dd_select_sem.addItems(self.file_handler.sem_db.keys())
        self.layout.addWidget(self.dd_select_sem)

        # image settings
        self.image_box = QGroupBox("Image Settings", self)
        self.image_layout = QVBoxLayout()

        self.select_image_button = QPushButton("Select SEM File", self)
        self.image_layout.addWidget(self.select_image_button)
        self.select_image_button.clicked.connect(self.select_sem_file)

        self.center_image_button = QPushButton("Center Image", self)
        self.image_layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.vispy_canvas_wrapper.center_image)

        self.image_box.setLayout(self.image_layout)
        self.layout.addWidget(self.image_box)
        

        # tools settings
        self.tools_box = QGroupBox("Select Tool", self)
        self.tools_layout = QVBoxLayout()

        tools = dict()
        tools['move'] = QPushButton("&move", self)
        tools['line'] = QPushButton("&line", self)
        tools['circle'] = QPushButton("&circle", self)
        tools['rectangle'] = QPushButton("&rectangle", self)
        tools['scale'] = QPushButton("&identify scaling", self)
        tools['scale'].clicked.connect(self.automatic_scaling)

        self.tools = QButtonGroup(self)


        for i, tool in enumerate(tools.values()):
            tool.setCheckable(True)
            self.tools.addButton(tool, id=i)
            self.tools_layout.addWidget(tool)
        
        self.tools.button(0).setChecked(True)

        self.tools_box.setLayout(self.tools_layout)
        self.layout.addWidget(self.tools_box)

        # scaling

        self.scaling_box = QGroupBox("Scaling", self)
        self.scaling_layout = QVBoxLayout()

        posDouble = QDoubleValidator()   
        posDouble.setBottom(0)
        posInt = QIntValidator()
        posInt.setRange(0, 100000)
        self.pixel_edit = QLineEdit(self, placeholderText="Enter value")
        self.pixel_edit.setValidator(posInt)
        self.length_edit = QLineEdit(self, placeholderText="Enter value")
        self.length_edit.setValidator(posDouble)

        scaling = QHBoxLayout()
        scaling.addWidget(self.pixel_edit)
        scaling.addWidget(QLabel("px    :  "))
        scaling.addWidget(self.length_edit)
        scaling.addWidget(QLabel("µm"))

        self.scaling_layout.addLayout(scaling)
        self.scaling_box.setLayout(self.scaling_layout)
        self.layout.addWidget(self.scaling_box)


        # add empty space
        self.layout.addStretch(1)
        

        # Output
        self.output_box = QGroupBox("Output", self)
        self.output_layout = QVBoxLayout()

        self.structure_edit = QLineEdit(self, placeholderText="enter structure name")
        self.output_layout.addWidget(self.structure_edit)

        self.openOutputWindow = QPushButton("Open Output Window", self)
        self.output_layout.addWidget(self.openOutputWindow)
        self.openOutputWindow.clicked.connect(self.open_output_window)

        self.output_box.setLayout(self.output_layout)
        self.layout.addWidget(self.output_box)

        # Table
        self.table = QTableWidget()
        self.table.setRowCount(5)
        self.table.setColumnCount(5)
        self.layout.addWidget(self.table)
        self.table.hide()
        
        self.setLayout(self.layout)
    
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

    def open_output_window(self):
        self.output_window = OutputWindow()
        self.output_window.show()

    def automatic_scaling(self):
        #only when image is loaded
        if not self.vispy_canvas_wrapper.start_state:
            # get seedPoint from sem_db
            try:
                seed_point = self.file_handler.sem_db[self.dd_select_sem.currentText()]['SeedPoints']
                # only actually try to find scaling bar, when data is given by database
                if seed_point is not None:
                    self.vispy_canvas_wrapper.find_scaling_bar_width(seed_point)
            except:
                self.raise_error("Something went wrong when reading database:")            

