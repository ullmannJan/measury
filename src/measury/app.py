# absolute imports
from vispy.app import use_app
import sys
import warnings

# relative imports
from .main_window import MainWindow
from .data_handler import DataHandler
from . import __version__


class App:

    def __init__(self, file_path=None, logger=None):

        self.vispy_app = use_app("pyside6")
        self.vispy_app.create()
        self.data_handler = DataHandler(logger)
        self.main_window = MainWindow(self.data_handler)
        self.data_handler.main_window = self.main_window
        self.data_handler.open_file(
            file_path=file_path
        )

    def run(self, run_vispy=True):
        """
        Run the application.

        Args:
            run_vispy (bool, optional): Whether to run the VisPy application.
            Defaults to True.
        """
        # bug fix for windows where icon is not displayed
        if "win" in sys.platform:
            import ctypes
            myappid = f'pit.spectran.app.{__version__}' # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        sys.excepthook = self.exception_hook
        warnings.showwarning = self.warning_handler

        self.main_window.show()
        # update axis because when creating the qt application the
        # transformations change implicitely
        self.main_window.vispy_canvas.center_image()
        if run_vispy:
            self.vispy_app.run()

    def exception_hook(self, exception_type, exception_value: Exception, traceback):
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
        self.main_window.raise_error(exception_value)
        sys.__excepthook__(exception_type, exception_value, traceback)
        
    def warning_handler(self, message, category, filename, lineno, file=None, line=None):
        """
        Custom warning handler.

        Args:
            message (Warning): The warning message.
            category (Warning): The category of the warning.
            filename (str): The file name where the warning occurred.
            lineno (int): The line number where the warning occurred.
            file (file object, optional): The file object to write the warning to.
            line (str, optional): The line of code where the warning occurred.
        """
        warning_message = f"{filename}:{lineno}: {category.__name__}: {message}"
        print(warning_message)

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
