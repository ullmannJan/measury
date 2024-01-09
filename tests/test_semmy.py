from semmy.app import App

def test_main_program():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    # app.vispy_app.sleep(1)
    app.vispy_app.quit()
    app.close()
    
def test_load_storage_file():
    
    app = App()
    app.run(run_vispy=False)
    app.vispy_app.process_events()
    app.data_handler.load_storage_file("")
    app.vispy_app.quit()
    app.close()