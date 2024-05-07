# absolute imports
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, \
    QGroupBox, QPushButton, QCheckBox, QLineEdit, QHBoxLayout, \
    QColorDialog, QComboBox, QTabWidget
from PyQt6.QtGui import QIcon, QGuiApplication, QColor
from PyQt6.QtCore import Qt, pyqtSignal

# relative imports
from . import __version__ as semmy_version
from . import semmy_path
from .settings import Settings, DEFAULT_SETTINGS

class SemmyWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, parent, title="Window"):
        super().__init__()
        # this makes the main application unresponsive while using this window
        # self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.parent = parent

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setWindowTitle(f"Semmy: {title}")
        self.setWindowIcon(QIcon(str(semmy_path/"data/tape_measure_128.ico")))
        self.setMinimumSize(300,200)


class SaveWindow(SemmyWindow):
    """
    The window displayed to save the data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(title="Save Dialog", *args, **kwargs)
                
        #Save Options 
        self.options_box = QGroupBox("Options", self)
        self.options_layout = QVBoxLayout()
        self.options_box.setLayout(self.options_layout)
        self.layout.addWidget(self.options_box)
        
        self.save_img_checkbox = QCheckBox(text="Save Image")
        self.save_img_checkbox.setChecked(True)
        self.options_layout.addWidget(self.save_img_checkbox)

        # Save Button
        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.save)
        self.layout.addWidget(self.saveButton)

    def save(self):
        return self.parent.data_handler.save_storage_file(save_image=self.save_img_checkbox.isChecked())


class AboutWindow(SemmyWindow):
    """
    The window displaying the about.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(title="About", *args, **kwargs)
        
        self.info_layout = QVBoxLayout()

        self.info_layout.addWidget(QLabel(f"<b>Semmy {semmy_version}</b>"))
        self.info_layout.addWidget(QLabel("A simple tool for measuring distances in images."))
        self.info_layout.addWidget(QLabel("Developed by:"))
        self.info_layout.addWidget(QLabel("Jan Ullmann"))

        self.layout.addLayout(self.info_layout)

class DataWindow(SemmyWindow):
    """
    The window displaying the data results.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(title="Measurements", *args, **kwargs)
        
        label = QLabel(self.parent.data_handler.calculate_results_string())
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Make the text selectable
        self.layout.addWidget(label)

        # Copy Button
        self.copyButton = QPushButton("Copy", self)
        self.copyButton.clicked.connect(self.copy_to_clipboard)
        self.layout.addWidget(self.copyButton)
        # Save Button
        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.parent.data_handler.save_measurements_file)
        self.layout.addWidget(self.saveButton)
        
    def copy_to_clipboard(self):
        cb = QGuiApplication.clipboard()
        cb.clear()
        cb.setText(self.parent.data_handler.calculate_results_string())
        print(cb.text())
        
class SettingsWindow(SemmyWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(title="Settings", *args, **kwargs)
        # self.setMinimumHeight(500)

        self.settings: Settings = self.parent.settings
        self.settings.load_settings()

        self.main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.graphics = QWidget()
        self.misc = QWidget()

        self.tab_widget.addTab(self.graphics, "Graphics")
        self.tab_widget.addTab(self.misc, "Misc")
        self.tab_widget.resize(300, 400)

        self.create_graphics_ui()
        self.create_misc_ui()

        # Resize the window to fit the contents of the tabs
        self.resize(self.tab_widget.sizeHint())

        # Buttons Layout
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
        # Save Button
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save)
        self.save_button.setEnabled(self.changed)
        self.button_layout.addWidget(self.save_button)
        
        # reset button
        self.reset_button = QPushButton("Reset to defaults", self)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.reset_button.setEnabled(not self.settings.is_default)
        self.button_layout.addWidget(self.reset_button)
        
        self.layout.addLayout(self.main_layout)

    def create_misc_ui(self):
        
        self.misc_layout = QVBoxLayout()
        self.misc.setLayout(self.misc_layout)
        
        
    def create_graphics_ui(self):
        """Create the UI for the settings window."""

        # rendering version
        self.graphics_layout = QVBoxLayout()

        self.rendering_layout = QHBoxLayout()
        self.rendering_label = QLabel("Image Rendering", self)

        self.rendering_combobox = QComboBox(self)
        self.rendering_combobox.addItems(["bessel", "blackman", "catrom", "cubic", "custom", "gaussian", "hamming", "hanning", "hermite", "kaiser", "lanczos", "linear", "mitchell", "nearest", "quadric", "sinc", "spline16", "spline36", "bilinear", "bicubic"])
        self.rendering_combobox.setCurrentText(self.settings.value('graphics/image_rendering'))
        self.rendering_combobox.currentTextChanged.connect(self.update_window)
        
        self.rendering_layout.addWidget(self.rendering_label)
        self.rendering_layout.addWidget(self.rendering_combobox)
        self.graphics_layout.addLayout(self.rendering_layout)
        
        # Color Selector inside
        self.color_layout = QHBoxLayout()
        self.color_label = QLabel("Object Color", self)
        
        self.color_picker = ColorPicker(self.settings.value('graphics/object_color'), "Pick Color", self)
        self.color_picker.color_updated.connect(self.update_window)
        
        self.color_layout.addWidget(self.color_label)
        self.color_layout.addWidget(self.color_picker)
        self.graphics_layout.addLayout(self.color_layout)
        
        # Color Selector border
        self.border_color_layout = QHBoxLayout()
        self.border_color_label = QLabel("Object Border Color", self)
        
        self.border_color_picker = ColorPicker(self.settings.value('graphics/object_border_color'), "Pick Color", self)
        self.border_color_picker.color_updated.connect(self.update_window)
        
        self.border_color_layout.addWidget(self.border_color_label)
        self.border_color_layout.addWidget(self.border_color_picker)
        self.graphics_layout.addLayout(self.border_color_layout)
        
        # Color Selector scale bar
        self.scale_bar_color_layout = QHBoxLayout()
        self.scale_bar_color_label = QLabel("Scale Bar Color", self)
        
        self.scale_bar_color_picker = ColorPicker(self.settings.value('graphics/scale_bar_color'), 
                                                  "Pick Color", 
                                                  self, 
                                                  alpha_channel=False)
        self.scale_bar_color_picker.color_updated.connect(self.update_window)
        
        self.scale_bar_color_layout.addWidget(self.scale_bar_color_label)
        self.scale_bar_color_layout.addWidget(self.scale_bar_color_picker)
        self.graphics_layout.addLayout(self.scale_bar_color_layout)
        
            
        self.graphics.setLayout(self.graphics_layout)

    def reset_to_defaults(self):
        """Reset the settings to the default values."""
        
        self.rendering_combobox.setCurrentText(DEFAULT_SETTINGS.get("graphics/image_rendering"))
        self.color_picker.selectedColor = DEFAULT_SETTINGS.get("graphics/object_color")
        self.border_color_picker.selectedColor = DEFAULT_SETTINGS.get("graphics/object_border_color")
        self.scale_bar_color_picker.selectedColor = DEFAULT_SETTINGS.get("graphics/scale_bar_color")
        self.update_window()
    
    def update_window(self):
        """Update the windows with the new settings."""
        self.parent.data_handler.logger.info("Updating settings window")
        # set button states
        self.reset_button.setEnabled(not self.settings.is_default)
        self.save_button.setEnabled(self.changed)
        
    def save(self):
        self.settings.save("graphics/object_color", self.color_picker.selectedColor)
        self.settings.save("graphics/object_border_color", self.border_color_picker.selectedColor)
        self.settings.save("graphics/image_rendering", self.rendering_combobox.currentText())
        self.settings.save("graphics/scale_bar_color", self.scale_bar_color_picker.selectedColor)
        self.update_window()
        self.parent.vispy_canvas.update_object_colors()
        # update color of the scalebar
        self.parent.vispy_canvas.find_scale_bar_width(*self.parent.vispy_canvas.scale_bar_params)
    
    @property
    def changed(self):
        """Check if there is a change in the settings gui."""
        return self.color_picker.selectedColor.getRgb() != self.settings.value("graphics/object_color").getRgb() or \
                self.border_color_picker.selectedColor.getRgb() != self.settings.value("graphics/object_border_color").getRgb() or \
                self.rendering_combobox.currentText() != self.settings.value("graphics/image_rendering") or \
                self.scale_bar_color_picker.selectedColor.getRgb() != self.settings.value("graphics/scale_bar_color").getRgb()

class ColorPicker(QPushButton):
    
    color_updated = pyqtSignal(QColor)  # Define a custom signal
    
    def __init__(self, color:QColor, *args, alpha_channel=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.color_picker = QColorDialog()
        if alpha_channel:
            self.color_picker.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel)
        self.color_picker.colorSelected.connect(self.update_color)
        self.clicked.connect(self.color_picker.open)
        self.selectedColor = color  # Initialize with a default color
        
    def update_color(self, color):
        self._selectedColor = color
        
        rgba = color.getRgb()
        self.setStyleSheet(f"background-color: rgba{rgba};")
        self.color_updated.emit(color)

    @property
    def selectedColor(self) -> QColor:
        return self._selectedColor
    
    @selectedColor.setter
    def selectedColor(self, color: QColor):
        self.color_picker.setCurrentColor(color)
        self.update_color(color)
    
    