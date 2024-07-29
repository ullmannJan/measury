import PyInstaller.__main__
import shutil
import sys
import platform
from pathlib import Path
from measury import __version__ as measury_version

script_path = Path(__file__).parent.resolve()

def compile(program_name, method="onedir", zipped=False):
    # run pyinstaller
    arguments = [
            str(script_path / "run_clean.py"),
            f"--{method}",
            "--windowed",
            "--name",
            program_name,
            "--specpath",
            "build",
            "--collect-all",
            "vispy",
            "--collect-all",
            "measury",
            "--collect-all",
            "scipy",
            "--noconfirm",
            "--icon",
        ]
    
    if sys.platform == "darwin":
        arguments.append("../img/logo/tape_measure_128.icns") 
        arguments.append("--windowed")
        extension = ".app"

    else:
        arguments.append("../img/logo/tape_measure_128.ico")
        extension = ""


    PyInstaller.__main__.run(
        arguments
    )

    # zip output for easy distribution
    output_path = (script_path / f"../dist/{program_name}{extension}").resolve()
    # Modify the output_path based on architecture
    if zipped:

        # Determine the architecture
        arch = platform.machine()
        match sys.platform:
            case "win32":
                archive_format = "zip"
                suffix = "_win"
            case "linux":
                archive_format = "gztar"
                suffix = "_lnx"
            case "darwin":
                archive_format = "gztar"
                suffix = "_mac"

        # Append architecture to suffix
        if "arm" in arch.lower():
            suffix += "_arm"
        elif "x86_64" in arch.lower() or "amd64" in arch.lower():
            suffix += "_x64"

        shutil.make_archive(
            output_path.with_name(f"{program_name}{suffix}{extension}"),
            archive_format,
            root_dir=output_path.parent, # the dist folder so that we can archive the full folder
            base_dir=f"{program_name}{extension}",
        )
        
if __name__ == "__main__":
    # set program name and method
    program_name = "Measury" + "_" + measury_version
    method = "onedir"
    zipped = False
    if len(sys.argv) > 1 and sys.argv[1] == "zipped":
        zipped = True
        
    compile(program_name, method, zipped)
