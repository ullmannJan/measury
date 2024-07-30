# absolute imports
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QWidget,
    QGroupBox,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QHBoxLayout,
    QColorDialog,
    QComboBox,
    QTabWidget,
    QPlainTextEdit,
    QStyleFactory,
    QDialog,
)
from PySide6.QtGui import QIcon, QGuiApplication, QColor, QTextCursor, QImage, QPixmap,\
    qRed, qGreen, qBlue, qAlpha, qRgba
from PySide6.QtCore import Qt, Signal
import numpy as np


# relative imports
from . import __version__ as measury_version
from . import measury_path
from .settings import Settings, DEFAULT_SETTINGS


class MeasuryWindow(QWidget):
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

        self.setWindowTitle(f"Measury: {title}")
        self.setWindowIcon(QIcon(str(measury_path / "data/tape_measure_128.ico")))
        self.setMinimumSize(300, 200)

    def closeEvent(self, event):
        """
        Override the close event to set focus back to the parent window.
        """
        if self.parent:
            self.parent.setFocus()
            self.parent.activateWindow()
        super().closeEvent(event)


class SaveWindow(MeasuryWindow):
    """
    The window displayed to save the data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(title="Save Dialog", *args, **kwargs)

        # Save Options
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
        return self.parent.data_handler.save_storage_file(
            save_image=self.save_img_checkbox.isChecked()
        )


class AboutWindow(MeasuryWindow):
    """
    The window displaying the about.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(title="About", *args, **kwargs)

        self.info_layout = QVBoxLayout()

        self.info_layout.addWidget(QLabel(f"<b>Measury {measury_version}</b>"))
        self.info_layout.addWidget(
            QLabel("A simple tool for measuring distances in images.")
        )
        self.info_layout.addWidget(QLabel("Developed by:"))
        self.info_layout.addWidget(QLabel("Jan Ullmann"))

        self.layout.addLayout(self.info_layout)


class DataWindow(MeasuryWindow):
    """
    The window displaying the data results.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(title="Measurements", *args, **kwargs)

        label = QLabel(self.parent.data_handler.calculate_results_string())
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )  # Make the text selectable
        self.layout.addWidget(label)

        # Copy Button
        self.copyButton = QPushButton("Copy to Clipboard", self)
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

class ImageWindow(QDialog):
    """
    The window displaying the image.
    """
    image = None

    def __init__(self, image:QImage, title="Image Editor", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.image = image
        self.orig_image = self.extract_img_arr(image)[1]

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(str(measury_path / "data/tape_measure_128.ico")))
        self.setMinimumSize(300, 200)
        self.setMaximumSize(800, 600)

        # force this window on top
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Create a QVBoxLayout
        layout = QVBoxLayout()

        # Create a QLabel and set the QImage as its pixmap
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.redraw_image()

        # Add the QLabel to the layout
        layout.addWidget(self.label)

        # add buttons
        self.button_layout = QHBoxLayout()

        self.conversion_dd = QComboBox(self)
        self.conversion_dd.addItems(["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"])
        self.conversion_dd.currentTextChanged.connect(self.swap_colors)
        layout.addWidget(self.conversion_dd)

        self.reset_button = QPushButton("Reset", self)
        self.button_layout.addWidget(self.reset_button)
        self.reset_button.clicked.connect(self.reset_image)

        self.save_button = QPushButton("Save", self)
        self.button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.close)

        # set focus on save so that enter directly closes the window
        self.save_button.setFocus()

        # Set the layout to the window
        layout.addLayout(self.button_layout)
        self.setLayout(layout)

    def extract_img_arr(self, image:QImage) -> np.ndarray:
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)
        width = image.width()
        height = image.height()

        # Get the pixel data as a NumPy array
        ptr = image.bits()
        return image, np.array(ptr).reshape((height, width, 4))  # 4 channels: R, G, B, A

    def swap_colors(self):
        # Convert QImage to a format that allows direct access to pixel data
        color_order = self.conversion_dd.currentText()
        image = self.image.convertToFormat(QImage.Format.Format_RGBA8888)
        arr = self.orig_image.copy() 

        # Define the channel order
        channel_map = {
            "RGB": [0, 1, 2],
            "RBG": [0, 2, 1],
            "GRB": [1, 0, 2],
            "GBR": [1, 2, 0],
            "BRG": [2, 0, 1],
            "BGR": [2, 1, 0],
        }

        # Swap the color channels
        arr[..., :3] = arr[..., channel_map[color_order]]

        # Convert the NumPy array back to QImage
        self.image = QImage(arr.data, arr.shape[1], arr.shape[0], image.bytesPerLine(), QImage.Format.Format_RGBA8888)
        self.redraw_image()

    def reset_image(self):
        self.conversion_dd.setCurrentIndex(0)
        self.redraw_image() 
        
    def redraw_image(self):
        scaled_pixmap = QPixmap.fromImage(self.image).scaled(
            self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        # Call the redraw_image method to scale the image when the window is resized
        self.redraw_image()
        super().resizeEvent(event)


class SettingsWindow(MeasuryWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(title="Settings", *args, **kwargs)

        self.settings: Settings = self.parent.settings
        self.settings.load_settings()

        self.main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.graphics = QWidget()
        self.ui = QWidget()
        self.misc = QWidget()

        self.tab_widget.addTab(self.graphics, "Graphics")
        self.tab_widget.addTab(self.ui, "User Interface")
        self.tab_widget.addTab(self.misc, "Misc")
        self.tab_widget.setMinimumSize(350, 200)

        self.create_graphics_ui()
        self.create_ui_ui()
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
        self.adjustSize()
        
    def create_ui_ui(self):
        
        self.ui_layout = QVBoxLayout()
        self.ui.setLayout(self.ui_layout)

        self.default_microscope_layout = QHBoxLayout()
        self.default_microscope_label = QLabel("Default Microscope", self)
        self.default_microscope_layout.addWidget(self.default_microscope_label)
        self.default_microscope_dd = QComboBox(self)
        self.default_microscope_dd.addItems(self.parent.data_handler.micros_db.keys())
        self.default_microscope_dd.setCurrentText(self.settings.value("ui/microscope"))
        self.default_microscope_dd.currentTextChanged.connect(self.update_window)
        self.default_microscope_layout.addWidget(self.default_microscope_dd)
        self.ui_layout.addLayout(self.default_microscope_layout)
        
        self.show_both_scaling_layout = QHBoxLayout()
        self.show_both_scaling_label = QLabel("Show Scaling in px and unit", self)
        self.show_both_scaling_layout.addWidget(self.show_both_scaling_label)
        self.show_both_scaling_cb = QCheckBox(self)
        self.show_both_scaling_cb.setChecked(self.settings.value("ui/show_both_scaling", type=bool))
        self.show_both_scaling_cb.stateChanged.connect(self.update_window)
        self.show_both_scaling_layout.addWidget(self.show_both_scaling_cb)
        self.ui_layout.addLayout(self.show_both_scaling_layout)

        self.ui_layout.addStretch()

    def create_misc_ui(self):

        self.misc_layout = QVBoxLayout()
        self.misc.setLayout(self.misc_layout)

        self.clearUndoHistButton = QPushButton("Clear Undo History", self)
        self.clearUndoHistButton.clicked.connect(self.parent.reset_undo_stack)
        self.misc_layout.addWidget(self.clearUndoHistButton)

        self.file_extensions_layout = QHBoxLayout()
        self.file_extensions_label = QLabel("File Extensions", self)
        self.file_extensions_layout.addWidget(self.file_extensions_label)
        self.file_extensions = QLineEdit(self)
        self.file_extensions.setPlaceholderText(".msry;.measury")
        file_ext_string = ";".join(self.settings.value("misc/file_extensions"))
        self.file_extensions.setText(file_ext_string)
        self.file_extensions.textChanged.connect(self.update_window)
        self.file_extensions_layout.addWidget(self.file_extensions)
        self.misc_layout.addLayout(self.file_extensions_layout)

        self.misc_layout.addStretch()

    def create_graphics_ui(self):
        """Create the UI for the settings window."""

        # rendering version
        self.graphics_layout = QVBoxLayout()

        self.rendering_layout = QHBoxLayout()
        self.rendering_label = QLabel("Image Rendering", self)

        self.rendering_combobox = QComboBox(self)
        self.rendering_combobox.addItems(
            [
                "bessel",
                "blackman",
                "catrom",
                "cubic",
                "custom",
                "gaussian",
                "hamming",
                "hanning",
                "hermite",
                "kaiser",
                "lanczos",
                "linear",
                "mitchell",
                "nearest",
                "quadric",
                "sinc",
                "spline16",
                "spline36",
                "bilinear",
                "bicubic",
            ]
        )
        self.rendering_combobox.setCurrentText(
            self.settings.value("graphics/image_rendering")
        )
        self.rendering_combobox.currentTextChanged.connect(self.update_window)

        self.rendering_layout.addWidget(self.rendering_label)
        self.rendering_layout.addWidget(self.rendering_combobox)
        self.graphics_layout.addLayout(self.rendering_layout)

        # graphics style
        self.graphics_style_layout = QHBoxLayout()
        self.graphics_style_label = QLabel("Graphics Style", self)

        self.graphics_style_dd = QComboBox(self)

        available_styles = QStyleFactory.keys()

        self.graphics_style_dd.addItems(available_styles)
        self.graphics_style_dd.setCurrentText(self.settings.value("graphics/style"))
        self.graphics_style_dd.currentTextChanged.connect(self.update_window)

        self.graphics_style_layout.addWidget(self.graphics_style_label)
        self.graphics_style_layout.addWidget(self.graphics_style_dd)
        self.graphics_layout.addLayout(self.graphics_style_layout)

        # Color Selector inside
        self.color_layout = QHBoxLayout()
        self.color_label = QLabel("Object Color", self)

        self.color_picker = ColorPicker(
            self.settings.value("graphics/object_color"), "Pick Color", self
        )
        self.color_picker.color_updated.connect(self.update_window)

        self.color_layout.addWidget(self.color_label)
        self.color_layout.addWidget(self.color_picker)
        self.graphics_layout.addLayout(self.color_layout)

        # Color Selector border
        self.border_color_layout = QHBoxLayout()
        self.border_color_label = QLabel("Object Border Color", self)

        self.border_color_picker = ColorPicker(
            self.settings.value("graphics/object_border_color"), "Pick Color", self
        )
        self.border_color_picker.color_updated.connect(self.update_window)

        self.border_color_layout.addWidget(self.border_color_label)
        self.border_color_layout.addWidget(self.border_color_picker)
        self.graphics_layout.addLayout(self.border_color_layout)

        # Color Selector scale bar
        self.scale_bar_color_layout = QHBoxLayout()
        self.scale_bar_color_label = QLabel("Scale Bar Color", self)

        self.scale_bar_color_picker = ColorPicker(
            self.settings.value("graphics/scale_bar_color"),
            "Pick Color",
            self,
            alpha_channel=False,
        )
        self.scale_bar_color_picker.color_updated.connect(self.update_window)

        self.scale_bar_color_layout.addWidget(self.scale_bar_color_label)
        self.scale_bar_color_layout.addWidget(self.scale_bar_color_picker)
        self.graphics_layout.addLayout(self.scale_bar_color_layout)

        self.graphics_layout.addStretch()

        self.graphics.setLayout(self.graphics_layout)

    def set_settings(self, settings: dict):
        """Set Settings to a value."""

        self.rendering_combobox.setCurrentText(settings.get("graphics/image_rendering"))
        self.color_picker.selectedColor = settings.get("graphics/object_color")
        self.border_color_picker.selectedColor = settings.get(
            "graphics/object_border_color"
        )
        self.scale_bar_color_picker.selectedColor = settings.get(
            "graphics/scale_bar_color"
        )
        self.graphics_style_dd.setCurrentText(settings.get("graphics/style"))

        self.default_microscope_dd.setCurrentText(settings.get("ui/microscope"))
        self.show_both_scaling_cb.setChecked(settings.get("ui/show_both_scaling"))
        
        file_ext_string = ";".join(settings.get("misc/file_extensions"))
        self.file_extensions.setText(file_ext_string)
        self.update_window()

    def reset_to_defaults(self):
        """Reset the settings to the default values."""
        self.set_settings(DEFAULT_SETTINGS)
        self.reset_button.setEnabled(False)

    def update_window(self):
        """Update the windows with the new settings."""
        self.parent.data_handler.logger.info("Updating settings window")
        # set button states
        self.reset_button.setEnabled(not self.settings.is_default)
        self.save_button.setEnabled(self.changed)

    @property
    def current_selection(self):
        return {
            "graphics/object_color": self.color_picker.selectedColor,
            "graphics/object_border_color": self.border_color_picker.selectedColor,
            "graphics/image_rendering": self.rendering_combobox.currentText(),
            "graphics/scale_bar_color": self.scale_bar_color_picker.selectedColor,
            "graphics/style": self.graphics_style_dd.currentText(),
            "ui/microscope": self.default_microscope_dd.currentText(),
            "ui/show_both_scaling": self.show_both_scaling_cb.isChecked(),
            "misc/file_extensions": self.file_extensions.text().split(";"),
        }

    def save(self):
        for key in self.current_selection.keys():
            if key in DEFAULT_SETTINGS.keys():
                value = self.current_selection.get(key)
                self.settings.save(key, value)

        # update the window and the color palette
        self.parent.update_style()

        self.update_window()
        # update color of the scalebar if it has been drawn
        if self.parent.vispy_canvas.scale_bar_params[0] is not None:
            self.parent.vispy_canvas.find_scale_bar_width(
                *self.parent.vispy_canvas.scale_bar_params
            )
        else:
            self.parent.vispy_canvas.draw_image()
        self.parent.vispy_canvas.update_colors()
        self.parent.right_ui.update_colors()
        self.parent.main_ui.set_selected_object_table_columns()
        self.parent.main_ui.update_object_table()

    @property
    def changed(self):
        """Check if there is a change in the settings gui."""
        return not self.settings.equals_settings(self.current_selection)


class ColorPicker(QPushButton):

    color_updated = Signal(QColor)  # Define a custom signal

    def __init__(self, color: QColor, *args, alpha_channel=True, **kwargs):
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


class XMLWindow(MeasuryWindow):
    """
    The window displaying the xml values of a file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(title="XML file data", *args, **kwargs)

        self.setMinimumHeight(500)

        byte_stream = self.parent.data_handler.img_byte_stream

        values = self.parent.main_ui.get_microscope().get_metadata(byte_stream)
        # create scrollable text area
        self.text_area = QPlainTextEdit(self)
        self.text_area.setPlainText(values)
        self.text_area.setReadOnly(True)

        # create search line edit
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Search")
        self.search_line_edit.returnPressed.connect(self.search_text)

        # create search button
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.search_text)

        # add widgets to layout
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_line_edit)
        self.search_layout.addWidget(self.search_button)

        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.text_area)

    def search_text(self):
        # get search query from line edit
        query = self.search_line_edit.text()

        # search text area for query
        found = self.text_area.find(query)

        if not found:
            # if query was not found, move cursor to start and search again
            self.text_area.moveCursor(QTextCursor.MoveOperation.Start)
            self.text_area.find(query)
