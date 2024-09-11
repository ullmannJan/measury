from measury.app import App
from pathlib import Path
import pytest
from numpy import __version__ as np_version

if np_version[0] == "2":
    test_files = ["test_image.tif", "test_file.msry", "test_file_2.msry"]
else:
    test_files = ["test_image.tif", "test_file.msry", "test_file_3.msry", "test_file_4.msry"]

def test_main_program():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    # app.vispy_app.sleep(1)
    app.close()
    
def test_right_ui():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.right_ui.show_ui()
    app.vispy_app.process_events()
    app.main_window.right_ui.hide_ui()
    app.vispy_app.process_events()
    app.close()
    
@pytest.mark.parametrize("file", test_files)
def test_open_file(file):
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/"test_data"/file)
    app.close()

def test_identify_scaling():

    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_image.tif"))
    app.main_window.main_ui.automatic_scaling()
    app.close()

@pytest.mark.parametrize("file", test_files)
def test_start_with_image(file):

    app = App(file_path=Path(__file__).parent/"test_data"/file)
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.close()
    
def test_open_right_ui():

    app = App(file_path=Path(__file__).parent/"test_data"/test_files[-1])
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.right_ui.show_ui()
    app.vispy_app.process_events()
    app.main_window.right_ui.hide_ui()
    app.vispy_app.process_events()
    app.close()

def test_settings_page():

    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.open_settings_page()
    app.vispy_app.process_events()
    app.close()
    
def test_data_page():

    app = App(file_path=Path(__file__).parent/"test_data"/test_files[-1])
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.open_data_page()
    app.vispy_app.process_events()
    app.close()
    
def test_image_rotation():

    app = App(file_path=Path(__file__).parent/"test_data"/test_files[-1])
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.vispy_canvas.rotate_image()
    app.vispy_app.process_events()
    app.main_window.vispy_canvas.rotate_image(direction="counterclockwise")
    app.vispy_app.process_events()
    app.close()
    