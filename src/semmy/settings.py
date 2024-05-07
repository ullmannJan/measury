from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSettings

DEFAULT_SETTINGS = {
    "graphics/object_color": QColor(255, 0, 0, 26),
    "graphics/object_border_color": QColor(255, 0, 0, 127),
    "graphics/image_rendering": "nearest",
    "graphics/scale_bar_color": QColor(255, 0, 0, 255),
}

class Settings(QSettings):
    
    def __init__(self, parent, organization:str, application:str):
        super().__init__(organization, application)
        self.parent = parent
        
    
    def load_defaults(self):
        """Manage loading all the settings."""
        self.parent.data_handler.logger.info("Loading default settings")
        for key, value in DEFAULT_SETTINGS.items():
            print(key, ": ", value)
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
        self.parent.data_handler.logger.info("Saving settings")
        
        self.setValue(key, value)
            
            # self.default_values = self.default_values and self.value(key) == DEFAULT_SETTINGS.get(key)
        
        self.sync()

    @property
    def is_default(self):
        """Test if the settings are the default values."""
        
        for key, value in DEFAULT_SETTINGS.items():
            if self.value(key) != value:
                return False
        return True
        
        
                
        
        