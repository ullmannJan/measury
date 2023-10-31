import numpy as np
from numpy.linalg import norm
import cv2
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label, transforms, MatrixTransform
from DrawableObjects import EditEllipseVisual, EditRectVisual


class VispyCanvas(SceneCanvas):
    """ Canvas for displaying the vispy instance"""

    CANVAS_SHAPE = (800, 600)
    main_ui = None

    line = None
    line_start = None

    


    def __init__(self, file_handler):
        
        self.file_handler = file_handler

        SceneCanvas.__init__(self,size=self.CANVAS_SHAPE, 
                                  bgcolor=(240/255, 240/255, 240/255,1),
                                  keys='interactive')
        self.unfreeze()
        
        self.grid = self.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(row=1, col=1, bgcolor='black')

        self.image = visuals.Image(data = None,
                            texture_format="auto",
                            interpolation='nearest',
                            cmap="viridis",
                            parent=self.view.scene)
        
        
        self.start_state = True

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


        self.load_image_label = Label("Click here to select\nan image", color='white', font_size=16)
        self.grid.add_widget(self.load_image_label, row=1, col=1)

        
        # camera
        self.view.camera.flip = (0,1,0)
        self.view.camera.set_range(x=(0,1),
                                   y=(0,1), 
                                   margin=0)  
              

        # for manipulating shapes
        self.selected_object = None
        self.selected_point = None
        self.mouse_start_pos = [0, 0]

        self.freeze()


    def update_image(self):

        if self.file_handler.img_path is not None:
            try:
                self.title_label.text = self.file_handler.img_path

                self.file_handler.img_data = cv2.imread(self.file_handler.img_path)
                
                self.draw_image()

                self.view.camera = "panzoom"
                self.view.camera.set_range(x=(0,self.file_handler.img_data.shape[1]),
                                            y=(0,self.file_handler.img_data.shape[0]), margin=0)
                self.view.camera.aspect = 1
                self.view.camera.flip = (0,1,0)

                self.xaxis.link_view(self.view)
                self.yaxis.link_view(self.view)
                
                self.start_state = False

            except Exception as error:
                # handle the exception                                
                self.main_ui.raise_error(error)
            
            self.remove_load_text()
    
    def draw_image(self, img_data=None):
        if img_data is None:
            img_data = self.file_handler.img_data
        self.image.set_data(img_data)

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
        # transform so that coordinates start at 0 in self.view window
        tr = self.scene.node_transform(self.view)
        # only activate when over self.view by looking if coordinates < 0 or > size of self.view
        if not( (tr.map(event.pos)[:2] > self.view.size).any() or (tr.map(event.pos)[:2] < (0,0)).any() ):
            
            if self.start_state:
                # when no image is selected open file opening sequence by clicking
                self.main_ui.select_sem_file()
            else:
                # main use of program

                # transform to get image pixel coordinates
                tr_image = self.scene.node_transform(self.image)
                mouse_image_coords = tr_image.map(event.pos)[:2]
                m_i_x, m_i_y = np.floor(mouse_image_coords).astype(int)

                match self.main_ui.tools.checkedId():
                    ## move image
                    case 0:
                        # enable panning
                        self.view.camera._viewbox.events.mouse_move.connect(
                            self.view.camera.viewbox_mouse_event)
                    
                    ## line
                    case 1:
                        #disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event)
                        if event.button == 1:
                            if self.line_start is None:
                                # first point stored
                                self.line_start = mouse_image_coords
                            else:
                                # save both points 
                                print(self.line_start, mouse_image_coords)
                                scaling_factor = 1
                                if self.main_ui.length_edit.text() and self.main_ui.pixel_edit.text():
                                    scaling_factor = float(self.main_ui.length_edit.text())/float(self.main_ui.pixel_edit.text())
                                print(scaling_factor*abs(np.linalg.norm(self.line_start-mouse_image_coords)))
                                
                                # self.main_ui.table.show()

                                #second point captured
                                self.line_start = None
                        elif event.button == 2:
                            self.line.visible = False
                            self.line_start = None
                            

                    ## circle
                    case 2 | 3:
                        #disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event)
                        
                        tr = self.scene.node_transform(self.view.scene)
                        pos = tr.map(event.pos)
                        self.view.interactive = False
                        selected = self.visual_at(event.pos)
                        self.view.interactive = True
                        if self.selected_object is not None:
                            self.selected_object.select(False)
                            self.selected_object = None

                        if event.button == 1:
                            
                            if selected is not None:
                                self.selected_object = selected.parent
                                # update transform to selected object
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)

                                self.selected_object.select(True, obj=selected)
                                self.selected_object.start_move(pos)
                                self.mouse_start_pos = event.pos

                            # create new object:
                            if self.selected_object is None:
                                
                                if self.main_ui.tools.checkedId() == 2:
                                    new_object = EditEllipseVisual(parent=self.view.scene)
                                elif self.main_ui.tools.checkedId() == 3:
                                    new_object = EditRectVisual(parent=self.view.scene)

                                new_object.select_creation_controlpoint()
                                new_object.set_center(pos[0:2])
                                self.selected_object = new_object.control_points
                                self.selected_object.transform = transforms.STTransform(translate=(0, 0, -2))
                                new_object.transform = transforms.STTransform(translate=(0, 0, -1))

                        if event.button == 2:  # right button deletes object
                            if selected is not None:
                                selected.parent.parent = None
                                self.selected_object = None
                            
                        
                        
                        



                    ## rectangle



                    ## identify scaling
                    case 4:
                        #disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event)

                        # get width of scaling bar and show it in image
                        self.find_scaling_bar_width((m_i_x, m_i_y))

    def find_scaling_bar_width(self, seed_point):
        # get width of scaling bar by floodFilling an area of similar pixels.
        # The start point needs to be given

        # create copy of image which can be modified
        img_data_modified = self.file_handler.img_data.copy()
        cv2.floodFill(img_data_modified, 
                        None,
                        seed_point,
                        newVal=(255, 0, 0),
                        loDiff=(10,10,10),
                        upDiff=(10,10,10)
                    )
        
        self.draw_image(img_data=img_data_modified)

        non_zero_indices = np.nonzero(np.sum(self.file_handler.img_data-img_data_modified, axis=2))

        # plus one to account for the start pixel
        scale_px = np.max(non_zero_indices[1])-np.min(non_zero_indices[1]) + 1

        self.main_ui.pixel_edit.setText(str(scale_px))
        self.scene.update()

    def on_mouse_move(self, event):

        # transform so that coordinates start at 0 in self.view window
        tr = self.scene.node_transform(self.view)
        # only activate when over self.view by looking if coordinates < 0 or > size of self.view
        if not( (tr.map(event.pos)[:2] > self.view.size).any() or (tr.map(event.pos)[:2] < (0,0)).any() ):
            
            if not self.start_state:
                # transform to get image pixel coordinates
                tr_image = self.scene.node_transform(self.image)
                mouse_image_coords = tr_image.map(event.pos)[:2]

                match self.main_ui.tools.checkedId():
                    ## line
                    case 1:
                        if self.line_start is not None:
                            if self.line is None:
                                self.line = visuals.Line(pos=np.array([self.line_start, mouse_image_coords]),
                                                         width=5, 
                                                         color=(1,1,1,0.7),
                                                         method='gl',
                                                         antialias=True,
                                                         parent=self.view.scene)
                                self.line.transform = transforms.STTransform(translate=(0, 0, -1))
                            else:
                                self.line.visible = True
                                self.line.set_data(np.array([self.line_start, mouse_image_coords]))
                    ## circle
                    case 2 | 3:
                        if event.button == 1:
                            if self.selected_object is not None:
                                # update transform to selected object
                                # check if letter k is pressed
                                modifiers = [key.name for key in event.modifiers]
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)
                                if 'Shift' in modifiers:
                                    
                                    try:
                                        x = (pos[0:2] - self.selected_object.center)[0]
                                        y = (pos[0:2] - self.selected_object.center)[1]
                                        angle = np.arctan(y/x)
                                        self.selected_object.rotate(-angle)
                                    except:
                                        angle = 90
                                        self.selected_object.rotate(angle)
                                else:
                                    
                                    self.selected_object.move(pos[0:2])

                        else:
                            None
                    ## rectangle

    # later improvements
    # def on_key_press(self, event):
    #     print(event.key)
    #     if event.key in ['K']:
    #         former_tool_id = self.main_ui.tools.checkedId()
    #         self.main_ui.tools.button(0).setChecked(True)


                        
