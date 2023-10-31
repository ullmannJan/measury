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

        self.control_points = [scene.visuals.Markers(parent=self)
                               for i in range(0, 4)]
        for c in self.control_points:
            c.set_data(pos=np.array([[0, 0]], dtype=np.float32),
                       symbol="s",
                       edge_color="white",
                       size=6)
            c.interactive = True
        
        self.freeze()

    def update_bounds(self):
        self._center = [0.5 * (self.parent.bounds(0)[1] +
                               self.parent.bounds(0)[0]),
                        0.5 * (self.parent.bounds(1)[1] +
                               self.parent.bounds(1)[0])]
        self._width = self.parent.bounds(0)[1] - self.parent.bounds(0)[0]
        self._height = self.parent.bounds(1)[1] - self.parent.bounds(1)[0]
        self.update_points()

    def update_points(self):

        
        self.control_points[0].set_data(
            pos=np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]]))
        self.control_points[1].set_data(
            pos=np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]]))
        self.control_points[2].set_data(
            pos=np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]]))
        self.control_points[3].set_data(
            pos=np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                           self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]]))

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

    def move(self, end):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:
            self._width = 2 * (end[0] - self._center[0])
            self._height = 2 * (end[1] - self._center[1])
            self.update_points()
            self.parent.update_from_controlpoints()

    def rotate(self, angle):
        if not self.parent.editable:
            return
        self._angle = angle
        self.update_points()
        self.parent.update_from_controlpoints()

    def visible(self, v):
        for c in self.control_points:
            c.visible = v

    def get_center(self):
        return self._center

    def set_center(self, val):
        self._center = val
        self.update_points()


class EditVisual(scene.visuals.Compound):
    
    form = None
    
    def __init__(self, editable=True, selectable=True, on_select_callback=None,
                 callback_argument=None, *args, **kwargs):
        scene.visuals.Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.editable = editable
        self._selectable = selectable
        self._on_select_callback = on_select_callback
        self._callback_argument = callback_argument
        self.control_points = ControlPoints(parent=self)
        self.drag_reference = [0, 0]
        self.freeze()

    def add_subvisual(self, visual):
        scene.visuals.Compound.add_subvisual(self, visual)
        visual.interactive = True
        self.control_points.update_bounds()
        self.control_points.visible(False)

    def select(self, val, obj=None):
        if self.selectable:
            self.control_points.visible(val)
            if self._on_select_callback is not None:
                self._on_select_callback(self._callback_argument)

    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

    def move(self, end):
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
    def __init__(self, center=[0, 0], width=50, height=40, *args, **kwargs):
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
        self.control_points.visible(False)

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
    def __init__(self, center=[0, 0], radius=[50, 50], *args, **kwargs):
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
        self.control_points.visible(False)

    def set_center(self, val):
        self.control_points.set_center(val)
        self.form.center = val

    def update_from_controlpoints(self):
        try:
            self.form.radius = [0.5 * abs(self.control_points._width),
                                   0.5 * abs(self.control_points._height)]
        except ValueError:
            None
