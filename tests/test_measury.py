from measury.app import App
from pathlib import Path

def test_main_program():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    # app.vispy_app.sleep(1)
    app.close()
    
def test_rigth_ui():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.main_window.right_ui.show_ui()
    app.vispy_app.process_events()
    app.main_window.right_ui.hide_ui()
    app.vispy_app.process_events()
    app.close()

def test_open_tif_file():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.vispy_app.process_events()
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_image.tif"), 
                                       vispy_instance=app.main_window.vispy_canvas)
    app.close()
    
def test_open_measury_file():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_file.msry"), 
                                       vispy_instance=app.main_window.vispy_canvas)
    app.close()

def test_identify_scaling():

    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_image.tif"), 
                                       vispy_instance=app.main_window.vispy_canvas)
    app.main_window.main_ui.automatic_scaling()
    app.close()

def test_start_with_image():

    app = App(file_path=Path(__file__).parent/Path("test_data/test_file.msry"))
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.close()
    
def test_open_right_ui():

    app = App(file_path=Path(__file__).parent/Path("test_data/test_file.msry"))
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
    