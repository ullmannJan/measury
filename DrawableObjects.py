import numpy as np

from vispy import app, scene
from vispy.color import Color
from vispy.visuals.transforms import MatrixTransform   


class ControlPoints(scene.visuals.Compound):
    def __init__(self, parent):
        scene.visuals.Compound.__init__(self, [])
        self.unfreeze()
        self.parent = parent
        self._center = [0, 0]
        self._width = 0.0
        self._height = 0.0
        self._angle = 0.0 # in radians
        self.selected_cp = None
        self.opposed_cp = None

        self.edge_color = "black"
        self.face_color = (1,1,1,0.5)
        self.marker_size = 8

        self.control_points = [scene.visuals.Markers(parent=self)
                               for i in range(0, 4)]
        for c in self.control_points:
            c.set_data(pos=np.array([[0, 0]], dtype=np.float32),
                       edge_color=self.edge_color,
                       face_color=self.face_color,
                       size=self.marker_size)
            c.interactive = True
        
        self.freeze()

    def update_bounds(self):
        self._center = [0.5 * (self.parent.bounds(0)[1] +
                               self.parent.bounds(0)[0]),
                        0.5 * (self.parent.bounds(1)[1] +
                               self.parent.bounds(1)[0])]
        self._width = abs(self.parent.bounds(0)[1] - self.parent.bounds(0)[0])
        self._height = abs(self.parent.bounds(1)[1] - self.parent.bounds(1)[0])
        self.update_points()

    def update_points(self):

        
        self.control_points[0].set_data(
            pos=np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)
        self.control_points[1].set_data(
            pos=np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)
        self.control_points[2].set_data(
            pos=np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)
        self.control_points[3].set_data(
            pos=np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)

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
                    self.opposed_cp = \
                        self.control_points[int((i + n_cp / 2)) % n_cp]

    def start_move(self, start):
        None

    def move(self, end, modifiers=[], *args, **kwargs):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:

            diag = end-self._center

            self._width = abs(2 * (np.cos(self._angle)*diag[0] - np.sin(self._angle)*diag[1]))
            if "Control" in modifiers:
                self._height = self._width
            else:
                self._height = abs( 2 * (np.sin(self._angle)*diag[0] + np.cos(self._angle)*diag[1]))

            self.update_points()
            self.parent.update_from_controlpoints()

    def rotate(self, angle):
        if not self.parent.editable:
            return
        self._angle = angle
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


class EditVisual(scene.visuals.Compound):
        
    def __init__(self, 
                 control_points=None,
                 editable=True, 
                 selectable=True, 
                 on_select_callback=None,
                 callback_argument=None, 
                 *args, **kwargs):
        
        scene.visuals.Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.editable = editable
        self.form = None
        self._selectable = selectable
        self._on_select_callback = on_select_callback
        self._callback_argument = callback_argument

        if control_points == "LineControlPoints":
            self.control_points = LineControlPoints(parent=self)
        else:
            self.control_points = ControlPoints(parent=self)
        
        self.drag_reference = [0, 0]
        self.freeze()

    def add_subvisual(self, visual):
        scene.visuals.Compound.add_subvisual(self, visual)

    def select(self, val, obj=None):
        if self.selectable:
            self.control_points.visible(val)
            if self._on_select_callback is not None:
                self._on_select_callback(self._callback_argument)

    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

    def move(self, end, *args, **kwargs):
        if self.editable:
            shift = end[0:2] - self.drag_reference
            self.set_center(shift)
        
            self.update_transform()

    def rotate(self, angle):
        if self.editable:
            self.control_points.rotate(angle)
            self.update_transform()

    def update_transform(self):
        tr = MatrixTransform()
        tr.translate(-self.center)
        tr.rotate(np.rad2deg(self.control_points._angle), (0,0,-1))
        tr.translate(self.center)
        self.form.transform = tr

    def update_from_controlpoints(self):
        None

    @property
    def selectable(self):
        return self._selectable

    @selectable.setter
    def selectable(self, val):
        self._selectable = val

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
        self.control_points.select(True, self.control_points.control_points[2])

class EditRectVisual(EditVisual):
    def __init__(self, center=[0, 0], width=100, height=50, *args, **kwargs):
        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()
        self.form = scene.visuals.Rectangle(center=center, 
                                            width=width,
                                            height=height,
                                            color=(1,1,1,0.3),
                                            border_color="white",
                                            border_width=2,
                                            radius=0, 
                                            parent=self)
        self.form.interactive = True

        self.freeze()
        self.add_subvisual(self.form)
        self.control_points.update_bounds()

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


class EditEllipseVisual(EditVisual):
    def __init__(self, center=[0, 0], radius=[100, 100], *args, **kwargs):
        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()
        self.form = scene.visuals.Ellipse(center=center, radius=radius,
                                             color=(1,1,1,0.3),
                                             border_color="white",
                                             border_width=2,
                                             parent=self)
        self.form.interactive = True

        self.freeze()
        self.add_subvisual(self.form)
        self.control_points.update_bounds()

    def set_center(self, val):
        self.control_points.set_center(val)
        self.form.center = val

    def update_from_controlpoints(self):
        try:
            self.form.radius = [0.5 * abs(self.control_points._width),
                                   0.5 * abs(self.control_points._height)]
        except ValueError:
            None

class LineControlPoints(scene.visuals.Compound):

    def __init__(self, parent, *args, **kwargs):
        scene.visuals.Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.parent = parent
        self._length = 0.0
        self.start = [0, 0]
        self.end = [0, 0]
        self.selected_cp = None

        self.edge_color = "black"
        self.face_color = (1,1,1,0.2)
        self.marker_size = 8

        self.control_points = [scene.visuals.Markers(parent=self)
                               for i in range(0, 2)]
        for cpoint, coord in zip(self.control_points, [self.start, self.end]):
            cpoint.set_data(pos=np.array([coord], dtype=np.float32),
                       edge_color=self.edge_color,
                       face_color=self.face_color,
                       size=self.marker_size)
            cpoint.interactive = True
        
        self.freeze()
    
    @property
    def length(self):
        self._length = abs(np.linalg.norm(self.start-self.end))

    def update_points(self):

        self.control_points[0].set_data(
            pos=np.array([self.start]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)
        self.control_points[1].set_data(
            pos=np.array([self.end]),
            edge_color=self.edge_color,
            face_color=self.face_color,
            size=self.marker_size)

    def select(self, val, obj=None):
        self.visible(val)
        self.selected_cp = None

        if obj is not None:
            for c in self.control_points:
                if c == obj:
                    self.selected_cp = c

    def start_move(self, start):
        None

    def move(self, end, *args, **kwargs):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:
            if self.selected_cp == self.control_points[0]:
                self.start = end
            elif self.selected_cp == self.control_points[1]:
                self.end = end
                
            self.update_points()
            self.parent.update_from_controlpoints()

    def visible(self, v):
        for c in self.control_points:
            c.visible = v

    def set_start(self, start):
        self.start = start
        self.update_points()

    def set_end(self, end):
        self.end = end
        self.update_points()

    def get_center(self):
        return np.array(self.start) + 0.5*(np.array(self.end) - np.array(self.start))

    def set_center(self, val):
        shift = val-self.get_center()
        self.start += shift
        self.end += shift
        self.update_points()
        

class EditLineVisual(EditVisual):
        
    def __init__(self, line_start=[0,0], line_end=[0,0], *args, **kwargs):

        EditVisual.__init__(self, control_points="LineControlPoints", *args, **kwargs)
        self.unfreeze()

        self.line_start = line_start
        self.line_end = line_end

        self.line_color = (1,1,1,0.6)
        self.line_width = 5

        self.form = scene.visuals.Line(pos=np.array([self.line_start, self.line_end]),
                                        width=self.line_width, 
                                        color=self.line_color,
                                        method='gl',
                                        antialias=True,
                                        parent=self)
        self.form.interactive = True
        
        self.freeze()
        self.add_subvisual(self.form)

    @property
    def length(self):
        return self.control_points.length()

    def set_start(self, start):
        self.line_start = start
        self.control_points.set_start(start)
    
    def set_end(self, end):
        self.line_end = end
        self.control_points.set_end(end)

    def set_coords(self, start, end):
        self.line_start = start
        self.line_end = end
        self.control_points.set_start(start)
        self.control_points.set_end(end)

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
            self.form.set_data(pos=np.array([self.control_points.start, self.control_points.end]),
                                width=self.line_width, 
                                color=self.line_color)
        except ValueError:
            None

    @property
    def selectable(self):
        return self._selectable

    @selectable.setter
    def selectable(self, val):
        self._selectable = val

    def select_creation_controlpoint(self):
        self.control_points.select(True, self.control_points.control_points[0])

    def set_center(self, val):
        self.control_points.set_center(val[0:2])