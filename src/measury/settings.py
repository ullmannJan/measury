from PySide6.QtGui import QColor
from PySide6.QtCore import QSettings

DEFAULT_SETTINGS = {
    "graphics/object_color": QColor(255, 0, 0, 26),
    "graphics/object_border_color": QColor(255, 0, 0, 127),
    "graphics/image_rendering": "nearest",
    "graphics/scale_bar_color": QColor(255, 0, 0, 255),
    "graphics/style": "Fusion",
    "ui/microscope": "Generic_Microscope",
    "ui/show_both_scaling": False,
    "misc/file_extensions": [".msry", ".measury"],
}


class Settings(QSettings):

    def __init__(self, parent, organization: str, application: str):
        super().__init__(organization, application)
        self.parent = parent

    def load_defaults(self):
        """Manage loading all the settings."""
        self.parent.data_handler.logger.info("Loading default settings")
        for key, value in DEFAULT_SETTINGS.items():
            self.setValue(key, value)
        self.sync()

    def load_settings(self):
        """Load all the settings."""
        self.parent.data_handler.logger.info("Loading settings")
        for key in DEFAULT_SETTINGS.keys():
            if self.value(key) is None:
                # No settings exist, load the default settings
                self.load_defaults()

    def save(self, key, value):
        """Manage saving all the settings."""
        self.parent.data_handler.logger.info(f"Saving setting: {key}")
        self.setValue(key, value)
        self.sync()

    @property
    def is_default(self):
        """Test if the settings are the default values."""
        return self.equals_settings(DEFAULT_SETTINGS)

    def equals_settings(self, settings: dict):
        """Compare the settings to the default settings."""
        # check if the keys are the same
        if set(self.allKeys()) != set(settings.keys()):
            self.parent.data_handler.logger.info(
                f"Settings not equal: {set(self.allKeys())} {set(settings.keys())}"
            )
            return False
        # check if the values are the same
        for key in settings.keys():
            # for lists we need to compare the sets
            if isinstance(settings.get(key), list):
                if set(self.value(key)) != set(settings.get(key)):
                    self.parent.data_handler.logger.info(
                        f"Settings not equal: {set(self.allKeys())} {set(settings.keys())}"
                    )
                    return False
            # for boolean we need to set the type
            elif isinstance(settings.get(key), bool):
                if self.value(key, type=bool) != settings.get(key):
                    self.parent.data_handler.logger.info(
                        f"Setting not equal: {key} {self.value(key)} {settings.get(key)}"
                    )
                    return False
            # otherwise simply compare the values
            elif self.value(key) != settings.get(key):
                self.parent.data_handler.logger.info(
                    f"Setting not equal: {key} {self.value(key)} {settings.get(key)}"
                )
                return False
        return True
