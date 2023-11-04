import PyInstaller.__main__
import shutil
from distutils.dir_util import copy_tree
from pathlib import Path

program_name = "Semmy"
method = "onedir"

PyInstaller.__main__.run([
    'run.py',
    f'--{method}',
    '--windowed',
    '-n', program_name,
    # '--add-data', 'data:data',
    # '--add-data', 'img/logo:img/logo',
    '--collect-all', 'vispy',
    '--noconfirm'
])

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