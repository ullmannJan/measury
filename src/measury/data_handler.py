# absolute imports
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QGuiApplication, QUndoCommand
import pickle
from os import startfile
from subprocess import Popen
from sys import platform
from copy import deepcopy
import logging
import numpy as np  
import cv2

# you need this import as they are implicitly used
from .drawable_objects import EditRectVisual, EditLineVisual, EditEllipseVisual
from .data.microscopes import load_microscopes


class DataHandler:
    img_data = None
    img_byte_stream = None
    file_path: Path | None = None

    main_window: dict | None = None
    drawing_data: dict

    units: dict
    logger: logging.Logger | None = None
    
    file_extensions = ('.msry', '.measury')

    # database (dict) of sems with points in scaling bar
    def __init__(self, logger=None):

        self.sem_db = load_microscopes()
            
        if logger is not None:
            self.logger = logger
        else:
            logging.basicConfig(level=logging.CRITICAL,
                                format='%(asctime)s  %(levelname)-10s %(name)s: %(message)s')
            self.logger = logging.getLogger("Measury")
            self.logger.setLevel(logging.CRITICAL)

        # drawing data is a dictionary of the form:
        # {
        #   'object 1': [measured_line, measured_line, ...],
        #   'object 2': [measured_circle, measured_circle, ...],
        #   ...
        # }
        self.drawing_data = dict()
        self.units = dict(fm=1e-15, pm=1e-12, Å=1e-10, 
                          nm=1e-9, µm=1e-6, mm=1e-3, 
                          cm=1e-2, m=1, km=1e3, )

    def save_object(self, structure_name, object):
        """save object into storage structure

        Args:
            structure_name (string): _description_
            object_data (_type_): _description_
        """
        if structure_name == "" or structure_name.isspace():
            structure_name = self.generate_output_name()

        # if not in output dict then add an empty list
        if structure_name not in self.drawing_data.keys():
            self.drawing_data[structure_name] = list()
        self.drawing_data[structure_name].append(object)
        self.logger.info(f"object {object} saved in {structure_name} in drawing_data")
        
        return structure_name

    def delete_object(self, object):
        """delete object from the storage dict

        Args:
            object_data (class:object): the object that should be deleted
        """
        for object_name, object_list in list(self.drawing_data.items()):
            if object in object_list:
                object_list.remove(object)
            # in case it is the controlpoints
            if object.parent in object_list:
                object_list.remove(object.parent)
                object = object.parent
            # If the list is empty after removal, delete the key from the dictionary
            if not object_list:
                self.main_window.main_ui.remove_from_structure_dd(object_name)
                del self.drawing_data[object_name]
                if self.main_window.main_ui.structure_dd.currentText() == object_name:
                    self.main_window.main_ui.structure_dd.setCurrentText("")
            
    def delete_all_objects(self):
        self.main_window.vispy_canvas.unselect()
        for structure_list in list(self.drawing_data.values()):
            for object in structure_list:
               object.delete()
            
        self.drawing_data = dict()
        self.main_window.main_ui.update_structure_dd()
        self.logger.info("Deleted all measurements")
        
    def delete_all_objects_w_undo(self):
        command = DeleteAllObjectsCommand(self)
        self.main_window.undo_stack.push(command)
        
    def find_object(self, object):
        if self.drawing_data:
            for k, val in self.drawing_data.items():
                if object in val:
                    return k, val.index(object)
            raise LookupError("Object could not be found in drawing_data")
    

    def generate_output_name(self):
        # return string that is not in the drawing_data keys and increases each time
        i = 1
        while f"structure_{i:03d}" in self.drawing_data.keys():
            i += 1
        return f"structure_{i:03d}"
    
    
    def open_file_location(self, path: Path):
        try:
            if path is not None:
            
                if platform == "win32":
                    # For Windows
                    startfile(path.parent)
                elif platform == "darwin":
                    # For MacOS
                    Popen(["open", str(path.parent)])
                else:
                    # For Linux
                    Popen(["xdg-open", str(path.parent)])
        except Exception as error:
            self.logger.warning(f"Could not open file location: {path.parent}:\n{error}")
            self.main_window.raise_error(f"Could not open file location: {path.parent}")

    def save_file_dialog(self, file_name="measury.msry", extensions="Measury Files (*.measury *.msry)"):
        filename, _ = QFileDialog.getSaveFileName(self.main_window.main_ui, 
                                                "Save", 
                                                file_name, 
                                                extensions)
        if filename:
            return filename
        
    def save_storage_file(self, save_image=True, **kwargs):
        
        filename = self.save_file_dialog(file_name=str(self.file_path.with_suffix('.msry')))
        if filename is None:
            return
        
        structure_data = dict()
        for key, val in self.drawing_data.items():
            structure_data[key] = [[obj.__class__, deepcopy(obj.save())] for obj in val]
        
        if save_image:
            scaling = (self.main_window.main_ui.pixel_edit.text(), 
                        self.main_window.main_ui.length_edit.text(), 
                        self.main_window.main_ui.units_dd.currentText())
            output = (self.img_byte_stream, structure_data, scaling)
        else:
            output = (None, structure_data, None)
        with open(filename, 'wb') as save_file:
            pickle.dump(output, save_file, pickle.HIGHEST_PROTOCOL, **kwargs)

        
    def load_into_view(self, drawing_data, vispy_instance):
        """
        Loads the drawing data into the view and the drawing_data dictionary.

        Args:
            drawing_data (dict): A dictionary containing the drawing data.
            vispy_instance: An instance of the Vispy class.

        Returns:
            None
        """
        self.delete_all_objects()
        self.drawing_data = drawing_data
        self.logger.info("loading drawing data into view and into drawing_data")
        if drawing_data:
            for val in drawing_data.values():
                for object in val:
                    object.parent = vispy_instance.view.scene
                
        
    def load_storage_file(self, file_path, vispy_instance):
        """load .msry data from a file and update the view

        """


        with open(file_path, 'rb') as file:
            
            self.logger.info(f"opened file: {file_path}")
            loaded_data = pickle.load(file)
            scaling = (None, None, None)
            if len(loaded_data) == 2:
                img_byte_stream, structure_data = loaded_data
            elif len(loaded_data) == 3:
                img_byte_stream, structure_data, scaling = loaded_data
            
            reply = QMessageBox.StandardButton.Yes
            question = None
            
            if self.img_data is None and img_byte_stream is None:
                self.main_window.raise_error("You can't load measurements without loading an image first.")
                return
            
            # there is an image with measurements
            if self.drawing_data and self.img_data is not None:
                if img_byte_stream is None:
                    if structure_data:
                        # only measurments / no image
                        question = "Do you want to load new measurements?\n\nThis will remove the current measurements."  
                    else:
                        # if the file is empty
                        return 
                else:
                    # image included
                    if structure_data:
                        question = "Do you want to load a new image with other measurements?\n\nThis will replace the current image and measurements."
                    else:     
                        question = "Do you want to load a new image?\n\nThis will replace the current image and remove the measurements."
            
            if question is not None:
                reply = QMessageBox.warning(self.main_window.main_ui, "Warning",
                        question,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
            
            if reply is QMessageBox.StandardButton.Yes:
                
                self.delete_all_objects()
                self.file_path = file_path
                if img_byte_stream is not None:
                    if isinstance(img_byte_stream, bytes):
                        self.img_byte_stream = img_byte_stream
                    else: # for old file format where just the pixel matrix is stored
                        # Step 1: Encode the image data to a specific format
                        self.logger.warning("old file format detected")
                        success, encoded_image = cv2.imencode('.png', 
                                                            img_byte_stream, 
                                                            [int(cv2.IMWRITE_PNG_COMPRESSION), 5])

                        if success:
                            # Step 2: Convert the encoded image to a byte stream
                            self.img_byte_stream = encoded_image.tobytes()
                            
                    self.logger.debug("set data_handler.img_byte_stream to loaded file data")
                    vispy_instance.update_image()
                
                if structure_data:
                    for key, val in structure_data.items():
                        for obj_type, obj_data in val:
                            new_object = obj_type(settings=self.main_window.settings, **obj_data, parent=vispy_instance.view.scene)
                            vispy_instance.create_new_object(new_object, structure_name=key)                    
                
                if scaling[0] is not None:
                    self.main_window.main_ui.pixel_edit.setText(str(scaling[0]))
                    self.main_window.main_ui.length_edit.setText(str(scaling[1]))
                    # find the index of the unit in the dropdown and set it
                    index = self.main_window.main_ui.units_dd.findText(scaling[2])
                    if index == -1:
                        self.main_window.main_ui.units_dd.addItem(scaling[2])
                        self.main_window.main_ui.units_dd.setCurrentIndex(self.main_window.main_ui.units_dd.count()-1)
                    else:
                        self.main_window.main_ui.units_dd.setCurrentIndex(index)
                    self.main_window.main_ui.units_changed()
                
                self.main_window.main_ui.update_structure_dd()           
    
    def open_file(self, file_path: str|Path|None, vispy_instance):
        
        try:
            if file_path:
                file_path = Path(file_path)
                
                if file_path.suffix in self.file_extensions:
                    self.load_storage_file(file_path, vispy_instance=vispy_instance)
                
                else:
                    reply = QMessageBox.StandardButton.Yes
                    if self.img_data is not None:
                        reply = QMessageBox.warning(self.main_window.main_ui, "Warning",
                            "Do you want to load a new image?\n\nThis will replace the current image and remove the measurements.",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No)
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.file_path = file_path
                        self.img_byte_stream = file_path.read_bytes()
                        self.delete_all_objects()
                        self.main_window.main_ui.reset_scaling()
                        vispy_instance.update_image()
                        
        except Exception as error:
            self.logger.error(f"Could not open file: {file_path}:\n{error}")
            self.main_window.raise_error(f"Could not open file: {file_path}: {error}")

    def open_image_from_clipboard(self, vispy_instance):

        reply = QMessageBox.StandardButton.Yes
        try:
            if self.img_data is not None:
                reply = QMessageBox.warning(self.main_window.main_ui, "Warning",
                    "Do you want to load a new image?\n\nThis will replace the current image and remove the measurements.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.file_path = Path("clipboard")
                self.delete_all_objects()
                self.main_window.main_ui.reset_scaling()
                clipboard = QGuiApplication.clipboard()
                
                clipboard_data = clipboard.image()
                width = clipboard_data.width()
                height = clipboard_data.height()
                # Get the pointer to the pixel data
                ptr = clipboard_data.constBits()
                ptr.setsize(height * width * 4)

                # Convert the pixel data to a byte stream
                img_data = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))

                # Step 1: Encode the image data to a specific format (e.g., '.png')
                success, encoded_image = cv2.imencode('.png', 
                                                      img_data, 
                                                      [int(cv2.IMWRITE_PNG_COMPRESSION), 5])

                if success:
                    # Step 2: Convert the encoded image to a byte stream
                    self.img_byte_stream = encoded_image.tobytes()
                            
                    vispy_instance.update_image()
                else:
                    raise Exception("Could not encode image data")
                
        except Exception as error:
            self.logger.error(f"Could not open from clipboard:\n{error}")
            self.main_window.raise_error(f"Could not open from clipboard: {error}")
            
    def calculate_results(self):
        """calculate the average and standard deviation of 
        the measurements for each structure in drawing_data
        """

        results = dict()
        for structure_name, object_list in self.drawing_data.items():
            results[structure_name] = dict()
            props = object_list[0].output_properties().keys()
            for prop in props:
                data = [obj.output_properties()[prop][0] for obj in object_list]
                unit = object_list[0].output_properties()[prop][1]
                if self.main_window.main_ui.scaling != 1 :
                    if prop in ['length', 'area', 'radius', 'width', 'height', 'center']:
                        data = [d*self.main_window.main_ui.scaling for d in data]
                        exponent = unit[-1] if unit[-1] in ['²', '³'] else ""
                        unit = self.main_window.main_ui.units_dd.currentText() + exponent
                
                if len(data) == 1:
                    results[structure_name][prop] = (np.mean(data), None, unit)
                else:
                    results[structure_name][prop] = (np.mean(data),np.std(data)/np.sqrt(len(object_list)), unit)
        return results
    
    def calculate_results_string(self):
        results = self.calculate_results()
        # sort dict
        results = dict(sorted(results.items()))
        results_string = ""
        for structure_name, structure_results in results.items():
            results_string += f"{structure_name}:\n"
            for prop, prop_results in structure_results.items():
                results_string += f"\t{prop}:\t "
                # value with or without std
                value_str = f"{prop_results[0]:.1f}"
                if prop_results[1] is not None:
                    value_str = f"({value_str} ± {prop_results[1]:.1f})"
                results_string += value_str
                # adding unit
                results_string += f" {prop_results[2]}\n"
            results_string += "\n"
        return results_string
    
    def save_measurements_file(self):
        filename = self.save_file_dialog(file_name=str(self.file_path.with_suffix('.meas')),extensions="Measurement File (*.meas)")
        if filename is None:
            return
        
        with open(filename, 'wb') as save_file:
            # write to text file
            save_file.write(self.calculate_results_string().encode('utf-8'))
            
    def rename_structure(self, structure, new_structure):
        if new_structure in self.drawing_data:
            self.main_window.raise_error("This structure already exists!")
        elif new_structure == "" or new_structure.isspace():
            self.main_window.raise_error("This name is not valid")
        else:
            self.drawing_data[new_structure] = self.drawing_data[structure] 
            del self.drawing_data[structure]
            return True
        
        return False
    
    
class DeleteAllObjectsCommand(QUndoCommand):
    def __init__(self, data_handler: DataHandler):
        super().__init__()
        self.data_handler = data_handler
        self.main_window = self.data_handler.main_window
        self.old_drawing_data = dict(data_handler.drawing_data)  # Save the old state

    def undo(self):
        # Restore the old state
        self.data_handler.logger.info("Undoing delete all objects")
        self.data_handler.drawing_data = self.old_drawing_data
        self.main_window.main_ui.update_structure_dd()
        self.data_handler.load_into_view(self.data_handler.drawing_data, 
                                         self.main_window.vispy_canvas)
        self.data_handler.logger.info("Restored all measurements")

    def redo(self):
        # Delete all objects
        self.data_handler.delete_all_objects()

    