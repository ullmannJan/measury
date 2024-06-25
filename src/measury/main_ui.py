# absolute imports
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, \
        QPushButton, QTableWidget, QWidget, QFileDialog, QComboBox, QLabel, \
        QButtonGroup, QLineEdit, QGroupBox, QTableWidgetItem, QListWidget, \
        QInputDialog
from PyQt6.QtGui import QDoubleValidator
from pathlib import Path

# relative imports
from .windows import SaveWindow
from .data.microscopes import Microscope


class MainUI(QWidget):
    
    main_window = None
    
    def __init__(self, main_window, parent=None):
        
        self.parent = parent
        super().__init__(self.parent)

        self.main_window = main_window
        self.vispy_canvas = main_window.vispy_canvas
        self.data_handler = main_window.data_handler
        self.right_ui = main_window.right_ui

        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(175)

        # sem settings

        # image settings
        self.image_box = QGroupBox("Image Settings", self)
        self.image_layout = QVBoxLayout()

        self.select_image_button = QPushButton("Select File", self)
        self.image_layout.addWidget(self.select_image_button)
        
        self.select_image_button.clicked.connect(lambda : self.select_sem_file(file_path=None))

        self.center_image_button = QPushButton("Center Image", self)
        self.image_layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.vispy_canvas.center_image)

        self.image_box.setLayout(self.image_layout)
        self.layout.addWidget(self.image_box)
        

        # tools settings
        self.tools_edit_box = QGroupBox("Edit", self)
        self.tools_edit_layout = QHBoxLayout()
        self.tools_create_box = QGroupBox("Create", self)
        self.tools_create_layout = QHBoxLayout()
        self.tools_scaling_box = QGroupBox("Scaling", self)
        self.tools_scaling_layout = QVBoxLayout()
        
        
        tools_edit = dict()
        tools_edit['move'] = QPushButton("move", self)
        tools_edit['select'] = QPushButton("select", self)
        tools_edit['edit'] = QPushButton("edit", self)
        tools_create = dict()
        tools_create['line'] = QPushButton("line", self)
        tools_create['angle'] = QPushButton("angle", self)
        tools_create['rectangle'] = QPushButton("rectangle", self)
        tools_create['circle'] = QPushButton("circle", self)
        tools_scaling = dict()
        tools_scaling['scale'] = QPushButton("identify scaling", self)
        tools_scaling['scale'].clicked.connect(self.automatic_scaling)

        # merge dicts
        tools = tools_edit | tools_create | tools_scaling
        
        self.tools = QButtonGroup(self)

        for i, tool in enumerate(tools.values()):
            tool.setCheckable(True)
            self.tools.addButton(tool, id=i)
        self.tools.button(0).setChecked(True)
            
        for tool in tools_edit.values():
            self.tools_edit_layout.addWidget(tool)
        self.tools_edit_box.setLayout(self.tools_edit_layout)
        self.layout.addWidget(self.tools_edit_box)
        
        for tool in tools_create.values():
            self.tools_create_layout.addWidget(tool)
        self.tools_create_box.setLayout(self.tools_create_layout)
        self.layout.addWidget(self.tools_create_box)
        
        
        # select microscope
        select_sem_layout = QHBoxLayout()
        self.sem_label = QLabel("Select Microscope:", self)
        select_sem_layout.addWidget(self.sem_label)

        self.dd_select_sem = QComboBox(self)
        self.dd_select_sem.addItems(self.data_handler.sem_db.keys())
        self.dd_select_sem.setCurrentText(self.main_window.settings.value("ui/microscope"))
        select_sem_layout.addWidget(self.dd_select_sem)
        self.tools_scaling_layout.addLayout(select_sem_layout)
        
        scaling_vertical_layout = QHBoxLayout()
        self.scaling_direction_dd = QComboBox(self)
        self.scaling_direction_dd.addItems(['horizontal', 'vertical'])
        scaling_vertical_layout.addWidget(self.scaling_direction_dd)
        scaling_vertical_layout.addWidget(tools_scaling['scale'])
        self.tools_scaling_layout.addLayout(scaling_vertical_layout)
        
        self.tools_scaling_box.setLayout(self.tools_scaling_layout)
        self.layout.addWidget(self.tools_scaling_box)
        self.tools_scaling_box.setLayout(self.tools_scaling_layout)

        # scaling

        self.scaling = 1.
        
        posDouble = QDoubleValidator()
        posDouble.setBottom(0)
        # posInt = QIntValidator()
        # posInt.setBottom(0)
        self.pixel_edit = QLineEdit(self, placeholderText="Enter value")
        self.pixel_edit.setValidator(posDouble)
        self.pixel_edit.textChanged.connect(self.update_scaling)
        self.length_edit = QLineEdit(self, placeholderText="Enter value")
        self.length_edit.setValidator(posDouble)
        self.length_edit.textChanged.connect(self.update_scaling)

        scaling = QHBoxLayout()
        scaling.addWidget(self.pixel_edit)
        scaling.addWidget(QLabel("px    :  "))
        scaling.addWidget(self.length_edit)
        
        self.units_dd = QComboBox()
        self.units_dd.setEditable(True)
        self.units_dd.addItems(self.data_handler.units.keys())
        # setting for default unit
        self.units_dd.setCurrentIndex(3)
        self.units_dd.currentTextChanged.connect(self.units_changed)
        scaling.addWidget(self.units_dd)
        
        self.tools_scaling_layout.addLayout(scaling)
        self.tools_scaling_box.setLayout(self.tools_scaling_layout)
        self.layout.addWidget(self.tools_scaling_box)

        # visibility settings
        self.visibility_box = QGroupBox("Visibility", self)
        self.visibility_layout = QHBoxLayout()
        self.visibility_box.setLayout(self.visibility_layout)
        self.layout.addWidget(self.visibility_box)

        self.visibility_button = QPushButton("Show all", self)
        self.visibility_button.clicked.connect(self.vispy_canvas.show_all_objects_w_undo)
        self.visibility_layout.addWidget(self.visibility_button)

        self.visibility_button = QPushButton("Hide all", self)
        self.visibility_button.clicked.connect(self.vispy_canvas.hide_all_objects_w_undo)
        self.visibility_layout.addWidget(self.visibility_button)

        # selected object
        self.selected_object_box = QGroupBox("Selected Object", self)
        self.selected_object_layout = QVBoxLayout()
        
        self.selected_structure_layout = QHBoxLayout()
        
        self.structure_dd = QComboBox(self)
        self.structure_dd.setEditable(True)
        self.structure_dd.setPlaceholderText("Enter structure name")
        self.structure_dd.currentTextChanged.connect(self.structure_dd_changed)
        self.selected_structure_layout.addWidget(self.structure_dd)
        
        # rename button
        self.rename_button = QPushButton("Rename Structure")
        self.rename_button.clicked.connect(self.rename_structure)
        self.selected_structure_layout.addWidget(self.rename_button)
        self.selected_object_layout.addLayout(self.selected_structure_layout)
        
        # object list
        self.object_list = QListWidget()
        self.object_list.itemClicked.connect(self.list_object_selected)
        self.selected_object_layout.addWidget(self.object_list)

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
        self.layout.addStretch()

        # Overview
        self.openSaveWindow = QPushButton("Show Measurements", self)
        self.layout.addWidget(self.openSaveWindow)
        self.openSaveWindow.clicked.connect(self.parent.open_data_page)

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
                    
            self.data_handler.open_file(file_path, self.vispy_canvas)
            
    def openFileNameDialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self,"Select Image", "","All Files (*);;Python Files (*.py)")
        if file_name:
            return file_name

    def open_save_window(self):
        if not self.vispy_canvas.start_state:
            self.save_window = SaveWindow(parent=self)
            self.save_window.show()

    def get_microscope(self) -> Microscope:
        return self.data_handler.sem_db[self.dd_select_sem.currentText()]()

    def automatic_scaling(self):
        #only when image is loaded
        if not self.vispy_canvas.start_state:
            # get seedPoint from sem_db
            try:
                seed_points = self.get_microscope().seed_points
                orientation = self.get_microscope().orientation
                if orientation is not None:
                    self.scaling_direction_dd.setCurrentText(orientation)
                # only actually try to find scaling bar, when data is given by database
                if seed_points is not None:
                    threshold = self.get_microscope().threshold
                    self.vispy_canvas.find_scale_bar_width_w_undo(seed_point_percentage=seed_points, 
                                                                  threshold=threshold)
            except Exception as e:
                self.main_window.raise_error("Something went wrong while trying to identify scaling bar: "+ str(e))            

    def update_scaling(self):
        length = self.length_edit.text()
        pixels = self.pixel_edit.text()
        if length != "" and pixels != "":
            self.scaling = float(length.replace(',',''))/float(pixels.replace(',',''))
        else:
            self.scaling = 1
        self.units_changed()
    
    def reset_scaling(self):
        self.units_dd.setCurrentIndex(3)
        self.pixel_edit.setText("")
        self.length_edit.setText("")
        self.units_changed()
        
    def units_changed(self):
        self.selected_object_table.setHorizontalHeaderItem(1, 
                            QTableWidgetItem(self.units_dd.currentText()))
        self.vispy_canvas.selection_update()
        
    def update_structure_dd(self):
        self.structure_dd.clear()
        if self.data_handler.drawing_data.keys():
            self.structure_dd.addItems(sorted(self.data_handler.drawing_data.keys()))
            self.structure_dd.setCurrentIndex(0)
            
        self.structure_dd_changed()
        
    def add_to_structure_dd(self, name):
        if name not in [self.structure_dd.itemText(i) for i in range(self.structure_dd.count())]:
            self.structure_dd.addItem(name)
        
        self.structure_dd.setCurrentText(name)
        
    def remove_from_structure_dd(self, name):
        names = [self.structure_dd.itemText(i) for i in range(self.structure_dd.count())]
        if name in names:
            self.structure_dd.removeItem(names.index(name))
            self.structure_dd.setCurrentIndex(0) 
            
    def structure_dd_changed(self):
        self.update_object_list()
        
        
    def update_object_list(self):
        self.object_list.clear()
        if self.structure_dd.currentText() != "":
            if self.structure_dd.currentText() in self.data_handler.drawing_data:
                objects = self.data_handler.drawing_data[self.structure_dd.currentText()]
                types = [type(obj).__name__ for obj in objects]
                self.object_list.insertItems(0, types)
            
    def clear_object_table(self):
        self.selected_object_table.clearContents()
        self.selected_object_table.setRowCount(0)
        
    def list_object_selected(self):
        
        structure = self.structure_dd.currentText()
        index = self.object_list.currentRow()
        
        object = self.data_handler.drawing_data[structure][index]
        self.vispy_canvas.select(object)
        
    def rename_structure(self):
        structure = self.structure_dd.currentText()
        
        if structure:
            
            new_structure, ok = QInputDialog.getText(self, "Rename",
                                    f"Do you want to rename the structure: {structure}?\n",
                                    text=structure)
            if ok:
                # After the user closes the QInputDialog, you can get the text from the QLineEdit
                status = self.data_handler.rename_structure(structure, new_structure)
                if status:
                    self.update_structure_dd()
                    self.structure_dd.setCurrentText(new_structure)
                    self.structure_dd_changed()
        