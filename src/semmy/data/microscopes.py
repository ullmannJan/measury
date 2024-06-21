import inspect
import sys
from abc import ABC, abstractmethod
from typing import Optional, Tuple

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
    
    @abstractmethod
    def get_metadata(self, file_path: Optional[str] = None) -> str:
        """
        Abstract method to get the metadata of a microscope image.

        :param file_path: The path to the file from which to extract metadata.
        :return: A string representing the metadata.
        """
        pass


class Generic_Microscope (Microscope):

    def get_metadata(self, file_path=None) -> str:
        return "Generic Microscope"


class Zeiss_Orion_Nanofab (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.698243, 0.92768),
                         orientation="horizontal",
                         threshold=10)

    def get_metadata(self, file_path=None) -> str:
        return "Zeiss Orion NanoFab"
    
class GUZ (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.02051, 0.94922), 
                         orientation="horizontal", 
                         threshold=10)

    def get_metadata(self, file_path=None) -> str:
        return "GUZ"

class Jeol_JSM_6500F (Microscope):

    def __init__(self):
        super().__init__(seed_points=(0.777344, 0.951172),
                     orientation="horizontal",
                     threshold=10)


    def get_metadata(self, file_path=None) -> str:
        return "Jeol JSM-6500F"

if __name__ == "__main__":
    microscopes = load_microscopes()
    for microscope in microscopes.values():
        print(microscope.get_metadata("file_path"))