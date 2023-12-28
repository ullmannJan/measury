from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")


semmy_path = Path(__file__).parent.resolve()
