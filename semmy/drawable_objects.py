import numpy as np

from vispy.scene.visuals import Compound, Markers, Rectangle, Ellipse, Line 
from vispy.visuals.transforms import MatrixTransform   


# Compound from vispy.scene.visuals
class ControlPoints(Compound):
    def __init__(self, parent):
        Compound.__init__(self, [])
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

        # Markers from vispy.scene.visuals
        self.control_points = [Markers(parent=self)
                               for i in range(0, 4)]
        self.coords = np.zeros((len(self.control_points),1,2), dtype=np.float32)

        for i, c in enumerate(self.control_points):
            c.set_data(pos=self.coords[i],
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
        #center-+
        self.coords[0] = np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                                    self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]])
        #center++
        self.coords[1] = np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           + 0.5 * np.sin(self._angle) * self._height,
                                    self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           + 0.5 * np.cos(self._angle) * self._height]])
        #center+-
        self.coords[2] = np.array([[self._center[0] + 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                                    self._center[1] - 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]])
        #center--
        self.coords[3] = np.array([[self._center[0] - 0.5 * np.cos(self._angle) * self._width 
                                           - 0.5 * np.sin(self._angle) * self._height,
                                    self._center[1] + 0.5 * np.sin(self._angle) * self._width
                                           - 0.5 * np.cos(self._angle) * self._height]])
        for i, c in enumerate(self.control_points):
            c.set_data(pos=self.coords[i],
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
        self.parent.start_move(start)

    def move(self, end, modifiers=[], *args, **kwargs):
        if not self.parent.editable:
            return
        if self.selected_cp is not None:
            
            # alt for scaling from center mode
            if 'Alt' in modifiers:
                diag = end-self._center

                self._width = 2*abs(np.cos(self._angle)*diag[0] - np.sin(self._angle)*diag[1])
                self._height = 2*abs(np.sin(self._angle)*diag[0] + np.cos(self._angle)*diag[1])
                if "Control" in modifiers:
                    val = max(self._width, self._height)
                    self._width = val
                    self._height = val

                self.update_points()
                self.parent.update_from_controlpoints()
            
            #normal scaling mode where one corner is fixed
            else:
                opp_index = self.control_points.index(self.opposed_cp)
                
                opp = self.coords[opp_index,0,:]
                diag = end-opp
                center = opp+0.5*diag            

                self._width = np.cos(self._angle)*diag[0] - np.sin(self._angle)*diag[1]
                self._height = np.sin(self._angle)*diag[0] + np.cos(self._angle)*diag[1]
                
                # depending on selected point
                if opp_index == 2 or opp_index == 1:
                    self._width *= -1
                if opp_index == 0 or opp_index == 1:
                    self._height *= -1
        
                # square rectangle when holding Ctrl
                if "Control" in modifiers:
                    val = np.max(np.abs([self._width, self._height]))
                    self._width = np.sign(self._width)*val
                    self._height = np.sign(self._height)*val

                    # I have forgotten why this works
                    if opp_index == 2 or opp_index == 0:
                        offset = val/np.sqrt(2)*\
                            np.array([np.sign(self._width)  *np.cos(np.pi/4+np.sign(self._width)*np.sign(self._height)*self.angle), 
                                      np.sign(self._height) *np.sin(np.pi/4+np.sign(self._width)*np.sign(self._height)*self.angle)])
                    else:
                        offset = val/np.sqrt(2)*\
                            np.array([np.sign(self._width)  *np.cos(np.pi/4-np.sign(self._width)*np.sign(self._height)*self.angle), 
                                      np.sign(self._height) *np.sin(np.pi/4-np.sign(self._width)*np.sign(self._height)*self.angle)])
                        
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
            self._angle = angle-self.parent.drag_reference_angle
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
    
    def get_angle(self):
        return self._angle
    
    @property
    def angle(self):
        return self._angle

    def set_angle(self, val):
        self._angle = val
        self.update_points()

    def delete(self):
        self.parent.delete()
        del self


# from vispy.scene.visuals
class EditVisual(Compound):
        
    def __init__(self, 
                 control_points=None,
                 editable=True, 
                 selectable=True, 
                 on_select_callback=None,
                 callback_argument=None, 
                 *args, **kwargs):
        
        # from vispy.scene.visuals
        Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.editable = editable
        self.form = None
        self._selectable = selectable
        self._on_select_callback = on_select_callback
        self._callback_argument = callback_argument

        match control_points:
            case ('LineControlPoints', int()):
                _, num_points = control_points
                self.control_points = LineControlPoints(parent=self, num_points=num_points)
            case _:
                self.control_points = ControlPoints(parent=self)
        
        self.drag_reference = [0, 0]
        self.drag_reference_angle = 0.0
        self.freeze()

    def add_subvisual(self, visual):
        # from vispy.scene.visuals
        Compound.add_subvisual(self, visual)

    def select(self, val, obj=None):
        if self.selectable:
            self.control_points.visible(val)
            if self._on_select_callback is not None:
                self._on_select_callback(self._callback_argument)

    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

        # calculate angle of drag reference point
        x,y = self.drag_reference
        # -y because y-axis is flipped
        angle_drag = np.arctan2(-y,x)
        self.drag_reference_angle = angle_drag - self.control_points.get_angle() 

    def move(self, end, *args, **kwargs):
        if self.editable:
            shift = end[0:2] - self.drag_reference
            self.set_center(shift)
        
            self.update_transform()
    
    def rotate(self, angle):
        """
        Rotate the object by angle (in radians) around its center from the drag reference point."""
        
        if self.editable:

            # shift is difference
            abs_angle = angle-self.drag_reference_angle
            # rotate control points and therefore shape as well
            self.set_angle(abs_angle%(2*np.pi))
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
    def angle(self):
        return self.control_points.get_angle()

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
    
    def set_angle(self, val):
        self.control_points.set_angle(val)

    def select_creation_controlpoint(self):
        self.control_points.select(True, self.control_points.control_points[1])

    def output_properties(self):
        None

    def delete(self):
        self.parent = None
        del self


class EditRectVisual(EditVisual):
    def __init__(self, center=[0, 0], width=1e-6, height=1e-6, *args, **kwargs):
        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()
        self.form = Rectangle(center=center, 
                                            width=width,
                                            height=height,
                                            color= (1,0,0,0.1),
                                            border_color=(1,0,0,0.5),
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
        try:
            self.form.center = self.control_points._center
        except ValueError:
            None
    
    def output_properties(self):
       
        return dict(
                center=(self.form.center, "px"),
                width=(self.form.width, "px"),
                height=(self.form.height, "px"),
                area=(self.form.height*self.form.width, "px²"),
                angle=(np.rad2deg(self.control_points._angle), "°"),
                )
    


class EditEllipseVisual(EditVisual):
    def __init__(self, center=[0, 0], radius=[1e-6, 1e-6], *args, **kwargs):
        EditVisual.__init__(self, *args, **kwargs)
        self.unfreeze()
        self.form = Ellipse(center=center, radius=radius,
                                             color= (1,0,0,0.1),
                                             border_color=(1,0,0,0.5),
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
        try:
            self.form.center = self.control_points._center
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
                area=(np.prod(self.form.radius)*np.pi, "px²"),
                angle=(np.rad2deg(self.control_points._angle), "°"),
                )

class LineControlPoints(Compound):

    def __init__(self, parent, num_points=2, *args, **kwargs):
        Compound.__init__(self, [], *args, **kwargs)
        self.unfreeze()
        self.parent = parent
        self.num_points = num_points
        self._length = 0.0
        self.coords = np.zeros((self.num_points,2))
        if self.num_points > 2:
            self.coords[1:-2] = [0, 50]
            self.coords[-1] = [50, 0]
        self.selected_cp = None

        self.edge_color = "black"
        self.face_color = (1,1,1,0.2)
        self.marker_size = 8

        self.control_points = [Markers(parent=self)
                               for i in range(0, self.num_points)]
        for cpoint, coord in zip(self.control_points, self.coords):
            cpoint.set_data(pos=np.array([coord], dtype=np.float32),
                       edge_color=self.edge_color,
                       face_color=self.face_color,
                       size=self.marker_size)
            cpoint.interactive = True
        
        self.freeze()
    
    @property
    def length(self):
        diff = np.diff(self.coords, axis=0)
        self._length = np.sum(np.abs(np.linalg.norm(diff, axis=1))) 
        return self._length
        # deprecated
        # self._length = abs(np.linalg.norm(self.start-self.end))

    def update_points(self):

        for cpoint, coord in zip(self.control_points, self.coords):
            cpoint.set_data(
                pos=np.array([coord]),
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
        return np.array(self.coords[0]) + 0.5*(np.array(self.coords[-1]) - np.array(self.coords[0]))

    def set_center(self, val):
        shift = val-self.get_center()
        self.coords += shift
        # self.start += shift
        # self.end += shift
        self.update_points()

    def delete(self):
        self.parent.delete()
        del self
        

class EditLineVisual(EditVisual):
        
    def __init__(self, num_points=2, *args, **kwargs):

        EditVisual.__init__(self, 
                            control_points=("LineControlPoints", num_points), 
                            *args, **kwargs)
        self.unfreeze()

        self.line_color = (1,0,0,0.5)
        self.line_width = 3
        

        self.form = Line(pos=self.control_points.coords,
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
        return self.control_points.length
    
    @property
    def angles(self):
        diff = np.diff(self.control_points.coords, axis=0)
        diff[0] *= -1
        angles = np.rad2deg(np.arctan2(-diff[:,1], diff[:,0]))
        return angles
    
    def start_move(self, start):
        self.drag_reference = start[0:2] - self.control_points.get_center()

    def set_coords(self, coords):
        self.coords = coords
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
            self.form.set_data(pos=self.control_points.coords,
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
        self.control_points.select(True, self.control_points.control_points[1])

    def set_center(self, val):
        self.control_points.set_center(val[0:2])

    

    def output_properties(self):
        
        if self.control_points.num_points == 2:
            angle = self.angles
            print(angle)
        else:
            angle = abs(np.diff(self.angles))

            if angle > 180:
                angle = 360 - angle
        
        return dict(
            length=(self.length, "px"),
            angle=(angle[0], "°")
            )