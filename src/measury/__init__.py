from pathlib import Path

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")

# for compiling the program
measury_path = Path(__file__).parent.resolve()

from .app import run