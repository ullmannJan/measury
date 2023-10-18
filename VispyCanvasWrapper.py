import numpy as np
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label
from vispy.io import load_data_file, read_png

class VispyCanvasWrapper():

    main_ui = None 

    def __init__(self):

        self.img = np.flipud(read_png("img/black.png"))
        self.no_image_selected = True

        self.canvas = SceneCanvas(size=(self.img.shape[1], 
                                        self.img.shape[0]), 
                                        bgcolor=(240/255, 240/255, 240/255,1))

        self.grid = self.canvas.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(1, 1, bgcolor='black')
        self.image = visuals.Image(
            self.img,
            texture_format="auto",
            interpolation='nearest',
            cmap="viridis",
            parent=self.view.scene,
        )

        # title
        title = Label("SEM-Image", color='black', font_size=12)
        title.height_max = 40
        self.grid.add_widget(title, row=0, col=0, col_span=3)

        
        # y axis
        yaxis = AxisWidget(orientation='left',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        yaxis.width_max = 80
        self.grid.add_widget(yaxis, row=1, col=0)
        
        # x axis
        xaxis = AxisWidget(orientation='bottom',
                                axis_font_size=12,
                                axis_label_margin=0,
                                tick_label_margin=15,
                                text_color='black')
        xaxis.height_max = 50
        self.grid.add_widget(xaxis, row=2, col=1)

        # padding right
        right_padding = self.grid.add_widget(row=1, col=2, row_span=2)
        right_padding.width_max =25

        # camera
        if self.no_image_selected:
            self.load_image_label = Label("Please select\nan image", color='white', font_size=20)
            self.grid.add_widget(self.load_image_label, row=1, col=1)
        else:
            self.view.camera = "panzoom"
        self.view.camera.set_range(x=(0,self.image.size[0]),
                                   y=(0,self.image.size[1]), 
                                   margin=0)
        self.view.camera.aspect = 1

        xaxis.link_view(self.view)
        yaxis.link_view(self.view)
    
    def update_image(self, img="img/2023-04-24_PTB_D5_10-01.jpg"):

        self.img = np.flipud(read_png(img))
        self.image = visuals.Image(
            self.img,
            texture_format="auto",
            interpolation='nearest',
            cmap="viridis",
            parent=self.view.scene,
        )
        if img is not None:
            self.load_image_label = None
            self.view.camera = "panzoom"
