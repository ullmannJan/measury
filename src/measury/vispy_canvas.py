# absolute imports
import numpy as np
import cv2
from vispy.scene import SceneCanvas, visuals, AxisWidget, Label
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtGui import QUndoCommand

# relative imports
from .drawable_objects import (
    EditEllipseVisual,
    EditRectVisual,
    ControlPoints,
    EditLineVisual,
    LineControlPoints,
)


class VispyCanvas(SceneCanvas):
    """Canvas for displaying the vispy instance"""

    CANVAS_SHAPE = (800, 600)
    main_ui = None
    main_window = None
    scale_bar_params = (None, True, 10)
    text_color = "black"

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

    def update_image(self):
        """Update the image in the vispy canvas"""

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

                self.title_label.text = self.data_handler.file_path.name

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
        self.data_handler.logger.debug("set vispy image data")
        self.image.set_data(img_data)
        self.image.interpolation = self.main_window.settings.value(
            "graphics/image_rendering"
        )

    def center_image(self):
        try:
            if self.data_handler.img_data is not None:
                self.view.camera.set_range(
                    x=(0, self.data_handler.img_data.shape[1]),
                    y=(0, self.data_handler.img_data.shape[0]),
                    margin=0,
                )
        except Exception as error:
            self.main_window.raise_error(f"Image could not be centered: {error}")

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
                match self.main_ui.tools.checkedButton().text():

                    case "move":
                        # enable panning
                        self.view.camera._viewbox.events.mouse_move.connect(
                            self.view.camera.viewbox_mouse_event
                        )

                        # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))

                        # unselect object
                        self.unselect()

                    case "select":
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

                    case "line" | "circle" | "rectangle" | "angle" | "edit":
                        # disable panning
                        self.view.camera._viewbox.events.mouse_move.disconnect(
                            self.view.camera.viewbox_mouse_event
                        )

                        tr = self.scene.node_transform(self.view.scene)
                        pos = tr.map(event.pos)
                        self.view.interactive = False
                        selected = self.visual_at(event.pos)
                        self.view.interactive = True
                        # unselect object to create room of new one
                        self.unselect()

                        if event.button == 1:
                            # QApplication.setOverrideCursor(QCursor(Qt.CursorShape.SizeAllCursor))

                            # edit object
                            if selected is not None:
                                self.selected_object = selected.parent
                                # update transform to selected object
                                tr = self.scene.node_transform(self.selected_object)
                                pos = tr.map(event.pos)

                                self.selected_object.select(True, obj=selected)
                                self.selected_object.start_move(pos)
                                self.move_object_w_undo(self.selected_object)

                                # update ui to display properties of selected object
                                self.selection_update()

                            # create new object:
                            if self.selected_object is None:

                                match self.main_ui.tools.checkedButton().text():
                                    case "line":
                                        new_object = EditLineVisual(
                                            parent=self.view.scene,
                                            settings=self.main_window.settings,
                                        )
                                    case "circle":
                                        new_object = EditEllipseVisual(
                                            parent=self.view.scene,
                                            settings=self.main_window.settings,
                                        )
                                    case "rectangle":
                                        new_object = EditRectVisual(
                                            parent=self.view.scene,
                                            settings=self.main_window.settings,
                                        )
                                    case "angle":
                                        new_object = EditLineVisual(
                                            settings=self.main_window.settings,
                                            parent=self.view.scene,
                                            num_points=3,
                                        )
                                    case "edit":
                                        return
                                # dont show object before it is added to drawing_data
                                new_object.select(False)
                                if self.check_creation_allowed(new_object):

                                    self.create_new_object_w_undo(
                                        new_object, pos=pos, selected=True
                                    )

                                    # update ui where data is shown
                                    self.selection_update(object=new_object)
                                else:
                                    new_object.delete()

                        # delete object
                        if event.button == 2:  # right button deletes object
                            # not self.selected_object because we want to
                            # delete it on hover too
                            if selected is not None:
                                self.delete_object_w_undo(object=selected.parent)

                                # Needs change
                                # self.main_ui.update_save_window()

                    case "identify scaling":
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
                                (m_i_x, m_i_y), relative=False
                            )

                        # right click to delete scaling identification
                        if event.button == 2:
                            self.draw_image(self.data_handler.img_data)
                            self.main_ui.pixel_edit.setText(None)

        # if click is above box
        elif (
            tr.map(event.pos)[1] < 0
            and tr.map(event.pos)[0] > 0
            and tr.map(event.pos)[0] < self.view.size[0]
        ):
            if not self.data_handler.file_path:
                self.main_ui.select_file()
            elif self.data_handler.file_path.name != "clipboard":
                self.data_handler.open_file_location(self.data_handler.file_path)

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

    def find_scale_bar_width(self, seed_points, relative=True, threshold=10):
        # get width of scaling bar by floodFilling an area of similar pixels.
        # The start point needs to be given

        if self.start_state:
            return

        self.scale_bar_params = (seed_points, relative, threshold)

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
            if self.main_ui.scaling_direction_dd.currentText() == "horizontal":
                scale_px = np.max(non_zero_indices[1]) - np.min(non_zero_indices[1]) + 1
            else:
                scale_px = np.max(non_zero_indices[0]) - np.min(non_zero_indices[0]) + 1

        self.main_ui.pixel_edit.setText(str(scale_px))
        self.scene.update()

    def find_scale_bar_width_w_undo(
        self, seed_point_percentage, relative=True, threshold=10
    ):
        command = FindScalingBarWidthCommand(
            self, seed_point_percentage, relative, threshold
        )
        self.main_window.undo_stack.push(command)

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

                        if self.main_ui.tools.checkedButton().text() in (
                            "line", "circle", "rectangle", "angle", "edit"
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

    def move_object_w_undo(self, object):
        command = MoveObjectCommand(self, object)
        self.main_window.undo_stack.push(command)

    def selection_update(self, object=None):

        if object is None:
            object = self.selected_object
        if self.selected_object is None:
            self.main_ui.clear_object_table()
            return

        # in case the selected objects is a control point
        # we want the parent object
        if isinstance(object, (ControlPoints, LineControlPoints)):
            object = self.selected_object.parent

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

    def update_object_property(self, obj, prop, value, scaling_factor=None):
        if obj is None:
            obj = self.get_selected_object()
        # update object property
        obj.update_property(prop, value, scaling_factor)
        # update ui to display properties of selected object

    def get_selected_object(self):
        """always returns the whole object instance,
        even if controlpoints are selected
        """
        if isinstance(self.selected_object, (ControlPoints, LineControlPoints)):
            return self.selected_object.parent
        return self.selected_object

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
        command = DeleteObjectCommand(self.data_handler, object)
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

        if isinstance(object, (ControlPoints, LineControlPoints)):
            object = object.parent

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
        if isinstance(object, (ControlPoints, LineControlPoints)):
            object = object.parent
        self.object = object

        # for redoing
        self.redoing = False
        if isinstance(self.object, EditLineVisual):
            self.coords = None
            self.old_coords = object.coords.copy()
        elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):

            self.height = None
            self.old_height = object.height
            self.width = None
            self.old_width = object.width
            self.center = None
            self.old_center = object.center
            self.angle = None
            self.old_angle = object.angle
        # for undoing

    def undo(self):
        self.vispy_instance.data_handler.logger.info("Undoing move object")

        # save former state
        if isinstance(self.object, EditLineVisual):
            self.coords = self.object.coords
            self.object.coords = self.old_coords
        elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):

            self.center = self.object.center
            self.height = self.object.height
            self.width = self.object.width
            self.angle = self.object.angle

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

        if not self.redoing:
            self.redoing = True
        else:
            if isinstance(self.object, EditLineVisual):
                self.object.coords = self.coords
            elif isinstance(self.object, (EditEllipseVisual, EditRectVisual)):
                self.object.set_center(self.center)
                self.object.width = self.width
                self.object.height = self.height
                self.object.angle = self.angle

            self.object.update_from_controlpoints()
            self.vispy_instance.selection_update()


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
    def __init__(self, vispy_canvas, seed_points, relative, threshold):
        super().__init__()
        self.vispy_canvas = vispy_canvas

        self.seed_points = seed_points
        self.relative = relative
        self.threshold = threshold

        self.old_scale_bar_params = self.vispy_canvas.scale_bar_params

    def undo(self):
        # Restore the old state
        self.vispy_canvas.find_scale_bar_width(*self.old_scale_bar_params)

    def redo(self):
        # Find the scaling bar width
        self.vispy_canvas.find_scale_bar_width(
            self.seed_points, self.relative, self.threshold
        )


class CreateObjectCommand(QUndoCommand):
    def __init__(self, vispy_canvas, new_object, pos, selected, structure_name):
        super().__init__()
        self.vispy_canvas = vispy_canvas
        if isinstance(new_object, (ControlPoints, LineControlPoints)):
            new_object = new_object.parent
        self.new_object = new_object
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
