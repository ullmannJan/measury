# absolute imports
from yaml import safe_load
from pathlib import Path
from . import run_path

class DataHandler:

    img_data = None

    main_ui: dict|None = None
    output_data: dict|None

    units: dict


    # database (dict) of sems with points in scaling bar
    def __init__(self, img_path=None):

        if img_path is not None:
            self.img_path = str(Path(img_path))
        else:
            self.img_path = None

        with open(run_path/Path('data/sem_db.yml'), 'r') as file:
            self.sem_db = safe_load(file)
        
        with open(run_path/Path('data/Settings.yaml'), 'r') as file:
            self.settings = safe_load(file)

        # output data is a dictionary of the form:
        # {
        #   'object 1': [measured_line, measured_line, ...],
        #   'object 2': [measured_circle, measured_circle, ...],
        #   ...
        # }
        self.output_data = dict()
        self.units =  dict(fm=1e-15, pm=1e-12, nm=1e-9, µm=1e-6, mm=1e-3, m=1, km=1e3)

    def save_object(self, object_name, object_data):
        if object_name == '':
            object_name = self.generate_output_name()
            self.main_ui.structure_edit.setText(object_name)

        # if not in output dict then add an empty list
        if object_name not in self.output_data.keys():
            self.output_data[object_name] = list()
        self.output_data[object_name].append(object_data)

    def delete_object(self, object_data):
        for object_name, object_list in list(self.output_data.items()):
            try:
                object_list.remove(object_data)
                # If the list is empty after removal, delete the key from the dictionary
                if not object_list:
                    del self.output_data[object_name]
            except ValueError:
                # The object was not in this list, so we can continue to the next one
                continue

    def generate_output_name(self):
        return f'object_001'
    