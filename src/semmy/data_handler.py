# absolute imports
from yaml import safe_load
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import pickle
from os import startfile
from subprocess import Popen
from sys import platform
from copy import deepcopy
import logging
from numpy import mean, std, sqrt

from . import semmy_path
# you need this as they are implicitly used
from .drawable_objects import EditRectVisual, EditLineVisual, EditEllipseVisual


class DataHandler:
    img_data = None
    file_path: Path | None = None

    main_ui: dict | None = None
    drawing_data: dict

    units: dict
    
    file_extensions = ('.sem', '.semmy')

    # database (dict) of sems with points in scaling bar
    def __init__(self):

        with open(semmy_path / Path("data/sem_db.yml"), "r", encoding='utf8') as file:
            self.sem_db = safe_load(file)

        with open(semmy_path / Path("data/settings.yaml"), "r", encoding='utf8') as file:
            self.settings = safe_load(file)

        # drawing data is a dictionary of the form:
        # {
        #   'object 1': [measured_line, measured_line, ...],
        #   'object 2': [measured_circle, measured_circle, ...],
        #   ...
        # }
        self.drawing_data = dict()
        self.units = dict(fm=1e-15, pm=1e-12, nm=1e-9, µm=1e-6, mm=1e-3, m=1, km=1e3)

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
        logging.info(f"object {object} saved in drawing_data")

    def delete_object(self, object):
        """delete object from the storage dict

        Args:
            object_data (class:object): the object that should be deleted
        """
        for object_name, object_list in list(self.drawing_data.items()):
            if object in object_list:
                object_list.remove(object)
            if object.parent in object_list:
                object_list.remove(object.parent)
            # If the list is empty after removal, delete the key from the dictionary
            if not object_list:
                self.main_ui.remove_from_structure_dd(object_name)
                del self.drawing_data[object_name]
                self.main_ui.structure_dd.setCurrentText("")
            
    def delete_all_objects(self):
        for structure_list in list(self.drawing_data.values()):
            for object in structure_list:
               object.delete()
            
        self.drawing_data = dict()
        self.main_ui.update_structure_dd()
        logging.info("Deleted all measurements")
        
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
            logging.warning(f"Could not open file location: {path.parent}:\n{error}")
            self.main_ui.raise_error(f"Could not open file location: {path.parent}")

    def save_file_dialog(self, file_name="semmy.semmy", extensions="Semmy Files (*.semmy *.sem)"):
        filename, _ = QFileDialog.getSaveFileName(self.main_ui, 
                                                "Save", 
                                                file_name, 
                                                extensions)
        if filename:
            return filename
        
    def save_storage_file(self, save_image=True, **kwargs):
        
        filename = self.save_file_dialog(file_name=str(self.file_path.with_suffix('.semmy')))
        if filename is None:
            return
        
        structure_data = dict()
        for key, val in self.drawing_data.items():
            structure_data[key] = [[obj.__class__, deepcopy(obj.save())] for obj in val]
        
        #TODO: scalebar length
        if save_image:
            output = (self.img_data, structure_data)
        else:
            output = (None, structure_data)
        with open(filename, 'wb') as save_file:
            pickle.dump(output, save_file, pickle.HIGHEST_PROTOCOL, **kwargs)
        # with open(filename, 'w') as save_file:
        #     yaml.dump(data, save_file, allow_unicode=True)
    
    def load_storage_file(self, file_path, vispy_instance):

        with open(file_path, 'rb') as file:
            
            logging.info(f"opened file: {file_path}")
            img_data, structure_data = pickle.load(file)
            # data: dict = yaml.load(file, Loader=yaml.Loader)
            
            reply = QMessageBox.StandardButton.Yes
            question = None
            
            if self.img_data is None and img_data is None:
                self.main_ui.raise_error("You can't load measurements without loading an image first.")
                return
            
            if self.drawing_data or self.img_data is not None:
                if img_data is None:
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
                reply = QMessageBox.warning(self.main_ui, "Warning",
                        question,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
            
            if reply is QMessageBox.StandardButton.Yes:
                
                self.delete_all_objects()
                self.file_path = file_path
                if img_data is not None:
                    self.img_data = img_data
                    logging.debug("set data_handler.img_data to loaded file data")
                    vispy_instance.update_image()
                

            if structure_data:
                for key, val in structure_data.items():
                    for obj_type, obj_data in val:
                        new_object = obj_type(**obj_data, parent=vispy_instance.view.scene)
                        vispy_instance.create_new_object(new_object, structure_name=key) 
            
            self.main_ui.update_structure_dd()           
    
    def open_file(self, file_path: str|Path|None, vispy_instance):
        
        if file_path:
            file_path = Path(file_path)
            
            if file_path.suffix in self.file_extensions:
                self.load_storage_file(file_path, vispy_instance=vispy_instance)
            
            else:
                reply = QMessageBox.StandardButton.Yes
                if self.img_data is not None:
                    reply = QMessageBox.warning(self.main_ui, "Warning",
                        "Do you want to load a new image?\n\nThis will replace the current image and remove the measurements.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.file_path = file_path
                    self.delete_all_objects()
                    vispy_instance.update_image()

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
                if self.main_ui.scaling != 1 :
                    if prop in ['length', 'area', 'radius', 'width', 'height', 'center']:
                        data = [d*self.main_ui.scaling for d in data]
                        exponent = unit[-1] if unit[-1] in ['²', '³'] else ""
                        unit = self.main_ui.units_dd.currentText() + exponent
                
                results[structure_name][prop] = (mean(data),std(data)/sqrt(len(object_list)), unit)
        return results
    
    def calculate_results_string(self):
        results = self.calculate_results()
        # sort dict
        results = dict(sorted(results.items()))
        results_string = ""
        for structure_name, structure_results in results.items():
            results_string += f"{structure_name}:\n"
            for prop, prop_results in structure_results.items():
                results_string += f"\t{prop}:\t ({prop_results[0]:.1f}"
                results_string += f" ± {prop_results[1]:.1f}) {prop_results[2]}\n"
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
            self.main_ui.raise_error("This structure already exists!")
        elif new_structure == "" or new_structure.isspace():
            self.main_ui.raise_error("This name is not valid")
        else:
            self.drawing_data[new_structure] = self.drawing_data[structure] 
            del self.drawing_data[structure]
            return True
        
        return False