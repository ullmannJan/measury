# absolute imports
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, \
        QPushButton, QTableWidget, QWidget, QFileDialog, QComboBox, QLabel, \
        QButtonGroup, QLineEdit, QGroupBox, QTableWidgetItem
from PyQt6.QtGui import QDoubleValidator, QIntValidator

# relative imports
from .windows import OutputWindow
from .vispy_canvas import VispyCanvas

class MainUI(QWidget):
    
    def __init__(self, vispy_canvas_wrapper: VispyCanvas, data_handler, parent=None):
        

        super().__init__(parent)

        self.vispy_canvas_wrapper = vispy_canvas_wrapper
        self.data_handler = data_handler

        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(175)

        # sem settings
        self.sem_label = QLabel("Select SEM", self)
        self.layout.addWidget(self.sem_label)

        self.dd_select_sem = QComboBox(self)
        self.dd_select_sem.addItems(self.data_handler.sem_db.keys())
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

        # Output
        self.output_box = QGroupBox("Output", self)
        self.output_layout = QVBoxLayout()

        self.structure_edit = QLineEdit(self, placeholderText="Enter structure name")
        self.output_layout.addWidget(self.structure_edit)
        # Needs change
        self.structure_edit.textChanged.connect(self.update_output_window)

        self.openOutputWindow = QPushButton("Open Output Window", self)
        self.output_layout.addWidget(self.openOutputWindow)
        self.openOutputWindow.clicked.connect(self.open_output_window)

        self.output_box.setLayout(self.output_layout)
        self.layout.addWidget(self.output_box)
        
        self.setLayout(self.layout)
    
    def select_sem_file(self):
        self.data_handler.img_path = self.openFileNameDialog()
        self.vispy_canvas_wrapper.update_image()

    def openFileNameDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self,"Select SEM Image", "","All Files (*);;Python Files (*.py)")
        if fileName:
            return fileName
        
    def raise_error(self, error):        
        msg = QMessageBox.critical(None, "Error", str(error))

    def open_output_window(self):
        self.output_window = OutputWindow(parent=self)
        self.output_window.show()

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

    # Needs change
    def update_output_window(self):
        if hasattr(self, 'output_window'):
            self.output_window.update_window()


    def units_changed(self):
        self.selected_object_table.setHorizontalHeaderItem(1, 
                            QTableWidgetItem(self.units_dd.currentText()))
        self.vispy_canvas_wrapper.selection_update()
        # Needs change
        if hasattr(self, 'output_window'):
            self.output_window.update_object_data_table()
         