from pathlib import Path

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")

# for compiling the program
semmy_path = Path(__file__).parent.resolve()

from sys import argv
from .app import App

def run(file_path=None):
    if len(argv) > 1:
        app = App(file_path=argv[1])
    else:
        app = App(file_path=file_path)
    
    app.run()