import PyInstaller.__main__
import shutil
from pathlib import Path
from measury import __version__ as measury_version
script_path = Path(__file__).parent.resolve()


if __name__ == '__main__':
    # set program name and method
    program_name = "Measury" + "_" + measury_version
    method = "onedir"
    zipped = False

    # run pyinstaller
    PyInstaller.__main__.run([
        str(script_path/'run_clean.py'),
        f'--{method}',
        '--windowed',
        '--name', program_name,
        '--specpath', 'build',
        '--icon', '../img/logo/tape_measure_128.ico',
        '--collect-all', 'vispy',
        '--collect-all', 'measury',
        '--noconfirm'
    ])

    # zip output for easy distribution
    output_path = (script_path/f"/../dist/{program_name}").resolve()
    if zipped:
        shutil.make_archive(output_path, 'zip', output_path)