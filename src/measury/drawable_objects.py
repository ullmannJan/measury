import numpy as np
from scipy.ndimage import map_coordinates

from vispy.scene.visuals import Compound, Markers, Rectangle, Ellipse, Line
from vispy.visuals.transforms import MatrixTransform, linear


# Compound from vispy.scene.visuals
class ControlPoints(Compound):
    def __init__(self, parent):
        Compound.__init__(self, [])
        self.unfreeze()
        self.parent = parent
        self._center = np.array([0, 0], dtype=np.float64)
        self._width = 0.0
        self._height = 0.0
        self._angle = 0.0  # in radians
        self.selected_cp = None
        self.opposed_cp = None

        self.edge_color = "black"
        self.face_color = (1, 1, 1, 0.5)
        self.marker_size = 8

        # Markers from vispy.scene.visuals
        self.control_points = [Markers(parent=self) for i in range(0, 4)]
        self.coords = np.zeros((len(self.control_points), 1, 2),
                               dtype=np.float32)

        for i, c in enumerate(self.control_points):
            c.set_data(
                pos=self.coords[i],
                edge_color=self.edge_color,
                face_color=self.face_color,
                size=self.marker_size,
            )
            c.interactive = True

        self.transform = linear.STTransform(translate=(0, 0, -2))

        self.freeze()

    def update_bounds(self):
        self._center = np.array(
            [
                0.5 * (self.parent.bounds(0)[1] + self.parent.bounds(0)[0]),
                0.5 * (self.parent.bounds(1)[1] + self.parent.bounds(1)[0]),
            ],
            dtype=np.float64,
        )
        self._width = abs(self.parent.bounds(0)[1] - self.parent.bounds(0)[0])
        self._height = abs(self.parent.bounds(1)[1] - self.parent.bounds(1)[0])
        self.update_points()

    def update_points(self):
        # center-+
        self.coords[0] = np.array(
            [
                [
                    self._center[0]
                    - 0.5 * np.cos(self._angle) * self._width
                    + 0.5 * np.sin(self._angle) * self._height,
                    self._center[1]
                    + 0.5 * np.sin(self._angle) * self._width
                    + 0.5 * np.cos(self._angle) * self._height,
                ]
            ]
        )
        # center++
        self.coords[1] = np.array(
            [
                [
                    self._center[0]
                    + 0.5 * np.cos(self._angle) * self._width
                    + 0.5 * np.sin(self._angle) * self._height,
                    self._center[1]
                    - 0.5 * np.sin(self._angle) * self._width
                    + 0.5 * np.cos(self._angle) * self._height,
                ]
            ]
        )
        # center+-
        self.coords[2] = np.array(
            [
                [
                    self._center[0]
                    + 0.5 * np.cos(self._angle) * self._width
                    - 0.5 * np.sin(self._angle) * self._height,
                    self._center[1]
                    - 0.5 * np.sin(self._angle) * self._width
                    - 0.5 * np.cos(self._angle) * self._height,
                ]
            ]
        )
        # center--
        self.coords[3] = np.array(
            [
                [
                    self._center[0]
                    - 0.5 * np.cos(self._angle) * self._width
                    - 0.5 * np.sin(self._angle) * self._height,
                    self._center[1]
                    + 0.5 * np.sin(self._angle) * self._width
                    - 0.5 * np.cos(self._angle) * self._height,
                ]
            ]
        )
        for i, c in enumerate(self.control_points):
            c.set_data(
                pos=self.coords[i],
                edge_color=self.edge_color,
                face_color=self.face_color,
                size=self.marker_size,
            )

    def select(self, val, obj=None):
        self.visible(val)
        self.selected_cp = None
        self.opposed_cp = None

        if obj is not None:
            n_cp = len(self.control_points)
            for i in range(0, n_cp):
                c = self.control_points[i]
                if c == obj:
                    self.selected_cp = c
                    self.opposed_cp = self.control_points[int((i + n_cp / 2)) % n_cp]

    def start_move(self, start):
        self.parent.start_move(start)

    def move(self, end, modifiers=[], *args, **kwargs):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:

            # alt for scaling from center mode
            if "Alt" in modifiers:
                diag = end - self._center

                self._width = 2 * abs(
                    np.cos(self._angle) * diag[0] - np.sin(self._angle) * diag[1]
                )
                self._height = 2 * abs(
                    np.sin(self._angle) * diag[0] + np.cos(self._angle) * diag[1]
                )
                if "Control" in modifiers:
                    val = max(self._width, self._height)
                    self._width = val
                    self._height = val

                self.update_points()
                self.parent.update_from_controlpoints()

            # normal scaling mode where one corner is fixed
            else:
                opp_index = self.control_points.index(self.opposed_cp)

                opp = self.coords[opp_index, 0, :]
                diag = end - opp
                center = opp + 0.5 * diag

                self._width = (
                    np.cos(self._angle) * diag[0] - np.sin(self._angle) * diag[1]
                )
                self._height = (
                    np.sin(self._angle) * diag[0] + np.cos(self._angle) * diag[1]
                )

                # depending on selected point
                if opp_index == 2 or opp_index == 1:
                    self._width *= -1
                if opp_index == 0 or opp_index == 1:
                    self._height *= -1

                # square rectangle when holding Ctrl
                if "Control" in modifiers:
                    val = np.max(np.abs([self._width, self._height]))
                    self._width = np.sign(self._width) * val
                    self._height = np.sign(self._height) * val

                    # I have forgotten why this works
                    if opp_index == 2 or opp_index == 0:
                        offset = (
                            val
                            / np.sqrt(2)
                            * np.array(
                                [
                                    np.sign(self._width)
                                    * np.cos(
                                        np.pi / 4
                                        + np.sign(self._width)
                                        * np.sign(self._height)
                                        * self.angle
                                    ),
                                    np.sign(self._height)
                                    * np.sin(
                                        np.pi / 4
                                        + np.sign(self._width)
                                        * np.sign(self._height)
                                        * self.angle
                                    ),
                                ]
                            )
                        )
                    else:
                        offset = (
                            val
                            / np.sqrt(2)
                            * np.array(
                                [
                                    np.sign(self._width)
                                    * np.cos(
                                        np.pi / 4
                                        - np.sign(self._width)
                                        * np.sign(self._height)
                                        * self.angle
                                    ),
                                    np.sign(self._height)
                                    * np.sin(
                                        np.pi / 4
                                        - np.sign(self._width)
                                        * np.sign(self._height)
                                        * self.angle
                                    ),
                                ]
                            )
                        )

                    if opp_index == 2 or opp_index == 1:
                        offset[0] *= -1
                    if opp_index == 0 or opp_index == 1:
                        offset[1] *= -1
                    center = opp + offset

                self.set_center(center)
                self.parent.update_from_controlpoints()
                self.parent.update_transform()

    def rotate(self, angle):
        if self.parent.editable:
            # if self.control_points.index(self.selected_cp)%2 == 0:
            self._angle = angle - self.parent.drag_reference_angle
            self.update_points()
            self.parent.update_from_controlpoints()
            self.parent.update_transform()

    def visible(self, v):
        for c in self.control_points:
            c.visible = v

    def get_center(self):
        return self._center

    @property
    def center(self):
        return self._center

    def set_center(self, val):
        self._center = val
        self.update_points()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, val):
        self._angle = val
        self.update_points()

    def delete(self):
        self.parent.delete()
        del self


# from vispy.scene.visuals
class EditVisual(Compound):

    def __init__(
        self,
        settings,
        control_points=None,
        editable=True,
        selectable=True,
        on_select_callback=None,
        callback_argument=None,
        angle=0,
        *args,
        **kwargs,
    ):

        # from vispy.scene.visuals
        Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.editable = editable
        self._selectable = selectable
        self.form = None
        self._on_select_callback = on_select_callback
        self._callback_argument = callback_argument
        self.settings = settings

        match control_points:
            case ("LineControlPoints", int()):
                _, num_points = control_points
                self.control_points = LineControlPoints(
                    parent=self, num_points=num_points
                )
            case _:
                self.control_points = ControlPoints(parent=self)
                self.angle = angle

        self.drag_reference = np.array([0, 0], dtype=np.float64)
        self.drag_reference_angle = 0.0

        self.transform = linear.STTransform(translate=(0, 0, -1))
        self.freeze()

    def add_subvisual(self, visual):
        # from vispy.scene.visuals
        Compound.add_subvisual(self, visual)

    def select(self, val, obj=None):
        if self.selectable:
            self.control_points.visible(val)
            if self._on_select_callback is not None:
                self._on_select_callback(self._callback_argument)

    @property
    def selected(self):
        return self.control_points.control_points[0].visible

    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

        # calculate angle of drag reference point
        x, y = self.drag_reference
        # -y because y-axis is flipped
        angle_drag = np.arctan2(-y, x)
        self.drag_reference_angle = angle_drag - self.control_points.angle

    def move(self, end, *args, **kwargs):
        if self.editable:
            shift = end[0:2] - self.drag_reference
            self.set_center(shift)

            self.update_transform()

    def rotate(self, angle):
        """
        Rotate the object by angle (in radians) around its center from the drag reference point.
        """

        if self.editable:

            # shift is difference
            abs_angle = angle - self.drag_reference_angle
            # rotate control points and therefore shape as well
            self.angle = abs_angle % (2 * np.pi)
            self.update_transform()

    def update_transform(self):
        tr = MatrixTransform()
        tr.translate(-self.center)
        tr.rotate(np.rad2deg(self.angle), (0, 0, -1))
        tr.translate(self.center)
        self.form.transform = tr

    def update_from_controlpoints(self):
        pass

    @property
    def selectable(self):
        return self._selectable

    @selectable.setter
    def selectable(self, val):
        self._selectable = val

    def set_visibility(self, v):
        self.visible = v
        # only make controlpoint not visible but never visible
        # that part is already done by the clicking architecture
        if not v:
            self.control_points.visible(v)

    @property
    def angle(self):
        return self.control_points.angle

    @angle.setter
    def angle(self, val):
        self.control_points.angle = val
        # self.update_from_controlpoints()

    # height
    @property
    def height(self):
        return self.control_points._height

    @height.setter
    def height(self, val):
        self.control_points._height = val
        self.control_points.update_points()
        self.update_from_controlpoints()

    # width
    @property
    def width(self):
        return self.control_points._width

    @width.setter
    def width(self, val):
        self.control_points._width = val
        self.control_points.update_points()
        self.update_from_controlpoints()

    # center
    @property
    def center(self):
        return self.control_points.get_center()

    @center.setter
    # this method redirects to set_center. Override set_center in subclasses.
    def center(self, val):
        self.set_center(val)

    # override this method in subclass
    def set_center(self, val):
        self.control_points.set_center(val[0:2])

    def select_creation_controlpoint(self):
        self.control_points.select(True, self.control_points.control_points[1])

    def output_properties(self):
        None

    def delete(self):
        self.parent = None
        del self

    def update_colors(self, color, border_color):
        pass

    def update_property(self, prop, val, scaling_factor=None):
        pass

    def get_modifiable_properties(self):
        return None


class EditRectVisual(EditVisual):
    def __init__(
        self,
        center=np.array([0, 0], dtype=np.float64),
        width=1e-6,
        height=1e-6,
        *args,
        **kwargs,
    ):

        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()

        self.form = Rectangle(
            center=center,
            width=width,
            height=height,
            border_width=2,
            radius=0,
            parent=self,
        )
        self.form.interactive = True

        color = self.settings.value("graphics/object_color").getRgb()
        self.form.color = tuple([value / 255 for value in color])
        border_color = self.settings.value("graphics/object_border_color").getRgb()
        self.form.border_color = tuple([value / 255 for value in border_color])

        self.freeze()
        self.add_subvisual(self.form)
        self.control_points.update_bounds()
        self.rotate(self.angle)

    def set_center(self, val):
        self.control_points.set_center(val[0:2])
        self.form.center = val[0:2]

    def update_from_controlpoints(self):
        try:
            self.form.width = abs(self.control_points._width)
        except ValueError:
            None
        try:
            self.form.height = abs(self.control_points._height)
        except ValueError:
            None
        try:
            self.form.center = self.control_points.center
        except ValueError:
            None
        try:
            self.angle = self.control_points.angle
            self.update_transform()
        except ValueError:
            None

    def output_properties(self):

        return dict(
            center=(self.form.center, "px"),
            width=(self.form.width, "px"),
            height=(self.form.height, "px"),
            area=(self.form.height * self.form.width, "px²"),
            angle=(np.rad2deg(self.control_points._angle), "°"),
        )

    def update_property(self, prop, val, scaling_factor=None):
        if scaling_factor is None:
            scaling_factor = 1
        match prop:
            case "center":
                self.set_center(val / scaling_factor)
            case "width":
                self.width = val / scaling_factor
            case "height":
                self.height = val / scaling_factor
            case "angle":
                self.angle = np.deg2rad(val)
                self.update_transform()
    
    def get_modifiable_properties(self):
        return ["center", "width", "height", "angle"]

    def save(self):
        return dict(
            center=self.form.center,
            width=self.form.width,
            height=self.form.height,
            angle=self.angle,
        )

    def intensity_profile(self, image, n_x=100, n_y=20, **kwargs):
        # Get the coordinates of the rectangle
        coords = self.control_points.coords[:, 0, :]

        # Compute the vector along y-direction
        x_dir = np.linspace(0, coords[3][0] - coords[0][0], n_y, endpoint=True)
        y_dir = np.linspace(0, coords[3][1] - coords[0][1], n_y, endpoint=True)
        # Compute the start and end points for all lines
        starts = coords[0][::-1] + np.column_stack((y_dir, x_dir))
        ends = coords[1][::-1] + np.column_stack((y_dir, x_dir))

        if self.control_points._width < 0:
            starts, ends = ends, starts

        # Initialize an empty list to hold the intensity profiles
        intensity_profile = np.zeros(n_x)
        evaluation_coords = np.empty((n_y, n_x, 2))
        img = np.sum(image, axis=2)
        # Iterate over all lines
        for i, (start, end) in enumerate(zip(starts, ends)):
            # Compute the coordinates along the line
            x_coords = np.linspace(start[1], end[1], n_x)
            y_coords = np.linspace(start[0], end[0], n_x)

            evaluation_coords[i, :, :] = np.column_stack((x_coords, y_coords))
            # Stack the coordinates into a 2D array
            eval_coords = np.vstack([y_coords, x_coords])

            # Compute the intensity profile for the line
            intensity_profile += map_coordinates(
                img, eval_coords, mode="constant", **kwargs
            )

        return intensity_profile, evaluation_coords

    def update_colors(self, color, border_color):
        self.form.color = color
        self.form.border_color = border_color


class EditEllipseVisual(EditVisual):
    def __init__(
        self,
        center=np.array([0, 0], dtype=np.float64),
        radius=np.array([1e-6, 1e-6], dtype=np.float64),
        *args,
        **kwargs,
    ):

        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()

        self.form = Ellipse(center=center, radius=radius, border_width=2, parent=self)

        color = self.settings.value("graphics/object_color").getRgb()
        self.form.color = tuple([value / 255 for value in color])
        border_color = self.settings.value("graphics/object_border_color").getRgb()
        self.form.border_color = tuple([value / 255 for value in border_color])

        self.form.interactive = True

        self.freeze()
        self.add_subvisual(self.form)
        self.control_points.update_bounds()
        self.rotate(self.angle)

    def set_center(self, val):
        self.control_points.set_center(val)
        self.form.center = val

    def update_from_controlpoints(self):
        try:
            self.form.radius = np.array(
                [
                    0.5 * abs(self.control_points._width),
                    0.5 * abs(self.control_points._height),
                ],
                dtype=np.float64,
            )
        except ValueError:
            None
        try:
            self.form.center = self.control_points.center
        except ValueError:
            None
        try:
            self.angle = self.control_points.angle
            self.update_transform()
        except ValueError:
            None

    def output_properties(self):

        if self.form.radius[0] == self.form.radius[1]:
            radius = self.form.radius[0]
        else:
            radius = self.form.radius
        return dict(
            center=(self.form.center, "px"),
            radius=(radius, "px"),
            area=(np.prod(self.form.radius) * np.pi, "px²"),
            angle=(np.rad2deg(self.control_points._angle), "°"),
        )

    def update_property(self, prop, val, scaling_factor=None):
        if scaling_factor is None:
            scaling_factor = 1
        match prop:
            case "center":
                self.set_center(val / scaling_factor)
            case "radius":
                self.width = val[0] / scaling_factor
                self.height = val[1] / scaling_factor
            case "angle":
                self.angle = np.deg2rad(val)
                self.update_transform()
    
    def get_modifiable_properties(self):
        return ["center", "radius", "angle"]

    def save(self):
        return dict(
            center=self.form.center,
            radius=np.array(self.form.radius),
            angle=self.angle,
        )

    def update_colors(self, color, border_color):
        self.form.color = color
        self.form.border_color = border_color


class LineControlPoints(Compound):

    def __init__(self, parent, num_points=2, *args, **kwargs):
        Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.parent = parent
        self.num_points = num_points
        self._length = 0.0
        self.coords = np.zeros((self.num_points, 2), dtype=np.float64)
        if self.num_points > 2:
            self.coords[1:-2] = [0, 50]
            self.coords[-1] = [50, 0]
        self.selected_cp = None

        self.edge_color = "black"
        self.face_color = (1, 1, 1, 0.2)
        self.marker_size = 8

        self.control_points = [Markers(parent=self) for i in range(0, self.num_points)]
        for cpoint, coord in zip(self.control_points, self.coords):
            cpoint.set_data(
                pos=np.array([coord], dtype=np.float32),
                edge_color=self.edge_color,
                face_color=self.face_color,
                size=self.marker_size,
            )
            cpoint.interactive = True

        self.transform = linear.STTransform(translate=(0, 0, -2))

        self.freeze()

    @property
    def length(self):
        diff = np.diff(self.coords, axis=0)
        self._length = np.abs(np.linalg.norm(diff, axis=1))
        if len(self._length) == 1:
            self._length = self._length[0]
        return self._length
        # deprecated
        # self._length = abs(np.linalg.norm(self.start-self.end))

    def update_points(self):

        for cpoint, coord in zip(self.control_points, self.coords):
            cpoint.set_data(
                pos=np.array([coord]),
                edge_color=self.edge_color,
                face_color=self.face_color,
                size=self.marker_size,
            )

    def select(self, val, obj=None):
        self.visible(val)
        self.selected_cp = None

        if obj is not None:
            for c in self.control_points:
                if c == obj:
                    self.selected_cp = c

    def start_move(self, start):
        self.parent.start_move(start)

    def move(self, end, *args, **kwargs):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:
            index = self.control_points.index(self.selected_cp)
            self.coords[index] = end[0:2]
            # if self.selected_cp == self.control_points[0]:
            #     self.start = end
            # elif self.selected_cp == self.control_points[1]:
            #     self.end = end

            self.update_points()
            self.parent.update_from_controlpoints()

    def visible(self, v):
        for c in self.control_points:
            c.visible = v

    def set_coords(self, coords):
        self.coords = coords
        self.update_points()

    def get_center(self):
        return np.array(self.coords[0]) + 0.5 * (
            np.array(self.coords[-1]) - np.array(self.coords[0])
        )

    def set_center(self, val):
        shift = val - self.get_center()
        self.coords += shift
        # self.start += shift
        # self.end += shift
        self.update_points()

    def delete(self):
        self.parent.delete()
        del self


class EditLineVisual(EditVisual):

    def __init__(self, num_points=2, coords=None, *args, **kwargs):

        EditVisual.__init__(
            self, control_points=("LineControlPoints", num_points), *args, **kwargs
        )
        self.unfreeze()

        self.num_points = num_points
        border_color = self.settings.value("graphics/object_border_color").getRgb()
        self.line_color = tuple([value / 255 for value in border_color])
        self.line_width = 3

        if coords is not None:
            self.coords = coords

        self.form = Line(
            pos=self.coords,
            width=self.line_width,
            color=self.line_color,
            method="gl",
            antialias=True,
            parent=self,
        )

        self.form.interactive = True

        self.freeze()
        self.add_subvisual(self.form)

    @property
    def length(self):
        return self.control_points.length

    @property
    def angles(self):
        diff = np.diff(self.control_points.coords, axis=0)
        diff[0] *= -1
        angles = np.rad2deg(np.arctan2(-diff[:, 1], diff[:, 0]))
        return angles

    @property
    def angle(self):
        return self.angles[0]

    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

    @property
    def coords(self):
        return self.control_points.coords

    @coords.setter
    def coords(self, coords):
        self.control_points.set_coords(coords)

    def move(self, end, *args, **kwargs):
        if self.editable:
            new_center = end[0:2] - self.drag_reference
            self.set_center(new_center)
            self.update_from_controlpoints()

    def rotate(self, angle):
        None

    def update_transform(self):
        None

    def update_from_controlpoints(self):
        try:
            self.form.set_data(
                pos=self.coords, width=self.line_width, color=self.line_color
            )
        except ValueError:
            None

    @property
    def selectable(self):
        return self._selectable

    @selectable.setter
    def selectable(self, val):
        self._selectable = val

    def select_creation_controlpoint(self):
        self.control_points.select(True, self.control_points.control_points[1])

    def set_center(self, val):
        self.control_points.set_center(val[0:2])

    def output_properties(self):

        if self.control_points.num_points == 2:
            angle = self.angles
        else:
            angle = abs(np.diff(self.angles))

            if angle > 180:
                angle = 360 - angle

        return dict(length=[self.length, "px"], angle=[angle[0], "°"])

    def update_property(self, prop, val, scaling_factor=None):
        if scaling_factor is None:
            scaling_factor = 1
        match prop:
            case "length":
                if isinstance(val, np.ndarray):
                    norm_vecs = (
                        np.diff(self.control_points.coords, axis=0) / self.length
                    )
                    for i, vec in enumerate(norm_vecs):
                        self.control_points.coords[i + 1] = (
                            self.control_points.coords[i]
                            + val[i] / scaling_factor * vec
                        )

                else:
                    # get normalized vector
                    norm_vec = np.diff(self.control_points.coords, axis=0) / self.length
                    self.control_points.coords[1] = (
                        self.control_points.coords[0] + val / scaling_factor * norm_vec
                    )
                self.update_from_controlpoints()
                self.control_points.update_points()
    
    def get_modifiable_properties(self):
        return ["length"]

    def save(self):
        return dict(coords=self.coords, num_points=self.num_points)

    def intensity_profile(self, image, n=100, **kwargs):

        # Iterate over pairs of consecutive coordinates

        diff = np.diff(self.control_points.coords, axis=0)
        lengths = np.abs(np.linalg.norm(diff, axis=1))

        # Compute the total length of the path
        total_length = np.sum(lengths)

        # Compute the number of points for each line segment
        num_points = np.round(n * lengths / total_length).astype(int)

        length = np.sum(num_points)
        intensity_profiles = np.empty(length)
        evaluation_coords = np.empty((length, 2))

        # Convert the image to grayscale
        img = np.sum(image, axis=2)

        count = 0
        for index, m in enumerate(num_points):
            # Swap x and y in the start and end points
            start = self.coords[index][::-1]
            end = self.coords[index + 1][::-1]

            # Compute the coordinates along the line
            x_coords = np.linspace(start[1], end[1], m, endpoint=True)
            y_coords = np.linspace(start[0], end[0], m, endpoint=True)

            # Stack the coordinates into a 2D array
            eval_coords = np.vstack([y_coords, x_coords])
            evaluation_coords[count : count + m] = eval_coords.T[:, ::-1]

            # Get the intensity profile along the line segment
            intensity_profile = map_coordinates(
                img, eval_coords, mode="constant", **kwargs
            )

            # Append the intensity profile to full array
            intensity_profiles[count : count + m] = intensity_profile

            count += m

        return intensity_profiles, evaluation_coords
