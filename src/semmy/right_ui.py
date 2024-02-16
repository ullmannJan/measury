from PyQt6.QtWidgets import (QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout)
import numpy as np
from vispy import scene
from vispy.scene import LinePlot
from vispy.scene.widgets import AxisWidget, Label

# relative imports
from .drawable_objects import EditRectVisual, EditLineVisual, LineControlPoints, ControlPoints

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
        self.vispy_intensity_plot = None
        self.create_intensity_plot()
        self.layout.addWidget(self.vispy_intensity_plot.native)
        
        
        # add spacer
        self.layout.addStretch()
    
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
        
        self.update_intensity_plot()
        
        # resize layout
        size = self.main_window.splitter.sizes()
        if self.content_size is None:
            self.content_size = self.layout.sizeHint().width()
        self.main_window.splitter.setSizes([size[0]-self.content_size//2, size[1]-self.content_size//2, self.content_size])
        
    def create_intensity_plot(self):
                
        self.vispy_intensity_plot = scene.SceneCanvas(size = (300, 300), keys='interactive', show=False, bgcolor=(240/255, 240/255, 240/255,1))
        grid = self.vispy_intensity_plot.central_widget.add_grid(margin=0)

        # Create a ViewBox and add it to the Grid
        self.diagram = grid.add_view(row=1, col=1, bgcolor='white', camera='panzoom')
        # Create a Line visual and add it to the ViewBox
        self.intensity_line = LinePlot(data=[0,0], 
                                       width=1, 
                                       marker_size=0)
        self.diagram.add(self.intensity_line)
        
        title_label = Label("Intensity Profile", color='black', font_size=8)
        title_label.height_max = 20
        grid.add_widget(title_label, row=0, col=1)

        # Create AxisWidget objects for the x and y axes and add them to the Grid
        x_axis = AxisWidget(orientation='bottom',
                            axis_font_size=8,
                            axis_label_margin=0,
                            tick_label_margin=15,
                            text_color='black')
        x_axis.height_max = 30
        y_axis = AxisWidget(orientation='left',
                            axis_font_size=8,
                            axis_label_margin=0,
                            tick_label_margin=15,
                            text_color='black')
        y_axis.width_max = 55
        grid.add_widget(x_axis, row=2, col=1)
        grid.add_widget(y_axis, row=1, col=0)

        # Link the axes to the ViewBox
        x_axis.link_view(self.diagram)
        y_axis.link_view(self.diagram)
        
    def update_intensity_plot(self):
        selected_element = self.main_window.main_ui.vispy_canvas_wrapper.selected_object
        if isinstance(selected_element, (LineControlPoints, ControlPoints)):
            selected_element = selected_element.parent
        if isinstance(selected_element, (EditLineVisual, EditRectVisual)):
            image = self.main_window.main_ui.data_handler.img_data
            
            if isinstance(selected_element, EditLineVisual):
                length = selected_element.length
                intensity = selected_element.intensity_profile(image=image, 
                                                               n=2*int(length))
            elif isinstance(selected_element, EditRectVisual):
                length = selected_element.width
                intensity = selected_element.intensity_profile(image=image, 
                                                               n_x=2*int(length),
                                                               n_y=2*int(selected_element.height))
            distance = np.linspace(0, length, len(intensity))
            
            # automatically set correct axis limits
            self.diagram.camera.set_range(x=(0, length), y=(np.min(intensity), np.max(intensity)))
            # update the line plot
            self.intensity_line.set_data((distance, intensity))
    
            
    
    

    