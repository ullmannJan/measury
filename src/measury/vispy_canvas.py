# absolute imports
import numpy as np
import cv2
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label
from vispy.visuals.transforms import linear
from PySide6.QtWidgets import QInputDialog
from PySide6.QtGui import QUndoCommand

# relative imports
from .drawable_objects import (
    EditEllipseVisual,
    EditRectVisual,
    ControlPoints,
    EditLineVisual,
    LineControlPoints,
    EditPolygonVisual,
    Markers,
)

class VispyCanvas(SceneCanvas):
    """Canvas for displaying the vispy instance"""

    CANVAS_SHAPE = (800, 600)
    main_ui = None
    main_window = None
    scale_bar_params = (None, True, None, None) # seed point, relative, threshold, direction
    text_color = "black"
    current_move = None
    origin = np.zeros(2)

    def __init__(self, main_window):

        self.data_handler = main_window.data_handler
        self.main_window = main_window

        SceneCanvas.__init__(
            self, size=self.CANVAS_SHAPE, keys=dict(delete=self.delete_object_w_undo)
        )
        self.unfreeze()
        # get background color of qt session
        self.update_background_color()

        if self.main_window.is_dark_mode():
            self.text_color = "white"

        self.grid = self.central_widget.add_grid(margin=0)

        self.view = self.grid.add_view(row=1, col=1, bgcolor="black")

        self.image = visuals.Image(
            data=None,
            texture_format="auto",
            interpolation=self.main_window.settings.value("graphics/image_rendering"),
            cmap="viridis",
            parent=self.view.scene,
        )

        # title
        self.title_label = Label(
            "Microscope-Image", color=self.text_color, font_size=12
        )
        self.title_label.height_max = 40
        self.grid.add_widget(self.title_label, row=0, col=0, col_span=3)

        # y axis
        self.yaxis = AxisWidget(
            orientation="left",
            axis_font_size=12,
            axis_label_margin=0,
            tick_label_margin=15,
            text_color=self.text_color,
        )
        self.yaxis.width_max = 80
        self.grid.add_widget(self.yaxis, row=1, col=0)

        # x axis
        self.xaxis = AxisWidget(
            orientation="bottom",
            axis_font_size=12,
            axis_label_margin=0,
            tick_label_margin=15,
            text_color=self.text_color,
        )
        self.xaxis.height_max = 50
        self.grid.add_widget(self.xaxis, row=2, col=1)

        self.update_axis_color()

        # padding right
        right_padding = self.grid.add_widget(row=1, col=2, row_span=2)
        right_padding.width_max = 5

        self.load_image_label = Label(
            "Click here to select\nan image", color="white", font_size=16
        )
        self.grid.add_widget(self.load_image_label, row=1, col=1)

        # camera
        self.view.camera.set_range(x=(0, 1), y=(0, 1), margin=0)

        self.start_state = True
        self.update_image()

        # for manipulating shapes
        self.selected_object = None
        self.selected_point = None

        self.freeze()
        
    def update_file_path(self, file_path=None):
        """Writes the filepath to the title label above the image
        
        Args:
            file_path (Path): file_path to the image
        """
        if file_path is None:
            file_path = self.data_handler.file_path
        if file_path is not None:
            self.title_label.text = file_path.name

    def update_image(self):
        """Update the image in the vispy canvas and also the 
        file path shown above the image"""

        # if there is no image loaded, do nothing
        if self.data_handler.file_path is not None:
            try:
                # opencv reads images in BGR format,
                # so we need to convert it to RGB
                self.data_handler.logger.debug(
                    f"update data_handler.file_path = {self.data_handler.file_path}"
                )
                BGR_img = cv2.imdecode(
                    np.frombuffer(self.data_handler.img_byte_stream, dtype=np.uint8),
                    cv2.IMREAD_UNCHANGED,
                )
                self.data_handler.img_data = cv2.cvtColor(BGR_img, cv2.COLOR_BGR2RGB)

                self.draw_image()

                self.view.camera = "panzoom"
                self.center_image()
                self.view.camera.aspect = 1
                self.view.camera.flip = (0, 1, 0)

                self.xaxis.link_view(self.view)
                self.yaxis.link_view(self.view)

                self.update_file_path()

            except Exception as error:
                # handle the exception
                if self.main_window is not None:
                    self.main_window.raise_error(f"Image could not be loaded: {error}")
                    return

            self.start_state = False
            self.remove_load_text()

    def draw_image(self, img_data=None):
        if img_data is None:
            img_data = self.data_handler.img_data
        self.data_handler.logger.debug("setting vispy image data")
        if img_data is not None:
            self.image.set_data(img_data)
        self.image.interpolation = self.main_window.settings.value(
            "graphics/image_rendering"
        )

    def center_image(self):
        try:
            if self.data_handler.img_data is not None:
                self.view.camera.set_range(
                    x=(0-self.origin[0], self.data_handler.img_data.shape[1]-self.origin[0]),
                    y=(0-self.origin[1], self.data_handler.img_data.shape[0]-self.origin[1]),
                    margin=0,
                )
        except Exception as error:
            self.main_window.raise_error(f"Image could not be centered: {error}")
            
    def rotate_image(self, direction="clockwise", rotate_objects=True):
        self.data_handler.logger.debug(f"rotate image")
        if self.data_handler.img_data is not None:
            if direction == "clockwise":
                new_origin = np.array([self.data_handler.img_data.shape[0]-self.origin[1], 
                                    self.origin[0]])

                self.data_handler.img_rotation += 90
                direction_hint = cv2.ROTATE_90_CLOCKWISE
            else:
                # rotate counter clockwise
                new_origin = np.array([self.origin[1],
                                        self.data_handler.img_data.shape[1] - self.origin[0]])
                self.data_handler.img_rotation -= 90
                direction_hint = cv2.ROTATE_90_COUNTERCLOCKWISE
            
            # updating objects  
            if rotate_objects:
                self.move_all_objects(self.origin)
                self.set_origin(new_origin, move_objects=False)
                self.rotate_all_objects(direction)
                self.move_all_objects(-new_origin)
            else:
                self.set_origin(new_origin, move_objects=False)
            self.data_handler.img_data = cv2.rotate(self.data_handler.img_data, direction_hint)
            self.draw_image()
            self.center_image()
            
    def rotate_coordinates_90(self, coords, direction="clockwise"):
        """Rotate coordinates by 90 degrees in the given direction, 

        Args:
            coords (np.ndarray): coordinates to rotate
            direction (cv2.rotation_type, optional): direction of rotation. Defaults to cv2.ROTATE_90_CLOCKWISE.

        Returns:
            np.ndarray: rotated coordinates
        """
        new_coords = np.empty_like(coords)
        self.data_handler.logger.debug("rotate coordinates " + direction)
        if direction == "clockwise":
            new_coords[:,0] = self.data_handler.img_data.shape[0] - coords[:,1]
            new_coords[:,1] = coords[:,0]
        else:
            new_coords[:,0] = coords[:,1]
            new_coords[:,1] = self.data_handler.img_data.shape[1] - coords[:,0]
        return new_coords
            
    def rotate_all_objects(self, direction="clockwise"):
        """Rotate all objects by a given angle"""
        self.data_handler.logger.debug("rotate all objects")
        for structure in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[structure]:
                # show object
                if isinstance(obj, EditLineVisual):
                    new_coords = self.rotate_coordinates_90(obj.coords, direction)
                    obj.coords = new_coords
                    obj.update_from_controlpoints()
                else:
                    if direction == 'clockwise':
                        obj.angle += np.pi/2
                    else:
                        obj.angle -= np.pi/2
                    
                    obj.center = self.rotate_coordinates_90(obj.center[np.newaxis, :], 
                                                            direction)[0]
                    obj.update_from_controlpoints()
                    
        self.scene.update()  
            
        
    def rotate_image_w_undo(self):
        command = RotateImageCommand(self)
        self.main_window.undo_stack.push(command)

    def add_load_text(self):
        # load image label
        self.load_image_label.visible = True

    def remove_load_text(self):
        # self.load_image_label.text = ""
        self.load_image_label.visible = False

    def on_mouse_release(self, event):
        # transform so that coordinates start at 0 in self.view window
        tr = self.scene.node_transform(self.view)
        # only activate when over self.view by looking
        # if coordinates < 0 or > size of self.view
        if not (
            (tr.map(event.pos)[:2] > self.view.size).any()
            or (tr.map(event.pos)[:2] < (0, 0)).any()
        ):

            if self.start_state:
                # when no image is selected open file opening
                #  sequence by clicking
                self.main_ui.select_file()
            elif event.button == 1:
                match self.main_ui.tools_buttons.checkedButton().text(): 
                    case "Line" | "Ellipse" | "Rectangle" | "Angle" | "Multi-Line" | "Polygon" | "Edit":
                        
                        # multi-line is not finished yet
                        if isinstance(self.selected_object, LineControlPoints):
                            if self.selected_object.continue_adding_points:
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)
                                self.add_point_w_undo(self.selected_object, pos[:2])
                            elif self.current_move.check_movement():
                                self.main_window.undo_stack.push(self.current_move)
                                
                                
                        # redo move object command to save current location
                        elif self.current_move is not None:
                            # if object was moved, put it on undo stack
                            if self.current_move.check_movement():
                                self.main_window.undo_stack.push(self.current_move)

        # if click is above box
        elif (
            tr.map(event.pos)[1] < 0 # above box
            and event.pos[1] > 0 # but still in vispy canvas
            and tr.map(event.pos)[0] > 0 # right of start of scene
            and tr.map(event.pos)[0] < self.view.size[0] # left of end of scene
        ):
            if not self.data_handler.file_path:
                self.main_ui.select_file()
            elif self.data_handler.file_path.name != "clipboard":
                self.data_handler.open_file_location(self.data_handler.file_path)
                        

    def on_mouse_press(self, event):
        # transform so that coordinates start at 0 in self.view window
        tr = self.scene.node_transform(self.view)
        # only activate when over self.view by looking
        #  if coordinates < 0 or > size of self.view
        if not (
            (tr.map(event.pos)[:2] > self.view.size).any()
            or (tr.map(event.pos)[:2] < (0, 0)).any()
        ):

            # if in start state, dont do anything as we are looking
            # at mouse_released for that
            if self.start_state:
                return

            # main use of program
            if event.button == 3:  # mouse wheel button for changing fov
                # enable panning
                self.view.camera._viewbox.events.mouse_move.connect(
                    self.view.camera.viewbox_mouse_event
                )

            else:
                match self.main_ui.tools_buttons.checkedButton().text():

                    case "Move":
                        # enable panning
                        self.view.camera._viewbox.events.mouse_move.connect(
                            self.view.camera.viewbox_mouse_event
                        )

                        # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))

                        # unselect object
                        self.unselect()

                    case "Set Origin":
                        # disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event
                        )

                        tr = self.scene.node_transform(self.view.scene)
                        pos = tr.map(event.pos)[:2]

                        # unselect object
                        self.unselect()

                        self.set_origin_w_undo(pos+self.origin)

                    case "Select":
                        # disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event
                        )

                        tr = self.scene.node_transform(self.view.scene)
                        pos = tr.map(event.pos)
                        self.view.interactive = False
                        selected = self.visual_at(event.pos)
                        self.view.interactive = True

                        if event.button == 1:

                            if selected is not None:
                                # unselect object to create room of new one
                                self.unselect()

                                self.selected_object = selected.parent

                                # update transform to selected object
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)

                                self.selected_object.select(True, obj=selected)
                                self.selected_object.start_move(pos)
                        
                                # update ui to display properties of selected object
                                self.selection_update()

                    case "Line" | "Ellipse" | "Rectangle" | "Angle" | "Multi-Line" | "Polygon" | "Edit":
                        # disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event
                        )

                        tr = self.scene.node_transform(self.view.scene)
                        pos = tr.map(event.pos)
                        self.view.interactive = False
                        # selected is what we clicked on 
                        # 6 as the markers are 8 wide and have a 1 pixel border 8+2*1=10 < 13=2*6+1 
                        selected_list = self.visuals_at(event.pos, 6)
                        selected = None
                        if selected_list:
                            # check if a marker is in the list, we want the last one, 
                            # so we iterate from the back
                            for selected in reversed(selected_list):
                                if isinstance(selected, Markers):
                                    break
                            else:
                                selected = selected_list[0]
                        
                        self.view.interactive = True

                        match event.button:
                            case 1:

                                # unselect object to create room for new one
                                self.unselect()                                
                                
                                # edit object
                                if selected is not None:    

                                    self.selected_object = selected.parent
                                    # update transform to selected object
                                    tr = self.scene.node_transform(self.selected_object)
                                    pos = tr.map(event.pos)

                                    self.selected_object.select(True, obj=selected)
                                    self.selected_object.start_move(pos)
                                    # self.move_object_w_undo(self.selected_object)
                                    
                                    # start a possible move
                                    if not isinstance(self.selected_object, LineControlPoints):    
                                        self.current_move = MoveObjectCommand(self, self.selected_object)
                                        self.data_handler.logger.debug("start moving object")
                                    
                                    elif not self.selected_object.continue_adding_points:
                                        self.current_move = MoveObjectCommand(self, self.selected_object)
                                        self.data_handler.logger.debug("start moving object")

                                    # update ui to display properties of selected object
                                    self.selection_update()
                                else:
                                    self.current_move = None
                                
                                # create new object:
                                if self.selected_object is None:

                                    match self.main_ui.tools_buttons.checkedButton().text():
                                        case "Line":
                                            new_object = EditLineVisual(
                                                parent=self.view.scene,
                                                settings=self.main_window.settings,
                                                num_points=2,
                                            )
                                        case "Ellipse":
                                            new_object = EditEllipseVisual(
                                                parent=self.view.scene,
                                                settings=self.main_window.settings,
                                            )
                                        case "Rectangle":
                                            new_object = EditRectVisual(
                                                parent=self.view.scene,
                                                settings=self.main_window.settings,
                                            )
                                        case "Angle":
                                            new_object = EditLineVisual(
                                                settings=self.main_window.settings,
                                                parent=self.view.scene,
                                                num_points=3,
                                            )
                                        case "Multi-Line":
                                            new_object = EditLineVisual(
                                                settings=self.main_window.settings,
                                                parent=self.view.scene,
                                                num_points=0,
                                            )
                                        case "Polygon":
                                            new_object = EditPolygonVisual(
                                                settings=self.main_window.settings,
                                                parent=self.view.scene)
                                        case "Edit":
                                            return
                                        
                                    # dont show object before it is added to drawing_data
                                    new_object.select(False)
                                    if self.check_creation_allowed(new_object):

                                        self.create_new_object_w_undo(
                                            new_object, pos=pos, selected=True
                                        )

                                        # update ui where data is shown
                                        self.selection_update(object=new_object)
                                        # if linecontrolpoint to get automatic line creation without draggin
                                        if isinstance(self.selected_object, LineControlPoints):
                                            last_cp = self.selected_object.control_points[-1]
                                            self.selected_object.select(True, last_cp)
                                    else:
                                        new_object.delete()

                                    
                            # delete object
                            case 2:  # right button deletes object
                                # not self.selected_object because we want to
                                # delete on hover too
                                if selected is not None:
                                    self.unselect()
                                    self.delete_object_w_undo(object=selected.parent)

                                    # TODO: live update of data window, when it is open
                                    # self.main_ui.update_data_window()
                            
                            # all other buttons just unselect the object
                            case _:
                                self.unselect()

                    case "Identify Scaling":
                        # disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event
                        )

                        if event.button == 1:

                            # transform to get image pixel coordinates
                            tr_image = self.scene.node_transform(self.image)
                            mouse_image_coords = tr_image.map(event.pos)[:2]
                            # mouse_click_coordinates
                            m_i_x, m_i_y = np.floor(mouse_image_coords).astype(int)

                            # get width of scaling bar and show it in image
                            self.find_scale_bar_width_w_undo(
                                (m_i_x, m_i_y), 
                                relative=False, 
                                threshold=self.main_ui.get_threshold(),
                                direction=self.main_ui.scaling_direction_dd.currentText()
                            )

                        # right click to delete scaling identification
                        if event.button == 2:
                            self.draw_image(self.data_handler.img_data)
                            self.main_ui.pixel_edit.setText(None)

    def create_new_object(
        self, new_object, pos=None, selected=False, structure_name=None
    ):

        self.data_handler.logger.info("Creating new Object")

        if pos is not None:
            new_object.set_center(pos[0:2])

        new_object.select(selected)
        if selected:
            new_object.select_creation_controlpoint()
            self.selected_object = new_object.control_points

        # save object in data_handler.drawing_data
        if structure_name is None:
            structure_name = self.main_ui.structure_dd.currentText()

        structure_name = self.data_handler.save_object(structure_name, new_object)

        if self.main_ui.structure_dd.currentText() == "":
            self.main_ui.structure_dd.setCurrentText(structure_name)

        self.main_ui.update_object_list()

        return structure_name

    def create_new_object_w_undo(
        self, new_object, pos=None, selected=False, structure_name=None
    ):
        command = CreateObjectCommand(self, new_object, pos, selected, structure_name)
        self.main_window.undo_stack.push(command)

    def update_object_colors(self):
        """
        Update the colors of the objects in the canvas.
        This method iterates over the drawing data stored in the data handler and updates the colors of each object.
        The colors are retrieved from the graphics settings in the main window.
        Returns:
            None
        """
        for name in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[name]:
                color = self.main_window.settings.value(
                    "graphics/object_color"
                ).getRgb()
                color = tuple([value / 255 for value in color])
                border_color = self.main_window.settings.value(
                    "graphics/object_border_color"
                ).getRgb()
                border_color = tuple([value / 255 for value in border_color])

                if isinstance(obj, (EditLineVisual)):
                    obj.line_color = border_color
                    obj.update_from_controlpoints()
                else:
                    obj.update_colors(color=color, border_color=border_color)
        self.scene.update()

    def update_background_color(self, color=None):
        if color is None:
            color = self.main_window.get_bg_color()
        # if self.main_window.is_dark_mode():
        #     color = "black"
        # else:
        #     color = (240/255, 240/255, 240/255, 1)

        # Convert QColor to RGBA tuple with values in range 0-1
        self.bgcolor = (
            color.red() / 255,
            color.green() / 255,
            color.blue() / 255,
            color.alpha() / 255,
        )
        self.update()

    def update_axis_color(self):

        if self.main_window.is_dark_mode():
            color = "white"
        else:
            color = "black"
        # Convert QColor to RGBA tuple with values in range 0-1
        # self.title_label.color = color
        self.xaxis.axis.text_color = color
        # self.xaxis.axis.axis_color = color
        self.xaxis.axis.tick_color = color
        self.yaxis.axis.text_color = color
        # self.yaxis.axis.axis_color = color
        self.yaxis.axis.tick_color = color

        # title color
        self.title_label._text_visual.color = color

    def background_color_changed(self):
        self.update_background_color()
        self.update_axis_color()

    def update_colors(self):
        self.update_background_color()
        self.update_axis_color()
        self.update_object_colors()

    def check_creation_allowed(self, new_object, structure_name=None):
        # check if object is allowed to be created
        if structure_name is None:
            structure_name = self.main_ui.structure_dd.currentText()

        if structure_name in self.data_handler.drawing_data.keys():
            structure_type = type(self.data_handler.drawing_data[structure_name][0])
        else:
            return True

        if isinstance(new_object, (structure_type)):
            return True
        else:
            # raise prompt to change structure name
            text, ok = QInputDialog.getText(
                self.main_ui,
                "Warning",
                f"This structure is of a different type: {structure_type}.\n"
                "Please change the structure name to create this object.",
                text=self.data_handler.generate_output_name(),
            )
            if ok:
                # After the user closes the QInputDialog,
                # you can get the text from the QLineEdit
                self.main_ui.structure_dd.setCurrentText(text)
            return False

    def find_scale_bar_width(self, seed_points, relative=True, threshold=None, direction=None):
        # get width of scaling bar by floodFilling an area of similar pixels.
        # The start point needs to be given

        if self.start_state:
            return
        if threshold is None:
            threshold = self.main_ui.DEFAULT_THRESHOLD
        if direction is None:
            direction = 'horizontal'
        
        self.scale_bar_params = (seed_points, relative, threshold, direction)
        self.main_ui.set_threshold(threshold)
        self.main_ui.scaling_direction_dd.setCurrentText(direction)

        if seed_points is None:
            self.draw_image()
            scale_px = ""
        else:
            # create copy of image which can be modified
            img_data_modified = self.data_handler.img_data.copy()
            if relative:
                seed_point_x = round(seed_points[0] * img_data_modified.shape[1])
                seed_point_y = round(seed_points[1] * img_data_modified.shape[0])
            else:
                seed_point_x, seed_point_y = seed_points
            self.data_handler.logger.debug(
                f"seed_point_x = {seed_point_x}, seed_point_y = {seed_point_y}"
            )

            cv2.floodFill(
                img_data_modified,
                None,
                (seed_point_x, seed_point_y),
                newVal=self.main_window.settings.value(
                    "graphics/scale_bar_color"
                ).getRgb(),
                loDiff=[threshold] * 3,
                upDiff=[threshold] * 3,
            )

            self.draw_image(img_data=img_data_modified)

            non_zero_indices = np.nonzero(
                np.sum(self.data_handler.img_data - img_data_modified, axis=2)
            )

            # plus one to account for the start pixel
            if direction == "horizontal":
                scale_px = np.max(non_zero_indices[1]) - np.min(non_zero_indices[1]) + 1
            else:
                scale_px = np.max(non_zero_indices[0]) - np.min(non_zero_indices[0]) + 1

        self.main_ui.pixel_edit.setText(str(scale_px))
        self.scene.update()

    def find_scale_bar_width_w_undo(self, seed_point_percentage, relative=True, threshold=None, direction=None):
        command = FindScalingBarWidthCommand(
            self, seed_point_percentage, relative, threshold, direction
        )
        self.main_window.undo_stack.push(command)

    def on_key_press(self, event):

        if self.start_state:
            return

        if isinstance(self.selected_object, LineControlPoints):
            if event.key.name == "Escape":
                if self.selected_object.continue_adding_points:
                    # self.selected_object.remove_point()
                    self.remove_point_w_undo()
                    self.selected_object.continue_adding_points = False
                else:
                    self.remove_point_w_undo()
            if event.key.name == "A":
                if (self.selected_object.num_points == 0 
                or len(self.selected_object.coords) < self.selected_object.num_points):

                    self.selected_object.continue_adding_points = True
                    
                    # get mouse position in image coordinates
                    index = self.selected_object.get_selected_index()
                    pos = self.selected_object.coords[index]
                    # undo gets called, when the released event is called
                    self.add_point_w_undo(self.selected_object, pos)


    def on_mouse_move(self, event):
        
        # transform so that coordinates start at 0 in self.view window
        tr = self.scene.node_transform(self.view)
        # only activate when over self.view by looking
        # if coordinates < 0 or > size of self.view
        if not (
            (tr.map(event.pos)[:2] > self.view.size).any()
            or (tr.map(event.pos)[:2] < (0, 0)).any()
        ):

            if self.start_state:
                return
            match event.button:
                case 1:
                    # Check if the left mouse button is being dragged
                    if not event.is_dragging:
                        return

                    # scale objects while dragging
                    if self.selected_object is not None:
                        modifiers = [key.name for key in event.modifiers]
                        tr = self.scene.node_transform(self.selected_object)
                        pos = tr.map(event.pos)

                        if self.main_ui.tools_buttons.checkedButton().text() in (
                            "Line", "Ellipse", "Rectangle", "Angle", "Edit", "Polygon", "Multi-Line"
                        ):

                            if "Shift" in modifiers and not isinstance(
                                self.selected_object,
                                (LineControlPoints, EditLineVisual),
                            ):

                                # calculate angle of current position
                                x, y = pos[0:2] - self.selected_object.center
                                angle = np.arctan2(-y, x)

                                # Check if "Control" is pressed for snapping
                                if "Control" in modifiers:
                                    # Calculate the nearest multiple of 45° (np.pi / 4 radians)
                                    nearest_multiple = round(angle / (np.pi / 4)) * (np.pi / 4)
                                    # Snap to the nearest multiple if the angle is close to it
                                    if abs(angle - nearest_multiple) < np.deg2rad(10):
                                        angle = nearest_multiple + self.selected_object.drag_reference_angle

                                self.selected_object.rotate(angle)

                            else:
                                self.selected_object.move(pos[0:2], modifiers=modifiers)

                            # update ui to display properties of selected object
                            self.selection_update()
                            self.main_window.right_ui.update_intensity_plot()

                case 3:
                    if event.is_dragging:
                        tr = self.view.node_transform(self.view.scene)
                        # Calculate the change in position of the mouse
                        dpos = tr.map(event.last_event.pos)[:2] - tr.map(event.pos)[:2]
                        # Pan the camera based on the mouse movement
                        self.view.camera.pan(dpos)
                
                case _:
                    # if it is a line that is still being drawn
                    if isinstance(self.selected_object, LineControlPoints):
                        if self.selected_object.continue_adding_points:
                            modifiers = [key.name for key in event.modifiers]
                            tr = self.scene.node_transform(self.selected_object)
                            pos = tr.map(event.pos)

                            self.selected_object.move(pos[:2], modifiers=modifiers)
                            self.selection_update()
                            self.main_window.right_ui.update_intensity_plot()
                        
    def hide_arrows(self):
        for name in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[name]:
                if isinstance(obj, EditRectVisual):
                    obj.hide_arrow()
        self.scene.update()
        
    def show_arrows(self):
        for name in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[name]:
                if isinstance(obj, EditRectVisual):
                    obj.show_arrow()
        self.scene.update()

    def move_object_w_undo(self, object):
        command = MoveObjectCommand(self, object)
        self.main_window.undo_stack.push(command)

    def remove_point_w_undo(self):
        # we dont want to undo the last 2 points
        if len(self.selected_object.coords) < 3:
            self.selected_object.remove_point()
        else:
            command = RemovePointCommand(self, self.selected_object)
            self.main_window.undo_stack.push(command)

    def add_point_w_undo(self, object, point):
        # we dont want to remember creating the first 2 (3 for angle) points 
        # as this is basically the creation of the object
        if (len(self.selected_object.coords) < 2 
        or (self.selected_object.num_points != 0 
            and len(self.selected_object.coords) < self.selected_object.num_points+1)):
            self.selected_object.add_point(point)
        else:
            command = AddPointCommand(self, object, point)
            self.main_window.undo_stack.push(command)

    def selection_update(self, object=None):

        if object is None:
            object = self.get_selected_object()
        if self.selected_object is None:
            self.main_ui.clear_object_table()
            return

        self.main_window.right_ui.update_intensity_plot()

        found_object = self.data_handler.find_object(object)
        if found_object:
            structure, index = found_object
        else:
            return
        self.main_ui.add_to_structure_dd(structure)
        self.main_ui.update_object_list()
        self.main_ui.object_list.item(index).setSelected(True)

        self.main_ui.update_object_table(object)

    def update_object_property_w_undo(self, obj, prop, value, scaling_factor=None, old_value=None):
        # only push onto undo stack if property is modifiable
        if prop in obj.get_modifiable_properties():
            command = UpdateObjectCommand(self, obj, prop, value, scaling_factor, old_value)
            self.main_window.undo_stack.push(command)
        # otherwise just redraw old value
        else:
            self.selection_update()

    def update_object_property(self, obj, prop, value, scaling_factor=None):
        if obj is None:
            obj = self.get_selected_object()
        # update object property
        changed = obj.update_property(prop, value, scaling_factor)
        # update ui to display properties of selected object
        self.selection_update()

        return changed


    def get_selected_object(self):
        """always returns the whole object instance,
        even if controlpoints are selected
        """
        return self.get_full_object(self.selected_object)
    
    def get_full_object(self, obj):
        if isinstance(obj, (ControlPoints, LineControlPoints)):
            return obj.parent
        return obj

    def delete_object(self, object=None):
        # delete selected object if no other is given
        if object is None:
            object = self.selected_object
        # delete object
        if object is not None:
            self.data_handler.delete_object(object)

            if object.selected:
                self.unselect()

            self.main_ui.update_object_list()
            object.delete()

        self.main_window.right_ui.update_intensity_plot()

    def delete_object_w_undo(self, object=None):
        if object is not None or self.selected_object is not None:
            command = DeleteObjectCommand(self.data_handler, object)
            self.main_window.undo_stack.push(command)

    def set_origin(self, point:np.ndarray, move_objects=True):
        """Set the origin of the image to a given point"""
        self.data_handler.logger.debug(f"set origin to {point}")

        if move_objects:
            self.move_all_objects(-(point-self.origin))
        self.origin = point 
        self.image.transform = linear.STTransform(translate=-self.origin)
        self.center_image()

    def move_all_objects(self, vector:np.ndarray):
        """Move all objects by a relative vector"""
        self.data_handler.logger.debug("move all objects")
        for structure in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[structure]:
                # show object
                obj.set_center(obj.center + vector)
                obj.update_from_controlpoints()
        self.scene.update()        

    def set_origin_w_undo(self, pos):
        command = SetOriginCommand(self, pos)
        self.main_window.undo_stack.push(command)

    def select(self, obj):
        self.unselect()
        self.selected_object = obj
        self.selected_object.select(True, obj=obj)
        self.selected_object.set_visibility(True)
        self.selection_update()

    def unselect(self):
        if self.selected_object is not None:
            self.selected_object.select(False)
            self.selected_object = None
            self.main_ui.clear_object_table()

    def show_all_objects(self):
        self.data_handler.logger.info("show all objects")
        for structure in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[structure]:
                # show object
                obj.set_visibility(True)
        self.scene.update()

    def show_all_objects_w_undo(self):
        command = ShowObjectCommand(self)
        self.main_window.undo_stack.push(command)

    def hide_all_objects(self):
        self.data_handler.logger.info("hide all objects")
        for structure in self.data_handler.drawing_data.keys():
            for obj in self.data_handler.drawing_data[structure]:
                # hide object
                obj.set_visibility(False)
        self.scene.update()

    def hide_all_objects_w_undo(self):
        command = HideObjectCommand(self)
        self.main_window.undo_stack.push(command)


class DeleteObjectCommand(QUndoCommand):
    def __init__(self, data_handler, object=None):
        super().__init__()
        self.data_handler = data_handler
        self.main_window = self.data_handler.main_window
        self.vispy_canvas = self.main_window.vispy_canvas
        if object is None:
            object = self.vispy_canvas.selected_object

        object = self.vispy_canvas.get_full_object(object)

        self.object = object
        self.structure, self.index = data_handler.find_object(self.object)

    def undo(self):
        # Restore the old state
        self.data_handler.logger.info("Undoing delete object")
        if self.structure in self.data_handler.drawing_data.keys():
            self.data_handler.drawing_data[self.structure].insert(
                self.index, self.object
            )
        else:
            self.data_handler.drawing_data[self.structure] = [self.object]
        self.main_window.main_ui.update_structure_dd()
        self.object.parent = self.vispy_canvas.view.scene

        self.data_handler.logger.info("Restored object")

    def redo(self):
        # Delete object
        self.vispy_canvas.delete_object(self.object)
        self.data_handler.logger.info("Deleted object")


class MoveObjectCommand(QUndoCommand):
    def __init__(self, vispy_instance, object):
        super().__init__()
        # make a copy of the object to be able to restore the old state
        self.vispy_instance = vispy_instance

        # if object is a control point, get the whole object
        self.object = vispy_instance.get_full_object(object)

        # for redoing
        self.redoing = False
        if isinstance(self.object, (EditLineVisual, EditPolygonVisual)):
            self.coords = None
            self.old_coords = object.coords.copy()
        elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):
            
            self.center = None
            self.height = None
            self.width = None
            self.angle = None
            self.old_height = self.object.height
            self.old_width = self.object.width
            self.old_center = self.object.center
            self.old_angle = self.object.angle
        # for undoing

    def undo(self):
        self.vispy_instance.data_handler.logger.info("Undoing move object")

        # save state before undoing move
        if isinstance(self.object, (EditLineVisual, EditPolygonVisual)):
            self.object.coords = self.old_coords
        elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):

            self.object.set_center(self.old_center)
            self.object.width = self.old_width
            self.object.height = self.old_height
            self.object.angle = self.old_angle

        # restore old state

        self.object.update_from_controlpoints()
        self.vispy_instance.selection_update()

    def redo(self):
        # Move the object
        self.vispy_instance.data_handler.logger.info("Redoing move object")

        # in the first creation we don't need to set it as it is already set
        # but we need to save the state
        if not self.redoing:
            if isinstance(self.object, (EditLineVisual, EditPolygonVisual)):
                self.coords = self.object.coords.copy()
            elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):
                self.center = self.object.center.copy()
                self.height = self.object.height
                self.width = self.object.width
                self.angle = self.object.angle
            self.redoing = True
        # move object on all redo operations except the first one
        else:
            if isinstance(self.object, (EditLineVisual, EditPolygonVisual)):
                self.object.coords = self.coords
            elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):
                self.object.set_center(self.center)
                self.object.width = self.width
                self.object.height = self.height
                self.object.angle = self.angle

        self.object.update_from_controlpoints()
        self.vispy_instance.selection_update()
        
    def check_movement(self):
        if isinstance(self.object, (EditLineVisual, EditPolygonVisual)):
            if len(self.old_coords) == len(self.object.coords):
                return (self.old_coords != self.object.coords).any()
            return True
        elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):
            return (
                self.old_width != self.object.width
                or self.old_height != self.object.height
                or (self.old_center != self.object.center).any()
                or self.old_angle != self.object.angle
            )


class HideObjectCommand(QUndoCommand):
    def __init__(self, vispy_canvas):
        super().__init__()
        self.vispy_canvas = vispy_canvas

    def undo(self):
        # Show the object
        self.vispy_canvas.show_all_objects()

    def redo(self):
        # Hide the object
        self.vispy_canvas.hide_all_objects()


class ShowObjectCommand(QUndoCommand):
    def __init__(self, vispy_canvas):
        super().__init__()
        self.vispy_canvas = vispy_canvas

    def undo(self):
        # Show the object
        self.vispy_canvas.hide_all_objects()

    def redo(self):
        # Hide the object
        self.vispy_canvas.show_all_objects()


class FindScalingBarWidthCommand(QUndoCommand):
    def __init__(self, vispy_canvas, seed_points, relative, threshold, direction):
        super().__init__()
        self.vispy_canvas:VispyCanvas = vispy_canvas

        self.seed_points = seed_points
        self.relative = relative
        self.threshold = threshold
        self.direction = direction

        self.old_scale_bar_params = self.vispy_canvas.scale_bar_params

    def undo(self):
        # Restore the old state
        self.vispy_canvas.find_scale_bar_width(*self.old_scale_bar_params)

    def redo(self):
        # Find the scaling bar width
        self.vispy_canvas.find_scale_bar_width(
            self.seed_points, self.relative, self.threshold, self.direction
        )


class CreateObjectCommand(QUndoCommand):
    def __init__(self, vispy_canvas, new_object, pos, selected, structure_name):
        super().__init__()
        self.vispy_canvas = vispy_canvas
        self.new_object = self.vispy_canvas.get_full_object(new_object)
        self.pos = pos
        self.selected = selected
        self.structure_name = structure_name
        self.parent = new_object.parent

    def undo(self):
        # Delete object
        self.vispy_canvas.data_handler.logger.info("Undoing create object")
        self.vispy_canvas.delete_object(self.new_object)

    def redo(self):

        # when it is an undo->redo operation some parameters are set
        if self.new_object and self.new_object.parent is None:
            self.selected = False
            self.new_object.parent = self.parent
            self.pos = None

        # Create object
        self.structure_name = self.vispy_canvas.create_new_object(
            self.new_object, self.pos, self.selected, self.structure_name
        )


class UpdateObjectCommand(QUndoCommand):
    def __init__(self, vispy_canvas, obj, prop, value, scaling_factor, old_value):
        super().__init__()

        self.vispy_canvas = vispy_canvas
        self.obj = obj
        self.prop = prop
        self.value = value
        self.scaling_factor = scaling_factor
        self.old_value = old_value

        if scaling_factor is None:
            self.scaling_factor = 1
    
    def undo(self):
        
        # logging
        if self.scaling_factor is None:
            scaling = 1
        else:
            scaling = self.scaling_factor
        self.vispy_canvas.data_handler.logger.debug(
            f"Undoing Change {self.prop} from {self.old_value*scaling} to {self.value}"
        )

        # update object property
        self.vispy_canvas.update_object_property(
            self.obj, self.prop, self.old_value, self.scaling_factor
        )


    def redo(self):
        # logging
        if self.scaling_factor is None:
            scaling = 1
        else:
            scaling = self.scaling_factor
        self.vispy_canvas.data_handler.logger.debug(
            f"Change {self.prop} from {self.old_value*scaling} to {self.value}"
        )

        # update object property
        self.vispy_canvas.update_object_property(
            self.obj, self.prop, self.value, self.scaling_factor
        )
        
class RemovePointCommand(QUndoCommand):

    def __init__(self, vispy_canvas, object):
        super().__init__()
        self.object = object
        self.delete_index = object.control_points.index(object.selected_cp)
        self.old_point = None
        self.vispy_canvas = vispy_canvas
        self.continue_adding_points = object.continue_adding_points

    def undo(self):
        # Show the object
        self.vispy_canvas.data_handler.logger.debug(
            f"Undoing remove point at index {self.delete_index}"
        )
        self.object.continue_adding_points = True
        self.object.add_point(self.old_point, index=self.delete_index)
        self.object.continue_adding_points = self.continue_adding_points

    def redo(self):
        # Hide the object
        self.vispy_canvas.data_handler.logger.debug(
            f"Redoing remove point at index {self.delete_index}"
        )
        self.old_point = self.object.coords[self.delete_index]
        self.object.remove_point(self.delete_index)

class AddPointCommand(QUndoCommand):

    def __init__(self, vispy_canvas, object, point):
        super().__init__()
        self.object = object
        self.add_index = object.get_selected_index() + 1
        self.point = point
        self.vispy_canvas = vispy_canvas
        self.redoing = False

    def undo(self):
        # remove movable point on undo
        self.object.continue_adding_points = False
        self.vispy_canvas.data_handler.logger.debug(
            f"Undoing adding point at index {self.add_index}"
        )
        if self.add_index < len(self.object.coords):
            self.point = self.object.coords[self.add_index]
            self.object.remove_point(self.add_index)

    def redo(self):
        self.vispy_canvas.data_handler.logger.debug(
            f"Redoing adding point at index {self.add_index}"
        )
        
        show=False
        if self.object is self.vispy_canvas.selected_object:
            self.object.select(True)
            show = True

        # when redoing, we need to add the point at the index 
        # before the one we added because that one is the currently moving one 
        if self.redoing:
            self.object.add_point(self.point, index=self.add_index, select=False, show=show)
        else:
            self.object.add_point(self.point, index=self.add_index)
        self.redoing = True

class SetOriginCommand(QUndoCommand):
    def __init__(self, vispy_canvas, pos):
        super().__init__()
        self.vispy_canvas = vispy_canvas
        self.old_origin = self.vispy_canvas.origin
        self.new_origin = pos

    def undo(self):
        # Show the object
        self.vispy_canvas.set_origin(self.old_origin)

    def redo(self):
        # Hide the object
        self.vispy_canvas.set_origin(self.new_origin)
        
class RotateImageCommand(QUndoCommand):
    def __init__(self, vispy_canvas):
        super().__init__()
        self.vispy_canvas = vispy_canvas
        
    def undo(self):
        """Rotate Image counter clockwise by 90 degrees"""
        self.vispy_canvas.rotate_image(direction="counter-clockwise")
        
    def redo(self):
        """Rotate Image clockwise by 90 degrees"""
        self.vispy_canvas.rotate_image(direction="clockwise")