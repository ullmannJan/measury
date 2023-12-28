from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("semmy")
except PackageNotFoundError:
    __version__ = "unknown version"

semmy_path = Path(__file__).parent.resolve()
