from semmy.app import App
from pathlib import Path

def test_main_program():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    # app.vispy_app.sleep(1)
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
    
def test_open_semmy_file():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_file.semmy"), 
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

    app = App(file_path=Path(__file__).parent/Path("test_data/test_file.semmy"))
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.close()
    