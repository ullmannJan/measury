import numpy as np
import cv2
from numpy.typing import NDArray
from vispy.color import Colormap
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label
from vispy.io import load_data_file, read_png
           
class VispyCanvas(SceneCanvas):
    """ Canvas """
    CANVAS_SHAPE = (800, 600)
    main_ui = None

    def __init__(self, file_handler):
        
        self.file_handler = file_handler

        SceneCanvas.__init__(self,size=self.CANVAS_SHAPE, 
                                  bgcolor=(240/255, 240/255, 240/255,1),
                                  keys='interactive')
        self.unfreeze()
        
        self.grid = self.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(1, 1, bgcolor='black')

        self.image = visuals.Image(data = None,
                            texture_format="auto",
                            interpolation='nearest',
                            cmap="viridis",
                            parent=self.view.scene)

        # title
        self.title_label = Label("SEM-Image", color='black', font_size=12)
        self.title_label.height_max = 40
        self.grid.add_widget(self.title_label, row=0, col=0, col_span=3)

        # y axis
        self.yaxis = AxisWidget(orientation='left',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        self.yaxis.width_max = 80
        self.grid.add_widget(self.yaxis, row=1, col=0)
        
        # x axis
        self.xaxis = AxisWidget(orientation='bottom',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        self.xaxis.height_max = 50
        self.grid.add_widget(self.xaxis, row=2, col=1)

        # padding right
        right_padding = self.grid.add_widget(row=1, col=2, row_span=2)
        right_padding.width_max =25


        self.load_image_label = Label("Please select\nan image", color='white', font_size=16)
        self.grid.add_widget(self.load_image_label, row=1, col=1)

        
        # camera
        self.view.camera.set_range(x=(0,1),
                                   y=(0,1), 
                                   margin=0)

        self.freeze()

    def update_image(self):
        # self.file_handler.img_path="img/2023-04-24_PTB_D5_10-01.jpg"
        # self.file_handler.img_path=None

        if self.file_handler.img_path is not None:
            try:
                self.remove_load_text()

                self.title_label.text = self.file_handler.img_path

                self.file_handler.img_data = np.flipud(cv2.imread(self.file_handler.img_path))
                
                self.image.set_data(self.file_handler.img_data)

                self.view.camera = "panzoom"
                self.view.camera.set_range(x=(0,self.file_handler.img_data.shape[1]),
                                            y=(0,self.file_handler.img_data.shape[0]), margin=0)
                self.view.camera.aspect = 1

                self.xaxis.link_view(self.view)
                self.yaxis.link_view(self.view)
            except Exception as error:
                # handle the exception                                
                self.main_ui.raise_error(error)

    def center_image(self):
        if self.file_handler.img_data is not None:
            self.view.camera.set_range(x=(0,self.file_handler.img_data.shape[1]),
                                       y=(0,self.file_handler.img_data.shape[0]), margin=0)

    def add_load_text(self):
         # load image label
         self.load_image_label.visible = True

    def remove_load_text(self):
        # self.load_image_label.text = ""
        self.load_image_label.visible = False

    def on_mouse_press(self, event):
        print(event)
        if event.button == 1:
            print(1)
        if event.button == 2:
            print(2)
        print(event.pos)
