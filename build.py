import PyInstaller.__main__
import shutil
from distutils.dir_util import copy_tree
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
    # '--add-data', 'data:data',
    # '--add-data', 'img/logo:img/logo',
    '--collect-all', 'vispy',
    '--noconfirm'
])

# copy data and img/logo
if method == "onedir":

    output_path = Path(f"dist/{program_name}")

    copy_tree("data", str(output_path/"data"))
    copy_tree("img/logo", str(output_path/"img/logo"))

if method == "onefile":

    output_path = Path(f"dist/{program_name}")
    output_path.mkdir(parents=True, exist_ok=True)

    shutil.move(f"dist/{program_name}.exe", output_path/f"{program_name}.exe")
    copy_tree("data", str(output_path/"data"))
    copy_tree("img/logo", str(output_path/"img/logo"))

# zip output for easy distribution
if zipped:
    shutil.make_archive(output_path, 'zip', output_path)