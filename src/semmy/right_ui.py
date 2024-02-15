from PyQt6.QtWidgets import (QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout)
import numpy as np
from vispy.plot import Fig as vp_Fig

# relative imports
from .drawable_objects import EditLineVisual, LineControlPoints

class RightUI(QWidget):
    
    content_size = None
    
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()
        self.main_window = main_window
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout)
        
        self.top_layout.addWidget(QLabel("UI for diagrams"))
        
        self.top_layout.addStretch()
        
        # button to close the right ui
        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.hide_ui)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("background-color: red; color: white; border: none;")
        self.top_layout.addWidget(self.close_button)
        
        
        # add intensity plot
        self.vispy_intensity_plot = vp_Fig(size=(200, 300), show=False)
        # Add a line plot
        line_plot = self.vispy_intensity_plot[0, 0]
        self.intensity_line = line_plot.plot(([0], [0]), 
                        marker_size=0)
                    #    title='Intensity Profile',
                    #    xlabel='Pixel',
                    #    ylabel='Intensity')
        # Remove the borders
        line_plot.border_color = (0, 0, 0, 0)
        
        self.layout.addWidget(self.vispy_intensity_plot.native)
        
        
        # add spacer
        self.layout.addStretch()
        
        
    def update_intensity_plot(self):
        selected_element = self.main_window.main_ui.vispy_canvas_wrapper.selected_object
        if isinstance(selected_element, LineControlPoints):
            selected_element = selected_element.parent
        if isinstance(selected_element, EditLineVisual):
            image = self.main_window.main_ui.data_handler.img_data
            intensity_profile = selected_element.intensity_profile(image=image)
            length = selected_element.length
            distance = np.linspace(0, length, len(intensity_profile))
            intensity = np.sum(intensity_profile, axis=1)
            
            # automatically set correct axis limits
            self.vispy_intensity_plot[0, 0].camera.set_range(x=(0, length), y=(np.min(intensity), np.max(intensity)))
            # update the line plot
            self.intensity_line.set_data((distance, intensity))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if self.width() == 0:
            self.main_window.open_right_ui_button.show()
        else:
            self.main_window.open_right_ui_button.hide()
            
    def hide_ui(self):
        self.content_size = self.width()
        size = self.main_window.splitter.sizes()
        self.main_window.splitter.setSizes([size[0]+self.content_size//2, 
                                            size[1]+self.content_size//2, 
                                            0])
        
        self.hide()
        self.main_window.open_right_ui_button.show()
        
    def show_ui(self):
        self.show()
        self.main_window.open_right_ui_button.hide()
        
        # resize layout
        size = self.main_window.splitter.sizes()
        if self.content_size is None:
            self.content_size = self.layout.sizeHint().width()
        self.main_window.splitter.setSizes([size[0]-self.content_size//2, size[1]-self.content_size//2, self.content_size])