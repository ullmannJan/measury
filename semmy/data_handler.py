import yaml
from pathlib import Path

class DataHandler:

    img_path = None
    img_data = None

    main_ui = None


    # database (dict) of sems with points in scaling bar
    def __init__(self):

        with open(Path('data/sem_db.yml'), 'r') as file:
            self.sem_db = yaml.safe_load(file)
        
        with open(Path('data/Settings.yaml'), 'r') as file:
            self.settings = yaml.safe_load(file)

        # output data is a dictionary of the form:
        # {
        #   'object 1': [measured_line, measured_line, ...],
        #   'object 2': [measured_circle, measured_circle, ...],
        #   ...
        # }
        self.output_data = dict()

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
    