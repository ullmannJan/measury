import yaml

class FileHandler:

    img_path = None
    img_data = None

    # database (dict) of sems with points in scaling bar
    def __init__(self) -> None:
        with open('data/sem_db.yml', 'r') as file:
            self.sem_db = yaml.safe_load(file)
