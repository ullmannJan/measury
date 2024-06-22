import inspect
import sys
from abc import ABC
from typing import Optional, Tuple
import json
import xml.etree.ElementTree as ET
import os

def load_microscopes():
    microscopes = dict()
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and issubclass(obj, Microscope) and obj != Microscope:
            microscopes[name] = obj
    return microscopes



class Microscope(ABC):
    def __init__(self, 
                 seed_points: Optional[Tuple[float, float]] = None, 
                 orientation: Optional[str] = None, 
                 threshold: Optional[int] = None):
        """
        Initializes a new instance of the Microscope class.

        :param seed_points: A tuple representing the seed points for the microscope.
        :param orientation: The orientation of the microscope.
        :param threshold: The threshold value used for processing.
        """
        self.seed_points = seed_points
        self.orientation = orientation
        self.threshold = threshold
    
    def get_metadata(self, file_path: Optional[str] = None) -> str:
        """
        Abstract method to get the metadata of a microscope image.

        :param file_path: The path to the file from which to extract metadata.
        :return: A string representing the metadata.
        """
        if file_path is None:
            return ""
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    


class Generic_Microscope (Microscope):

    def __init__(self):
        super().__init__()

class Zeiss_Orion_Nanofab (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.698243, 0.92768),
                         orientation="horizontal",
                         threshold=10)

    def get_metadata(self, file_path=None) -> str:
        try:
            values = self.get_xml(file_path)
        except:
            values = None
        # check if values is a non-empty dictionary
        if isinstance(values, dict):
            return json.dumps(values, indent=4, ensure_ascii=False)
        return Microscope().get_metadata(file_path)
        
    def get_xml(self, file_path=None):
        # This only works for Zeiss Orion files yet

        # first check if image was loaded
        if file_path is None:
            return None
        
        # get last line of file
        with open(file_path, 'rb') as f:
            try:  # catch OSError in case of a one line file 
                # move to the second last character
                f.seek(-2, os.SEEK_END)
                # move to the beginning of the line
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            # remove last character as it is null
            last_line = f.readline().decode()[:-1]
            
        try:
            root = ET.fromstring(last_line)
        except ET.ParseError as e:
            raise "There was a problem parsing the XML string.\n"\
                f"Problematic part of the XML string: {last_line[max(0, e.position[1]-10):e.position[1]+10]}"
        # Create a dictionary to store the values
        values = parse_element(root)
        
        return values
    
def parse_element(element):
    """Recursively parse an XML element and its children into a dictionary."""

    # Create a dictionary to store the element's attributes
    node = {}

    # Iterate over all child elements
    for child in list(element):
        # Recursively parse the child element
        child_data = parse_element(child)

        # If the child's tag is already in the node dictionary, add the child's data to that tag
        if child.tag in node:
            # If there's only one child with this tag so far, put it in a list
            if type(node[child.tag]) is list:
                node[child.tag].append(child_data)
            else:
                node[child.tag] = [node[child.tag], child_data]
        else:
            node[child.tag] = child_data

    # If the element has no child elements, store its text
    if not node:
        node = element.text

    return node

class GUZ (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.02051, 0.94922), 
                         orientation="horizontal", 
                         threshold=10)

class Jeol_JSM_6500F (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.777344, 0.951172),
                        orientation="horizontal",
                        threshold=10)

if __name__ == "__main__":
    microscopes = load_microscopes()
    for microscope in microscopes:
        print(microscope)