# absolute imports
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, \
        QPushButton, QTableWidget, QWidget, QFileDialog, QComboBox, QLabel, \
        QButtonGroup, QLineEdit, QGroupBox, QTableWidgetItem
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from pathlib import Path

# relative imports
from .windows import SaveWindow
from .vispy_canvas import VispyCanvas

class MainUI(QWidget):
    
    def __init__(self, vispy_canvas_wrapper: VispyCanvas, data_handler, parent=None):
        

        super().__init__(parent)

        self.vispy_canvas_wrapper = vispy_canvas_wrapper
        self.data_handler = data_handler

        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(175)

        # sem settings

        # image settings
        self.image_box = QGroupBox("Image Settings", self)
        self.image_layout = QVBoxLayout()

        self.select_image_button = QPushButton("Select SEM File", self)
        self.image_layout.addWidget(self.select_image_button)
        
        self.select_image_button.clicked.connect(lambda _: self.select_sem_file(file_path=None))

        self.center_image_button = QPushButton("Center Image", self)
        self.image_layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.vispy_canvas_wrapper.center_image)
        
        self.sem_label = QLabel("Select SEM", self)
        self.image_layout.addWidget(self.sem_label)

        self.dd_select_sem = QComboBox(self)
        self.dd_select_sem.addItems(self.data_handler.sem_db.keys())
        self.image_layout.addWidget(self.dd_select_sem)

        self.image_box.setLayout(self.image_layout)
        self.layout.addWidget(self.image_box)
        

        # tools settings
        self.tools_box = QGroupBox("Select Tool", self)
        self.tools_layout = QVBoxLayout()

        tools = dict()
        tools['move'] = QPushButton("&move", self)
        tools['select'] = QPushButton("&select", self)
        tools['line'] = QPushButton("&line", self)
        tools['circle'] = QPushButton("&circle", self)
        tools['rectangle'] = QPushButton("&rectangle", self)
        tools['angle'] = QPushButton("&angle", self)
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

        self.scaling = 1.
        self.scaling_box = QGroupBox("Scaling", self)
        self.scaling_layout = QVBoxLayout()

        posDouble = QDoubleValidator()
        posDouble.setBottom(0)
        posInt = QIntValidator()
        posInt.setBottom(0)
        self.pixel_edit = QLineEdit(self, placeholderText="Enter value")
        self.pixel_edit.setValidator(posInt)
        self.pixel_edit.textChanged.connect(self.update_scaling)
        self.length_edit = QLineEdit(self, placeholderText="Enter value")
        self.length_edit.setValidator(posDouble)
        self.length_edit.textChanged.connect(self.update_scaling)

        scaling = QHBoxLayout()
        scaling.addWidget(self.pixel_edit)
        scaling.addWidget(QLabel("px    :  "))
        scaling.addWidget(self.length_edit)
        self.units_dd = QComboBox()
        self.units_dd.addItems(self.data_handler.units.keys())
        # setting for default unit
        self.units_dd.setCurrentIndex(3)
        self.units_dd.currentTextChanged.connect(self.units_changed)
        scaling.addWidget(self.units_dd)


        self.scaling_layout.addLayout(scaling)
        self.scaling_box.setLayout(self.scaling_layout)
        self.layout.addWidget(self.scaling_box)


        # selected object
        self.selected_object_box = QGroupBox("Selected Object", self)
        self.selected_object_layout = QVBoxLayout()
        
        self.structure_edit = QLineEdit(self, placeholderText="Enter structure name")
        self.selected_object_layout.addWidget(self.structure_edit)

        self.selected_object_table = QTableWidget()
        self.selected_object_table.setRowCount(0)

        self.selected_object_table.setColumnCount(5)
        # do not hide for column headers
        self.selected_object_table.horizontalHeader().hide()
        self.selected_object_table.verticalHeader().hide()
        self.selected_object_table.resizeColumnsToContents()
        self.selected_object_table.horizontalHeader().setStretchLastSection(True)



        self.selected_object_layout.addWidget(self.selected_object_table)
        self.selected_object_box.setLayout(self.selected_object_layout)
        self.layout.addWidget(self.selected_object_box)

        # add empty space
        self.layout.addStretch(1)

        # Save


        self.openSaveWindow = QPushButton("Save", self)
        self.layout.addWidget(self.openSaveWindow)
        self.openSaveWindow.clicked.connect(self.open_save_window)
        
        self.setLayout(self.layout)
    
    def select_sem_file(self, file_path=None):
        if file_path is None:
            file_path = self.openFileNameDialog()
        if file_path:
            file_path = Path(file_path)
            
            # check if some measurements will be overwritten
            if self.data_handler.drawing_data:
                # ask for deletion of drawing data
                reply = QMessageBox.warning(self, "Warning",
                    "Do you want to load a new image?\n\nThis might replace the current image and remove the measurements.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)

                # if we want to overwrite the data, otherwise do nothing
                if reply == QMessageBox.StandardButton.Yes:
                    self.data_handler.delete_all_objects()
                    
                    self.data_handler.open_file(file_path, self.vispy_canvas_wrapper)
            
            # just do it if there is no measurement data
            else:
                self.data_handler.open_file(file_path, self.vispy_canvas_wrapper)
                

    def openFileNameDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self,"Select SEM Image", "","All Files (*);;Python Files (*.py)")
        if fileName:
            return fileName
        
    def raise_error(self, error):        
        msg = QMessageBox.critical(None, "Error", str(error))

    def open_save_window(self):
        if not self.vispy_canvas_wrapper.start_state:
            self.save_window = SaveWindow(parent=self)
            self.save_window.show()

    def automatic_scaling(self):
        #only when image is loaded
        if not self.vispy_canvas_wrapper.start_state:
            # get seedPoint from sem_db
            try:
                seed_point = self.data_handler.sem_db[self.dd_select_sem.currentText()]['SeedPoints']
                # only actually try to find scaling bar, when data is given by database
                if seed_point is not None:
                    self.vispy_canvas_wrapper.find_scaling_bar_width(seed_point)
            except:
                self.raise_error("Something went wrong when reading database:")            

    def update_scaling(self):
        length = self.length_edit.text()
        pixels = self.pixel_edit.text()
        if length != "" and pixels != "":
            self.scaling = float(length.replace(',',''))/float(pixels.replace(',',''))
        else:
            self.scaling = 1
        self.units_changed()


    def units_changed(self):
        self.selected_object_table.setHorizontalHeaderItem(1, 
                            QTableWidgetItem(self.units_dd.currentText()))
        self.vispy_canvas_wrapper.selection_update()
         