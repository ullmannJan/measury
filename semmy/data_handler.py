# absolute imports
from yaml import safe_load
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog
import pickle
from os import startfile
from subprocess import Popen
from sys import platform
from copy import deepcopy

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
        if structure_name == "":
            structure_name = self.generate_output_name()

        # if not in output dict then add an empty list
        if structure_name not in self.drawing_data.keys():
            self.drawing_data[structure_name] = list()
        self.drawing_data[structure_name].append(object)

    def delete_object(self, object):
        """delete object from the storage dict

        Args:
            object_data (class:object): the object that should be deleted
        """
        for object_name, object_list in list(self.drawing_data.items()):
            try:
                object_list.remove(object)
                # If the list is empty after removal, delete the key from the dictionary
                if not object_list:
                    self.main_ui.remove_from_structure_dd(object_name)
                    del self.drawing_data[object_name]

            except ValueError:
                # The object was not in this list, so we can continue to the next one
                continue
            
    def delete_all_objects(self):
        for structure_list in list(self.drawing_data.values()):
            for object in structure_list:
               object.delete()
            
        self.drawing_data = dict()
        
    def find_object(self, object):
        if self.drawing_data:
            for k, val in self.drawing_data.items():
                if object in val:
                    return k, val.index(object)
            raise LookupError("Object could not be found in drawing_data")
    

    def generate_output_name(self):
        return "structure_001"
    
    
    def open_file_location(self, path: Path):
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
                   
    def save_file_dialog(self, file_name="semmy.semmy"):
        filename, _ = QFileDialog.getSaveFileName(self.main_ui, 
                                                "Save", 
                                                file_name, 
                                                "Semmy Files (*.semmy *.sem)")
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
        
            img_data, structure_data = pickle.load(file)
            # data: dict = yaml.load(file, Loader=yaml.Loader)
            
            if img_data is None:
                if self.img_data is None:
                    return
            else:
                
                self.img_data = img_data
                self.file_path = file_path
                vispy_instance.update_image()

            
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
                self.file_path = file_path
                vispy_instance.update_image()