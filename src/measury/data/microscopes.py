import inspect
import sys
from abc import ABC
from typing import Optional, Tuple
import json
import xml.etree.ElementTree as ET
import io


def load_microscopes():
    microscopes = dict()
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and issubclass(obj, Microscope) and obj != Microscope:
            microscopes[name] = obj
    return microscopes


class Microscope(ABC):
    def __init__(
        self,
        seed_points: Optional[Tuple[float, float]] = None,
        orientation: Optional[str] = None,
        threshold: Optional[int] = None,
    ):
        """
        Initializes a new instance of the Microscope class.

        :param seed_points: A tuple representing the seed points for the
                            microscope.
        :param orientation: The orientation of the microscope.
        :param threshold: The threshold value used for processing.
        """
        self.seed_points = seed_points
        self.orientation = orientation
        self.threshold = threshold

    def get_metadata(self, byte_stream: Optional[bytes] = None) -> str:
        """
        Abstract method to get the metadata of a microscope image.

        :param file_path: The path to the file from which to extract metadata.
        :return: A string representing the metadata.
        """
        if byte_stream is None:
            return ""
        else:
            return byte_stream.decode("utf-8", errors="ignore")


class Generic_Microscope(Microscope):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Zeiss_Orion_Nanofab(Microscope):

    def __init__(self):
        super().__init__(
            seed_points=(0.698243, 0.92768),
            orientation="horizontal",
            threshold=10
        )

    def get_metadata(self, byte_stream=None) -> str:

        values = self.get_xml(byte_stream)

        # check if values is a non-empty dictionary
        if isinstance(values, dict):
            return json.dumps(values, indent=4, ensure_ascii=False)
        return Microscope().get_metadata(byte_stream)

    def get_xml(self, byte_stream=None) -> dict:
        # This only works for Zeiss Orion files yet
        # first check if image was loaded
        if byte_stream is None:
            return None

        # get last line of file
        last_line = get_last_line(byte_stream)

        try:
            root = ET.fromstring(last_line)
        except ET.ParseError as e:
            # return None
            raise Exception(
                "There was a problem parsing the XML string.\n"
                "Problematic part of the XML string: "
                f"'{last_line[max(0, e.position[1]-10):e.position[1]+10]}' "
                "Are you sure this is a Zeiss Orion Nanofab file?"
            )
        # Create a dictionary to store the values
        values = parse_element(root)

        return values


def get_last_line(byte_stream) -> str:
    with io.BytesIO(byte_stream) as f:
        # Go to the end of the file
        f.seek(0, io.SEEK_END)
        # Get the position (this is the size of the file in bytes)
        position = f.tell()
        line = b""
        # we're now moving backwards through the file
        while position >= 0:
            f.seek(position)
            next_char = f.read(1)
            # Stop if a newline is found and line is not empty
            if next_char == b"\n" and line:
                break
            line = next_char + line
            position -= 1
        # remove last end character
        last_line = line.decode(encoding="utf-8", errors="replace").strip()[:-1]
        # remove all elements before the first '<' and the last '>' character
        last_line = last_line[last_line.find("<"):last_line.rfind(">") + 1]
        last_line.replace("\n", "")
        
        return last_line


def parse_element(element) -> dict:
    """Recursively parse an XML element and its children into a dictionary."""

    # Create a dictionary to store the element's attributes
    node = {}

    # Iterate over all child elements
    for child in list(element):
        # Recursively parse the child element
        child_data = parse_element(child)

        # If the child's tag is already in the node dictionary,
        # add the child's data to that tag
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


class Zeiss_Crossbeam_550L(Microscope):

    def __init__(self):
        super().__init__(
            seed_points=(0.02051, 0.94922),
            orientation="horizontal",
            threshold=10
        )


class Jeol_JSM_6500F(Microscope):

    def __init__(self):
        super().__init__(
            seed_points=(0.777344, 0.951172),
            orientation="horizontal",
            threshold=10
        )


if __name__ == "__main__":
    microscopes = load_microscopes()
    for microscope in microscopes:
        print(microscope)
