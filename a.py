import numpy as np

from vispy import app, scene
from vispy.color import Color
from vispy.visuals.transforms import MatrixTransform   

class EditVisual(scene.visuals.Compound):
        
    def __init__(self, editable=True, selectable=True, on_select_callback=None,
                 callback_argument=None, *args, **kwargs):
        scene.visuals.Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.editable = editable
        self.form = None
        self._selectable = selectable
        self._on_select_callback = on_select_callback
        self._callback_argument = callback_argument
        self.control_points = ControlPoints(parent=self)
        self.drag_reference = [0, 0]
        self.freeze()

    def add_subvisual(self, visual):
        scene.visuals.Compound.add_subvisual(self, visual)
        visual.interactive = True

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