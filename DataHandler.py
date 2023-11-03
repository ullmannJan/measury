import yaml

class DataHandler:

    img_path = None
    img_data = None


    # database (dict) of sems with points in scaling bar
    def __init__(self, version=None):
        self.version = version

        with open('data/sem_db.yml', 'r') as file:
            self.sem_db = yaml.safe_load(file)
        
        with open('data/Settings.yaml', 'r') as file:
            self.settings = yaml.safe_load(file)

        # output data is a dictionary of the form:
        # {
        #   'object 1': [measured_line, measured_line, ...],
        #   'object 2': [measured_circle, measured_circle, ...],
        #   ...
        # }
        self.output_data = dict()
