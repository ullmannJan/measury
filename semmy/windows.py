# absolute imports
import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QComboBox,\
      QListWidget, QTableWidget, QTableWidgetItem
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

        # structure drop down
        self.dd_select_object = QComboBox(self)
        self.update_drop_down()
        self.layout.addWidget(self.dd_select_object)
        
        # object list
        self.object_list = QListWidget()
        if self.dd_select_object.currentText() != "":
            objects = self.parent.data_handler.output_data[self.dd_select_object.currentText()]
            types = [type(obj).__name__ for obj in objects]
            self.object_list.insertItems(0, types)
        self.dd_select_object.currentTextChanged.connect(self.drop_down_changed)
        self.layout.addWidget(self.object_list)

        # data table
        self.object_data_table = QTableWidget()
        self.object_data_table.setRowCount(0)
        self.object_data_table.setColumnCount(5)
        self.object_data_table.horizontalHeader().hide()
        self.object_data_table.verticalHeader().hide()
        self.object_data_table.resizeColumnsToContents()
        self.object_data_table.horizontalHeader().setStretchLastSection(True)
        
        if self.dd_select_object.currentText() != "" and self.object_list.currentItem() is not None:
            self.object_data_list.insertItems(0, types)

        self.object_list.currentItemChanged.connect(self.list_item_changed)
        self.layout.addWidget(self.object_data_table)

    def drop_down_changed(self):
        self.update_object_list()

    def list_item_changed(self):
        self.update_object_data_table()
    
    def update_drop_down(self, structure=None):
        self.dd_select_object.clear()
        self.dd_select_object.addItems(self.parent.data_handler.output_data.keys())
        # if structure is not None:
        #     if structure in [self.dd_select_object.itemText(i) for i in range(self.dd_select_object.count())]:
        #         self.dd_select_object.setCurrentText(structure)

    def update_object_list(self, list_index=None):
        self.object_list.clear()

        if self.dd_select_object.currentText() != "" and \
           self.dd_select_object.currentText() is not None:

            objects = self.parent.data_handler.output_data[self.dd_select_object.currentText()]
            types = [type(obj).__name__ for obj in objects]
            self.object_list.insertItems(0, types)
        
        if list_index is not None:
            if list_index < len(self.object_list.items()):
                self.object_list.setCurrentIndex(list_index)

    def update_object_data_table(self):
        
        self.object_data_table.clearContents()
        self.object_data_table.setRowCount(0)
        if self.dd_select_object.currentText() != "" and self.object_list.currentItem() != None:
            object = self.parent.data_handler.output_data[self.dd_select_object.currentText()][self.object_list.currentRow()]
            props = object.output_properties()
            self.object_data_table.setRowCount(len(props.keys()))

            for i, key in enumerate(props):
                self.object_data_table.setItem(i, 0, 
                                    QTableWidgetItem(key))
                
                value, unit = props[key]
                # if there is a conversion possible
                if self.parent.scaling != 1 :
                    scaled_length = 1 * np.array(value)
                    if key in ['length', 'area', 'radius', 'width', 'height', 'center']:
                        scaled_length *= self.parent.scaling
                        exponent = unit[-1] if unit[-1] in ['²', '³'] else ""
                        self.object_data_table.setItem(i, 2, 
                                QTableWidgetItem(self.parent.units_dd.currentText()+exponent))
                    else:
                        self.object_data_table.setItem(i, 2, 
                                QTableWidgetItem(unit))
                    self.object_data_table.setItem(i, 1, 
                                QTableWidgetItem(str(scaled_length)))

                if True: # if setting selected that pixels should be shown too
                    self.object_data_table.setItem(i, 3, 
                                QTableWidgetItem(str(value)))
                    self.object_data_table.setItem(i, 4, 
                                QTableWidgetItem(unit))
            
        self.object_data_table.resizeColumnsToContents()
    

    def update_window(self):
        self.update_drop_down()
        self.update_object_list()
        self.update_object_data_table()

class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.layout.addWidget(QLabel(f"Semmy v{semmy_version}"))
