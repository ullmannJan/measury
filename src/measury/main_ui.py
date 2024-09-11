# absolute imports
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QWidget,
    QFileDialog,
    QComboBox,
    QLabel,
    QButtonGroup,
    QLineEdit,
    QGroupBox,
    QTableWidgetItem,
    QListWidget,
    QInputDialog,
    QHeaderView,
)
from PySide6.QtGui import (QIntValidator, 
                           QDoubleValidator,
                           QRegularExpressionValidator,
                           QFontMetrics, 
                           QUndoCommand,
                           )
from PySide6.QtCore import Qt, QLocale
from pathlib import Path
import numpy as np
import re

# relative imports
from .windows import SaveWindow
from .data.microscopes import Microscope


class MainUI(QWidget):

    main_window = None
    update_full_table = False
    DEFAULT_THRESHOLD = 10

    def __init__(self, main_window, parent=None):

        self.parent = parent
        super().__init__(self.parent)

        self.main_window = main_window
        self.vispy_canvas = main_window.vispy_canvas
        self.data_handler = main_window.data_handler
        self.right_ui = main_window.right_ui

        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(250)

        # image settings
        self.image_box = QGroupBox("Image Settings", self)
        self.image_layout = QHBoxLayout()

        # self.select_image_button = QPushButton("Select File", self)
        # self.image_layout.addWidget(self.select_image_button)
        # self.select_image_button.clicked.connect(
        #     lambda: self.select_file(file_path=None)
        # )

        self.center_image_button = QPushButton("Center Image", self)
        self.image_layout.addWidget(self.center_image_button)
        self.center_image_button.clicked.connect(self.vispy_canvas.center_image)
        
        self.rotate_image_button = QPushButton("Rotate Image", self)
        self.image_layout.addWidget(self.rotate_image_button)
        self.rotate_image_button.clicked.connect(self.vispy_canvas.rotate_image_w_undo)

        image_tools = dict()
        image_tools["set_origin"] = QPushButton("Set Origin", self)
        self.image_layout.addWidget(image_tools["set_origin"])

        self.image_box.setLayout(self.image_layout)
        self.layout.addWidget(self.image_box)

        # tools settings
        self.tools_edit_box = QGroupBox("Edit", self)
        self.tools_edit_layout = QHBoxLayout()
        self.tools_create_box = QGroupBox("Create", self)
        self.tools_create_layout = QVBoxLayout()
        self.tools_scaling_box = QGroupBox("Scaling", self)
        self.tools_scaling_layout = QVBoxLayout()

        tools_edit = dict()
        tools_edit["move"] = QPushButton("Move", self)
        tools_edit["select"] = QPushButton("Select", self)
        tools_edit["edit"] = QPushButton("Edit", self)
        tools_create = dict()
        tools_create["line"] = QPushButton("Line", self)
        tools_create["angle"] = QPushButton("Angle", self)
        tools_create["multi-line"] = QPushButton("Multi-Line", self)
        tools_create["rectangle"] = QPushButton("Rectangle", self)
        tools_create["ellipse"] = QPushButton("Ellipse", self)
        tools_create["polygon"] = QPushButton("Polygon", self)
        tools_scaling = dict()
        tools_scaling["scale"] = QPushButton("Identify Scaling", self)
        tools_scaling["scale"].clicked.connect(self.automatic_scaling)

        # merge dicts
        self.tools = tools_edit | tools_create | tools_scaling | image_tools

        # create button group
        self.tools_buttons = QButtonGroup(self)
        for i, tool in enumerate(self.tools.values()):
            tool.setCheckable(True)
            self.tools_buttons.addButton(tool, id=i)
        self.tools_buttons.button(0).setChecked(True)

        # create edit layout
        for tool in tools_edit.values():
            self.tools_edit_layout.addWidget(tool)
        self.tools_edit_box.setLayout(self.tools_edit_layout)
        self.layout.addWidget(self.tools_edit_box)

        tools_create_list = tools_create.values()
        # create 3 columns for the create tools
        for i, t in enumerate(tools_create_list):
            if i % 3 == 0:
                tools_create_layout = QHBoxLayout()
                self.tools_create_layout.addLayout(tools_create_layout)
            tools_create_layout.addWidget(t)
        self.tools_create_box.setLayout(self.tools_create_layout)
        self.layout.addWidget(self.tools_create_box)

        # select microscope
        select_micop_layout = QHBoxLayout()
        self.micop_label = QLabel("Select Microscope:", self)
        select_micop_layout.addWidget(self.micop_label)

        self.dd_select_micop = QComboBox(self)
        self.dd_select_micop.addItems(self.data_handler.micros_db.keys())
        self.dd_select_micop.setCurrentText(
            self.main_window.settings.value("ui/microscope")
        )
        self.dd_select_micop.currentTextChanged.connect(self.microscope_changed)
        select_micop_layout.addWidget(self.dd_select_micop)
        self.tools_scaling_layout.addLayout(select_micop_layout)

        scaling_vertical_layout = QHBoxLayout()
        self.scaling_direction_dd = QComboBox(self)
        self.scaling_direction_dd.addItems(["horizontal", "vertical"])
        scaling_vertical_layout.addWidget(self.scaling_direction_dd)
        
        threshold_label = "Threshold: "
        self.scaling_label = QLabel(threshold_label, self)
        self.scaling_label.setFixedWidth(QFontMetrics(self.scaling_label.font()).horizontalAdvance(threshold_label))
        scaling_vertical_layout.addWidget(self.scaling_label)
        
        self.scaling_threshold_edit = QLineEdit(self, placeholderText=str(self.DEFAULT_THRESHOLD))
        self.scaling_threshold_edit.setValidator(QIntValidator(0, 255, self))
        
        # Calculate the width required to display "255"
        font_metrics = QFontMetrics(self.scaling_threshold_edit.font())
        width = font_metrics.horizontalAdvance("255")*2  # Adding some padding
        self.scaling_threshold_edit.setFixedWidth(width)
        scaling_vertical_layout.addWidget(self.scaling_threshold_edit)
        
        scaling_vertical_layout.addWidget(tools_scaling["scale"])
        self.tools_scaling_layout.addLayout(scaling_vertical_layout)

        self.tools_scaling_box.setLayout(self.tools_scaling_layout)
        self.layout.addWidget(self.tools_scaling_box)
        self.tools_scaling_box.setLayout(self.tools_scaling_layout)

        # scaling

        self.scaling_factor = None
        posDouble_validator = QRegularExpressionValidator(r"^\+?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?")

        self.pixel_edit = QLineEdit(self, placeholderText="Enter value")
        self.pixel_edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.pixel_edit.setValidator(posDouble_validator)
        self.pixel_edit.textChanged.connect(self.update_scaling)
        self.length_edit = QLineEdit(self, placeholderText="Enter value")
        self.length_edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.length_edit.setValidator(posDouble_validator)
        self.length_edit.textChanged.connect(self.update_scaling)

        scaling = QHBoxLayout()
        scaling.addWidget(self.pixel_edit)
        scaling.addWidget(QLabel("px    :  "))
        scaling.addWidget(self.length_edit)

        self.units_dd = QComboBox()
        self.units_dd.setEditable(True)
        self.units_dd.addItems(self.data_handler.units.keys())
        # setting for default unit
        self.units_dd.setMinimumWidth(60)
        self.units_dd.setCurrentIndex(3)
        self.units_dd.currentTextChanged.connect(self.units_changed)
        scaling.addWidget(self.units_dd)

        self.tools_scaling_layout.addLayout(scaling)
        self.tools_scaling_box.setLayout(self.tools_scaling_layout)
        self.layout.addWidget(self.tools_scaling_box)

        # visibility settings
        # self.visibility_box = QGroupBox("Visibility", self)
        # self.visibility_layout = QHBoxLayout()
        # self.visibility_box.setLayout(self.visibility_layout)
        # self.layout.addWidget(self.visibility_box)

        # self.visibility_button = QPushButton("Show all", self)
        # self.visibility_button.clicked.connect(self.vispy_canvas.show_all_objects_w_undo)
        # self.visibility_layout.addWidget(self.visibility_button)

        # self.visibility_button = QPushButton("Hide all", self)
        # self.visibility_button.clicked.connect(self.vispy_canvas.hide_all_objects_w_undo)
        # self.visibility_layout.addWidget(self.visibility_button)

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
        self.rename_button.clicked.connect(self.rename_structure_ask)
        self.selected_structure_layout.addWidget(self.rename_button)
        self.selected_object_layout.addLayout(self.selected_structure_layout)

        # object list
        self.object_list = QListWidget()
        self.object_list.itemClicked.connect(self.list_object_selected)
        self.selected_object_layout.addWidget(self.object_list)

        self.selected_object_table = QTableWidget()
        # run, when cell content changes via GUI
        self.selected_object_table.itemChanged.connect(self.cell_content_changed)
        self.selected_object_table.setRowCount(0)
        self.set_selected_object_table_columns()

        #  disable changing
        # self.selected_object_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # do not hide for column headers
        self.selected_object_table.horizontalHeader().hide()
        self.selected_object_table.verticalHeader().hide()
        self.selected_object_table.resizeColumnsToContents()
        # self.selected_object_table.horizontalHeader().setStretchLastSection(True)
        self.selected_object_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        

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
        
    def set_selected_object_table_columns(self):
        if self.main_window.settings.value("ui/show_both_scaling", type=bool):
            self.selected_object_table.setColumnCount(5)
        else:
            self.selected_object_table.setColumnCount(3)

    def update_object_table(self, object=None):
        """This methods updates the object table with the properties of the selected object.

        Args:
            object: the selected object
        """
        if object is None:
            object = self.vispy_canvas.get_selected_object()
            
        # selection table
        self.clear_object_table()
        if object is None:
            return
        
        self.update_full_table = True # to prevent triggering cell_content_changed

        props = object.output_properties()
        self.selected_object_table.setRowCount(len(props.keys()))
        for i, key in enumerate(props):
            self.selected_object_table.setItem(i, 0, QTableWidgetItem(key))

            value, unit = props[key]
            # if there is a conversion possible
            if self.scaling_factor is not None:
                scaled_length = 1 * np.array(value)
                if key in ["length", "area", "radius", "width", "height", "center"]:
                    scaled_length *= self.scaling_factor
                    exponent = unit[-1] if unit[-1] in ["²", "³"] else ""
                    self.selected_object_table.setItem(
                        i, 2, QTableWidgetItem(self.units_dd.currentText() + exponent)
                    )
                else:
                    self.selected_object_table.setItem(i, 2, QTableWidgetItem(unit))
                self.selected_object_table.setItem(
                    i, 1, QTableWidgetItem(str(scaled_length))
                )
            else:  # to attach flags so you cant edit these columns
                self.selected_object_table.setItem(i, 1, QTableWidgetItem(str(value)))
                self.selected_object_table.setItem(i, 2, QTableWidgetItem(unit))

            # if setting selected that pixels should be shown too
            if self.main_window.settings.value("ui/show_both_scaling", type=bool) and self.scaling_factor is not None:
                self.selected_object_table.setItem(i, 3, QTableWidgetItem(str(value)))
                self.selected_object_table.setItem(i, 4, QTableWidgetItem(unit))
            else:
                self.selected_object_table.setItem(i, 3, QTableWidgetItem(""))
                self.selected_object_table.setItem(i, 4, QTableWidgetItem(""))

        self.selected_object_table.resizeColumnsToContents()
        # make only column 3 editable
        for i in range(self.selected_object_table.rowCount()):
            for j in range(self.selected_object_table.columnCount()):
                if j != 3 and j != 1:
                    item = self.selected_object_table.item(i, j)
                    if item:
                        item.setFlags(item.flags() & Qt.ItemFlag.ItemIsEnabled)

        self.update_full_table = False

    # Slot function that gets called when an item's content changes
    def cell_content_changed(self, item: QTableWidgetItem):
        # in case we update everything, we do not want to trigger this function
        if self.update_full_table:
            return

        # item is the QTableWidgetItem that was changed
        row, column = item.row(), item.column()
        new_value = item.text()

        sel_object = self.vispy_canvas.get_selected_object()
        obj_property = list(sel_object.output_properties().keys())[row]
        old_value = sel_object.output_properties()[obj_property][0]

        if isinstance(old_value, np.ndarray):
            old_type = old_value.dtype
            # load numpy array from string
            new_value = np.array(
                [float(val) for val in new_value.strip("[]").split(" ") if val],
                dtype=old_type,
            )
        else:
            old_type = type(old_value)
            new_value = old_type(new_value)

        # only allow changes in the data value columns
        # this is only the case if the setting for showing both scaling is enabled
        if column == 3:
            self.vispy_canvas.update_object_property_w_undo(
                sel_object, obj_property, new_value, 
                old_value=old_value
            )
        
        if column == 1:
            self.vispy_canvas.update_object_property_w_undo(
                sel_object, obj_property, new_value, 
                self.scaling_factor if self.scaling_factor is not None else 1, 
                old_value=old_value
            )
            

    def select_file(self, file_path=None):
        if file_path is None:
            file_path = self.openFileNameDialog()
        if file_path:
            file_path = Path(file_path)

            self.data_handler.open_file(file_path)

    def openFileNameDialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "All Files (*);;Python Files (*.py)"
        )
        if file_name:
            return file_name

    def open_save_window(self):
        if not self.vispy_canvas.start_state:
            self.save_window = SaveWindow(parent=self)
            self.save_window.show()

    def get_microscope(self) -> Microscope:
        return self.data_handler.micros_db[self.dd_select_micop.currentText()]()

    def automatic_scaling(self):
        # only when image is loaded
        if not self.vispy_canvas.start_state:
            # get seedPoint from micros_db
            try:
                seed_points = self.get_microscope().seed_points
                orientation = self.get_microscope().orientation
                if orientation is not None:
                    self.scaling_direction_dd.setCurrentText(orientation)
                # only actually try to find scaling bar, when data is given by database
                if seed_points is not None:
                    self.vispy_canvas.find_scale_bar_width_w_undo(
                        seed_point_percentage=seed_points, threshold=self.get_threshold(),
                        direction=self.scaling_direction_dd.currentText()
                    )
            except Exception as e:
                self.main_window.raise_error(
                    "Something went wrong while trying to identify scaling bar: "
                    + str(e)
                )

    def update_scaling(self):
        length = self.length_edit.text()
        pixels = self.pixel_edit.text()
        # add a zero to the end if the user enters 
        # "e" for scientific notation so that it still is a valid number
        # Regular expression to check if the number ends with 'e', 'e-', or 'e+'
        scientific_notation_pattern = re.compile(r'e[+-]?$')
        
        # Add a zero to the end if the user enters "e", "e-" or "e+" for scientific notation
        if scientific_notation_pattern.search(length.lower()):
            length += "0"
        if scientific_notation_pattern.search(pixels.lower()):
            pixels += "0"
    
        
        if length != "" and pixels != "":
            # American
            am_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
            length, _ = am_locale.toDouble(length)
            pixels, _ = am_locale.toDouble(pixels)
        
            self.scaling_factor = length / pixels            
        else:
            self.scaling_factor = None
        self.units_changed()

    def reset_scaling(self):
        self.units_dd.setCurrentIndex(3)
        self.pixel_edit.setText("")
        self.length_edit.setText("")
        self.units_changed()
        
    def microscope_changed(self):
        threshold = self.get_microscope().threshold
        self.set_threshold(threshold)
        
    def set_threshold(self, threshold):
        if threshold is None:
            self.scaling_threshold_edit.setText("")
        else:
            self.scaling_threshold_edit.setText(str(threshold))
        
    def get_threshold(self):
        threshold = self.scaling_threshold_edit.text()
        return int(threshold) if threshold else self.DEFAULT_THRESHOLD

    def units_changed(self):
        self.selected_object_table.setHorizontalHeaderItem(
            1, QTableWidgetItem(self.units_dd.currentText())
        )
        self.vispy_canvas.selection_update()
        self.right_ui.update_intensity_plot()

    def update_structure_dd(self):
        self.structure_dd.clear()
        if self.data_handler.drawing_data.keys():
            self.structure_dd.addItems(sorted(self.data_handler.drawing_data.keys()))
            self.structure_dd.setCurrentIndex(0)

        self.structure_dd_changed()

    def add_to_structure_dd(self, name):
        if name not in [
            self.structure_dd.itemText(i) for i in range(self.structure_dd.count())
        ]:
            self.structure_dd.addItem(name)

        self.structure_dd.setCurrentText(name)

    def remove_from_structure_dd(self, name):
        names = [
            self.structure_dd.itemText(i) for i in range(self.structure_dd.count())
        ]
        if name in names:
            self.structure_dd.removeItem(names.index(name))
            self.structure_dd.setCurrentIndex(0)

    def structure_dd_changed(self):
        self.update_object_list()

    def update_object_list(self):
        self.object_list.clear()
        if self.structure_dd.currentText() != "":
            if self.structure_dd.currentText() in self.data_handler.drawing_data:
                objects = self.data_handler.drawing_data[
                    self.structure_dd.currentText()
                ]
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

    def rename_structure_ask(self):
        structure = self.structure_dd.currentText()

        if structure:

            new_structure, ok = QInputDialog.getText(
                self,
                "Rename",
                f"Do you want to rename the structure: {structure}?\n",
                text=structure,
            )
            if ok:
                # After the user closes the QInputDialog, you can get the text from the QLineEdit
                self.rename_structure_w_undo(structure, new_structure)
                    
    def rename_structure(self, structure, new_structure):
        status = self.data_handler.rename_structure(structure, new_structure)
        if status:
            self.update_structure_dd()
            if self.structure_dd.currentText() == structure:
                self.structure_dd.setCurrentText(new_structure)
            self.structure_dd_changed()
            
    def rename_structure_w_undo(self, structure_name, new_structure_name):
        command = RenameStructureCommand(self,
                                         structure_name, new_structure_name)
        self.main_window.undo_stack.push(command)       

class RenameStructureCommand(QUndoCommand):
    def __init__(self, main_ui, structure_name, new_structure_name):
        super().__init__()
        self.main_ui = main_ui
        self.structure_name = new_structure_name
        self.old_structure_name = structure_name
        
    def undo(self):
        self.main_ui.data_handler.logger.debug(f"Undo rename structure: {self.structure_name} -> {self.old_structure_name}")
        self.main_ui.rename_structure(self.structure_name, self.old_structure_name)

    def redo(self):
        self.main_ui.data_handler.logger.debug(f"Redo rename structure: {self.old_structure_name} -> {self.structure_name}")
        self.main_ui.rename_structure(self.old_structure_name, self.structure_name)
