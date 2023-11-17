import numpy as np
from numpy.linalg import norm
import cv2
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label, transforms
from semmy.drawable_objects import EditEllipseVisual, EditRectVisual, ControlPoints, EditLineVisual, LineControlPoints

# from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
# from PyQt6.QtGui import QCursor

class VispyCanvas(SceneCanvas):
    """ Canvas for displaying the vispy instance"""

    CANVAS_SHAPE = (800, 600)
    main_ui = None

    def __init__(self, data_handler, img=None):
        
        self.data_handler = data_handler

        SceneCanvas.__init__(self,
                             size=self.CANVAS_SHAPE, 
                             bgcolor=(240/255, 240/255, 240/255,1),
                             keys=dict(delete=self.delete_object)
                            )
        self.unfreeze()
        
        self.grid = self.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(row=1, col=1, bgcolor='black')

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


        self.load_image_label = Label("Click here to select\nan image", color='white', font_size=16)
        self.grid.add_widget(self.load_image_label, row=1, col=1)
        
        # camera
        self.view.camera.flip = (0,1,0)
        self.view.camera.set_range(x=(0,1),
                                   y=(0,1), 
                                   margin=0)  
              
        # load standard picture in development mode
        if img is None:
            self.start_state = True
        else:
            self.data_handler.img_path = img
            self.update_image()

        # for manipulating shapes
        self.selected_object = None
        self.selected_point = None

        self.freeze()


    def update_image(self):

        if self.data_handler.img_path is not None:
            try:
                self.title_label.text = self.data_handler.img_path

                # opencv reads images in BGR format, so we need to convert it to RGB
                BGR_img = cv2.imread(self.data_handler.img_path)
                self.data_handler.img_data = cv2.cvtColor(BGR_img, cv2.COLOR_BGR2RGB)
                
                self.draw_image()

                self.view.camera = "panzoom"
                self.view.camera.set_range(x=(0,self.data_handler.img_data.shape[1]),
                                            y=(0,self.data_handler.img_data.shape[0]), margin=0)
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
            img_data = self.data_handler.img_data
        self.image.set_data(img_data)

    def center_image(self):
        if self.data_handler.img_data is not None:
            self.view.camera.set_range(x=(0,self.data_handler.img_data.shape[1]),
                                       y=(0,self.data_handler.img_data.shape[0]), margin=0)
            

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
                # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.ArrowCursor)) 
                 
                if event.button == 3: # mouse wheel button for changing fov
                    # enable panning
                    self.view.camera._viewbox.events.mouse_move.connect(
                        self.view.camera.viewbox_mouse_event)
                    
                    # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))                    

                    # unselect object
                    if self.selected_object is not None:
                        self.selected_object.select(False)
                        self.selected_object = None

                else:
                    match self.main_ui.tools.checkedButton().text():

                        case "&move":
                            # enable panning
                            self.view.camera._viewbox.events.mouse_move.connect(
                                self.view.camera.viewbox_mouse_event)
                            
                            # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))                    

                            # unselect object
                            if self.selected_object is not None:
                                self.selected_object.select(False)
                                self.selected_object = None

                        case "&line" | "&circle" | "&rectangle" | "&angle":
                            #disable panning
                            self.view.camera._viewbox.events.mouse_move.disconnect(
                                self.view.camera.viewbox_mouse_event)
                            
                            tr = self.scene.node_transform(self.view.scene)
                            pos = tr.map(event.pos)
                            self.view.interactive = False
                            selected = self.visual_at(event.pos)
                            self.view.interactive = True
                            # unselect object to create rom of new one
                            if self.selected_object is not None:
                                self.selected_object.select(False)
                                self.selected_object = None

                            if event.button == 1:
                                # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))                    

                                
                                if selected is not None:
                                    self.selected_object = selected.parent

                                    # update transform to selected object
                                    tr = self.scene.node_transform(self.selected_object)
                                    pos = tr.map(event.pos)

                                    self.selected_object.select(True, obj=selected)
                                    self.selected_object.start_move(pos)

                                    # update ui to display properties of selected object
                                    self.selection_update()

                                # create new object:
                                if self.selected_object is None:
                                    # if it is the line object
                                    match self.main_ui.tools.checkedButton().text():
                                        case "&line":
                                            new_object = EditLineVisual(parent=self.view.scene)
                                        case "&circle":
                                            new_object = EditEllipseVisual(parent=self.view.scene)
                                        case "&rectangle":
                                            new_object = EditRectVisual(parent=self.view.scene)
                                        case "&angle":
                                            new_object = EditLineVisual(parent=self.view.scene, num_points=3)

                                    new_object.set_center(pos[0:2])
                                        
                                    new_object.select_creation_controlpoint()
                                    new_object.transform = transforms.STTransform(translate=(0, 0, -1))
                                    self.selected_object = new_object.control_points
                                    self.selected_object.transform = transforms.STTransform(translate=(0, 0, -2))

                                    # TODO: save object in database
                                    structure_name = self.main_ui.structure_edit.text()
                                    self.data_handler.save_object(structure_name, new_object)

                                    # update ui where data is shown
                                    self.selection_update(object=new_object)
                                    

                            if event.button == 2:  # right button deletes object
                                # not self.selected_object because we want to delete it on hover too
                                if selected is not None:
                                    self.delete_object(object=selected.parent)

                                

                        case "&identify scaling":
                            #disable panning
                            self.view.camera._viewbox.events.mouse_move.disconnect(
                                self.view.camera.viewbox_mouse_event)
                            
                            if event.button == 1:

                                # transform to get image pixel coordinates
                                tr_image = self.scene.node_transform(self.image)
                                mouse_image_coords = tr_image.map(event.pos)[:2]
                                # mouse_click_coordinates
                                m_i_x, m_i_y = np.floor(mouse_image_coords).astype(int)

                                # get width of scaling bar and show it in image
                                self.find_scaling_bar_width((m_i_x, m_i_y))
                            
                            # right click to delete scaling identification
                            if event.button == 2:
                                self.draw_image(self.data_handler.img_data)
                                self.main_ui.pixel_edit.setText(None)


    def find_scaling_bar_width(self, seed_point):
        # get width of scaling bar by floodFilling an area of similar pixels.
        # The start point needs to be given

        # create copy of image which can be modified
        img_data_modified = self.data_handler.img_data.copy()
        cv2.floodFill(img_data_modified, 
                        None,
                        seed_point,
                        newVal=(255, 0, 0),
                        loDiff=(10,10,10),
                        upDiff=(10,10,10)
                    )
        
        self.draw_image(img_data=img_data_modified)

        non_zero_indices = np.nonzero(np.sum(self.data_handler.img_data-img_data_modified, axis=2))

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
                
                # Check if the mouse wheel button is being dragged

                match event.button:
                    case 1: 
                        if event.is_dragging: # Check if the left mouse button is being dragged
                            
                            if self.selected_object is not None:
                                modifiers = [key.name for key in event.modifiers]
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)

                                match self.main_ui.tools.checkedButton().text():
                                        
                                    case "&line" | "&circle" | "&rectangle" | "&angle":
                                

                                        if 'Shift' in modifiers and not isinstance(self.selected_object, (LineControlPoints, EditLineVisual)):

                                            # calculate angle of current position
                                            x, y = pos[0:2] - self.selected_object.center
                                            angle = np.arctan2(-y,x)

                                            self.selected_object.rotate(angle)
                                            
                                        else:
                                            
                                            self.selected_object.move(pos[0:2], modifiers=modifiers)

                                        # update ui to display properties of selected object
                                        self.selection_update()

                    case 3:
                        if event.is_dragging:  
                            tr = self.view.node_transform(self.view.scene)
                            dpos = tr.map(event.last_event.pos)[:2] -tr.map(event.pos)[:2]  # Calculate the change in position of the mouse
                            self.view.camera.pan(dpos)  # Pan the camera based on the mouse movement



    def selection_update(self, object=None):

        if object is None:
            object = self.selected_object
        if isinstance(object, (ControlPoints, LineControlPoints)):
            object = self.selected_object.parent

        self.main_ui.selected_object_table.clearContents()
        self.main_ui.selected_object_table.setRowCount(0)
        self.main_ui.selected_object_box.setTitle(f"Selected Object: {object}")
        # if object is still none clear table and return
        if object is None:
            return
        
        props = object.output_properties()
        self.main_ui.selected_object_table.setRowCount(len(props.keys()))
        for i, key in enumerate(props):
            self.main_ui.selected_object_table.setItem(i, 0, 
                                QTableWidgetItem(key))
            
            value, unit = props[key]
            # if there is a conversion possible
            if self.main_ui.scaling != 1 :
                scaled_length = 1 * np.array(value)
                if key in ['length', 'area', 'radius', 'width', 'height', 'center']:
                    scaled_length *= self.main_ui.scaling
            
                    self.main_ui.selected_object_table.setItem(i, 2, 
                            QTableWidgetItem(self.main_ui.units_dd.currentText()))
                else:
                    self.main_ui.selected_object_table.setItem(i, 2, 
                            QTableWidgetItem(unit))
                self.main_ui.selected_object_table.setItem(i, 1, 
                            QTableWidgetItem(str(scaled_length)))

            if True: # if setting selected that pixels should be shown too
                self.main_ui.selected_object_table.setItem(i, 3, 
                            QTableWidgetItem(str(value)))
                self.main_ui.selected_object_table.setItem(i, 4, 
                            QTableWidgetItem(unit))
            
        self.main_ui.selected_object_table.resizeColumnsToContents()


    def delete_object(self, object=None):
        # delete selected object if no other is given
        if object is None:
            object = self.selected_object
        # delete object
        if object is not None:
            self.data_handler.delete_object(object)
            object.delete()
            self.selected_object = None
        self.selection_update()

    # later improvements
    # def on_key_press(self, event):
    #     print(event.key)
    #     if event.key in ['K']:
    #         former_tool_id = self.main_ui.tools.checkedId()
    #         self.main_ui.tools.button(0).setChecked(True)


                        
