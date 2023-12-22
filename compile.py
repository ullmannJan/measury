import PyInstaller.__main__
import shutil
from pathlib import Path
from semmy import __version__ as semmy_version


# set program name and method
program_name = "Semmy" + "_" + semmy_version
method = "onedir"
zipped = False

# run pyinstaller
PyInstaller.__main__.run([
    'run.py',
    f'--{method}',
    '--windowed',
    '--name', program_name,
    '--specpath', 'build',
    '--icon', '../img/logo/tape_measure_128.ico',
    '--collect-all', 'vispy',
    '--noconfirm'
])

# zip output for easy distribution
output_path = Path(f"dist/{program_name}")
if zipped:
    shutil.make_archive(output_path, 'zip', output_path)