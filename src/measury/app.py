# absolute imports
from vispy.app import use_app
import sys

# relative imports
from .main_window import MainWindow
from .data_handler import DataHandler


class App:

    def __init__(self, file_path=None, logger=None):

        self.vispy_app = use_app("pyqt6")
        self.vispy_app.create()
        self.data_handler = DataHandler(logger)
        self.main_window = MainWindow(self.data_handler)
        self.data_handler.main_window = self.main_window
        self.data_handler.open_file(
            file_path=file_path, vispy_instance=self.main_window.vispy_canvas
        )

    def run(self, run_vispy=True):
        """
        Run the application.

        Args:
            run_vispy (bool, optional): Whether to run the VisPy application.
            Defaults to True.
        """
        sys.excepthook = self.exception_hook

        self.main_window.show()
        # update axis because when creating the qt application the
        # transformations change implicitely
        self.main_window.vispy_canvas.center_image()
        if run_vispy:
            self.vispy_app.run()

    def exception_hook(self, exception_type, exception_value, traceback):
        """
        Exception hook for the application.

        Args:
            exception_type (type): Type of the exception.
            exception_value (Exception): The exception.
            traceback (traceback): The traceback of the exception.
        """
        # Print the error message to stderr
        print(f"Unhandled exception: {exception_value}")

        # Display an error message box
        self.main_window.raise_error(f"{exception_value, traceback}")
        sys.__excepthook__(exception_type, exception_value, traceback)

    def close(self):
        """
        Closes the application by quitting the Vispy app and
        closing the main window.
        """
        self.vispy_app.quit()
        self.main_window.close()


def run(file_path=None, logger=None):
    if len(sys.argv) > 1:
        app = App(file_path=sys.argv[1], logger=logger)
    else:
        app = App(file_path=file_path, logger=logger)

    app.run()
