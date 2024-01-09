from semmy.app import App
from pathlib import Path

def test_main_program():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    # app.vispy_app.sleep(1)
    app.close()
    
def test_open_file():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.open_file(Path(__file__).parent/Path("test_data/test_file.semmy"), 
                                       vispy_instance=app.main_window.vispy_canvas)
    app.close()
    