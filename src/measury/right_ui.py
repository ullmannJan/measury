from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
)
from PyQt6.QtGui import QIntValidator

import numpy as np
from vispy.scene import LinePlot, InfiniteLine, Text, SceneCanvas
from vispy.scene.widgets import AxisWidget, Label


# relative imports
from .drawable_objects import (
    EditRectVisual,
    EditLineVisual,
    LineControlPoints,
    ControlPoints,
)


class RightUI(QWidget):

    content_size = None

    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout)

        self.top_layout.addWidget(QLabel("Advanced Measurement Tools"))

        self.top_layout.addStretch()

        # button to close the right ui
        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.hide_ui)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(
            "background-color: red; color: white; border: none;"
        )
        self.top_layout.addWidget(self.close_button)

        # add intensity plot
        self.vispy_intensity_plot = IntensityPlot(self.main_window)
        self.layout.addWidget(self.vispy_intensity_plot.native)

        # add buttons to customize interpolation
        self.interpolation_box = QGroupBox("Interpolation Settings")
        self.layout.addWidget(self.interpolation_box)
        self.interpolation_layout = QVBoxLayout()
        self.interpolation_box.setLayout(self.interpolation_layout)
        self.ppx_layout = QHBoxLayout()
        self.interpolation_layout.addLayout(self.ppx_layout)
        # add qlineedit that allows only integers
        self.ppx_edit = QLineEdit()
        self.ppx_edit.setValidator(QIntValidator(1, 1000))
        self.ppx_edit.setPlaceholderText("1")
        self.ppx_layout.addWidget(QLabel("points per pixel: "))
        self.ppx_layout.addWidget(self.ppx_edit)
        self.ppx_edit.textChanged.connect(self.update_intensity_plot)

        self.order_layout = QHBoxLayout()
        self.interpolation_layout.addLayout(self.order_layout)
        self.order_layout.addWidget(QLabel("Spline interpolation order: "))
        self.order_dd = QComboBox()
        self.order_dd.addItems([str(i) for i in range(6)])
        self.order_layout.addWidget(self.order_dd)
        self.order_dd.currentIndexChanged.connect(
            lambda: self.update_intensity_plot(resize=False)
        )

        self.save_button = QPushButton("Save Intensity Profile")
        self.save_button.clicked.connect(self.save_intensity_plot)
        self.layout.addWidget(self.save_button)
        # add spacer
        self.layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.width() == 0:
            self.main_window.open_right_ui_button.show()
        else:
            self.main_window.open_right_ui_button.hide()

    def hide_ui(self):
        self.content_size = self.width()
        size = self.main_window.splitter.sizes()
        self.main_window.splitter.setSizes(
            [size[0] + self.content_size // 2,
             size[1] + self.content_size // 2,
             0]
        )

        self.hide()
        self.main_window.open_right_ui_button.show()

    def show_ui(self):
        self.show()
        self.main_window.open_right_ui_button.hide()

        self.update_intensity_plot()

        # resize layout
        size = self.main_window.splitter.sizes()
        if self.content_size is None:
            self.content_size = self.layout.sizeHint().width()
        self.main_window.splitter.setSizes(
            [
                size[0] - self.content_size // 2,
                size[1] - self.content_size // 2,
                self.content_size,
            ]
        )

    def update_intensity_plot(self, resize=True):
        if self.isHidden():
            return

        selected_element = self.main_window.vispy_canvas.selected_object
        # when clicked on control points, get the parent
        if isinstance(selected_element, (LineControlPoints, ControlPoints)):
            selected_element = selected_element.parent
        if isinstance(selected_element, (EditLineVisual, EditRectVisual)):
            image = self.main_window.data_handler.img_data
            # get ui settings
            interpolation_factor = (
                int(self.ppx_edit.text()) if self.ppx_edit.text() else 1
            )
            spline_order = int(self.order_dd.currentText())

            # calculate intensity profile
            if isinstance(selected_element, EditLineVisual):
                length = selected_element.length
                if int(length) <= 0:
                    return
                intensity, _ = selected_element.intensity_profile(
                    image=image,
                    n=interpolation_factor * int(length),
                    order=spline_order,
                )
                distance = np.linspace(0, length, len(intensity))
                if selected_element.angle % 90 == 0:
                    distance += np.min(selected_element.control_points.coords[:, 0])
            elif isinstance(selected_element, EditRectVisual):
                if spline_order > 1:
                    spline_order = 1
                    self.order_dd.setCurrentText("1")
                    self.main_window.raise_error(
                        "Spline order for rectangles is limited to 1"
                    )

                length = selected_element.width
                if int(length) <= 0:
                    return
                intensity, _ = selected_element.intensity_profile(
                    image=image,
                    n_x=interpolation_factor * int(length),
                    n_y=interpolation_factor * int(selected_element.height),
                    order=spline_order,
                )
                distance = np.linspace(0, length, len(intensity))
                if selected_element.angle % 90 == 0:
                    distance += np.min(selected_element.control_points.coords[:, 0, 0])

            intensity *= 1e-3

            # automatically set correct axis limits
            if resize:
                self.vispy_intensity_plot.diagram.camera.set_range(
                    x=(np.min(distance), np.max(distance)),
                    y=(np.min(intensity), np.max(intensity)),
                )
            # update the line plot
            self.vispy_intensity_plot.intensity_line.set_data((distance, intensity))
        else:
            self.vispy_intensity_plot.intensity_line.set_data([[0, 0], [0, 0]])
            self.vispy_intensity_plot.diagram.camera.set_range(x=(0, 1), y=(0, 1))

    def save_intensity_plot(self):

        file_path = self.main_window.data_handler.save_file_dialog(
            "intensity", "CSV (*.txt *.csv)"
        )
        if not file_path:
            return

        selected_element = self.main_window.vispy_canvas.selected_object
        if isinstance(selected_element, (LineControlPoints, ControlPoints)):
            selected_element = selected_element.parent
        if isinstance(selected_element, (EditLineVisual, EditRectVisual)):
            image = self.main_window.data_handler.img_data
            interpolation_factor = (
                int(self.ppx_edit.text()) if self.ppx_edit.text() else 1
            )

            if isinstance(selected_element, EditLineVisual):
                length = int(selected_element.length)
                if length <= 0:
                    return
                intensity, eval_coords = selected_element.intensity_profile(
                    image=image, n=interpolation_factor * length
                )

                np.savetxt(
                    file_path,
                    np.column_stack((intensity, eval_coords)),
                    delimiter="\t",
                    header="intensity, pixel_x, pixel_y",
                    fmt="%.2f",
                )

            elif isinstance(selected_element, EditRectVisual):
                length = int(selected_element.width)
                if length <= 0:
                    return
                intensity, eval_coords = selected_element.intensity_profile(
                    image=image,
                    n_x=interpolation_factor * length,
                    n_y=interpolation_factor * int(selected_element.height),
                )

                np.savetxt(
                    file_path,
                    np.column_stack(
                        (intensity, np.reshape(eval_coords, (len(intensity), -1)))
                    ),
                    delimiter="\t",
                    header="intensity, pixel_x, pixel_y, pixel_x, pixel_y, ...",
                    fmt="%.2f",
                )

    def update_colors(self):
        self.vispy_intensity_plot.update_colors()


class IntensityPlot(SceneCanvas):

    CANVAS_SHAPE = (400, 300)
    main_window = None

    def __init__(self, main_window) -> None:

        self.main_window = main_window

        SceneCanvas.__init__(
            self,
            size=self.CANVAS_SHAPE,
        )

        self.unfreeze()
        grid = self.central_widget.add_grid(margin=0)

        # Create a ViewBox and add it to the Grid
        self.diagram = grid.add_view(row=1, col=1, bgcolor="white", camera="panzoom")
        # Create a Line visual and add it to the ViewBox
        self.intensity_line = LinePlot(data=[0, 0], width=1, marker_size=0)
        self.diagram.add(self.intensity_line)

        self.title_label = Label("Intensity Profile", color="black", font_size=8)
        self.title_label.height_max = 20
        grid.add_widget(self.title_label, row=0, col=1)

        # Create AxisWidget objects for the x and y axes and add them to the Grid
        self.x_axis = AxisWidget(
            orientation="bottom",
            axis_font_size=8,
            axis_label_margin=0,
            tick_label_margin=15,
            text_color="black",
        )
        self.x_axis.height_max = 30
        self.y_axis = AxisWidget(
            orientation="left",
            axis_font_size=8,
            axis_label_margin=0,
            tick_label_margin=15,
            text_color="black",
        )
        self.y_axis.width_max = 55
        grid.add_widget(self.x_axis, row=2, col=1)
        grid.add_widget(self.y_axis, row=1, col=0)

        # Link the axes to the ViewBox
        self.x_axis.link_view(self.diagram)
        self.y_axis.link_view(self.diagram)

        self.v_line = InfiniteLine(pos=-1, vertical=True, color=(0.7, 0.7, 0.7, 1))
        self.h_line = InfiniteLine(pos=-1, vertical=False, color=(0.8, 0.8, 0.8, 1))

        # Add the lines to the diagram
        self.diagram.add(self.v_line)
        self.diagram.add(self.h_line)

        # add label that displays coordinates of mouse position
        self.mouse_label = Text(
            "",
            color="black",
            font_size=8,
            anchor_x="left",
            anchor_y="top",
            pos=(55, 20),
            parent=self.central_widget,
        )

        self.freeze()

        self.update_colors()

    def update_colors(self):
        if self.main_window.is_dark_mode():
            color = "white"
        else:
            color = "black"

        self.title_label._text_visual.color = color
        self.intensity_line.set_data(color=color)
        # self.v_line.color = color
        # self.h_line.color = color
        self.mouse_label.color = color
        self.x_axis.axis.text_color = color
        self.x_axis.axis.tick_color = color
        self.y_axis.axis.text_color = color
        self.y_axis.axis.tick_color = color
        bg_color = self.main_window.get_bg_color()
        bg_color = (
            bg_color.red() / 255,
            bg_color.green() / 255,
            bg_color.blue() / 255,
            bg_color.alpha() / 255,
        )
        self.diagram.bgcolor = bg_color
        self.bgcolor = bg_color

    def on_mouse_move(self, event):

        tr = self.scene.node_transform(self.diagram)
        # Get the position of the mouse in data coordinates
        if not (
            (tr.map(event.pos)[:2] > self.diagram.size).any()
            or ((tr.map(event.pos)[:2] < (0, 0)).any())
        ):

            # main use of program
            if event.button == 3:  # mouse wheel button for changing fov
                # enable panning
                self.diagram.camera._viewbox.events.mouse_move.connect(
                    self.diagram.camera.viewbox_mouse_event
                )
                if event.is_dragging:
                    tr = self.diagram.node_transform(self.diagram.scene)
                    dpos = (
                        tr.map(event.last_event.pos)[:2] - tr.map(event.pos)[:2]
                    )  # Calculate the change in position of the mouse
                    self.diagram.camera.pan(
                        dpos
                    )  # Pan the camera based on the mouse movement

            else:
                tr = self.scene.node_transform(self.diagram.scene)
                pos = tr.map(event.pos)
                # disable panning
                self.diagram.camera._viewbox.events.mouse_move.disconnect(
                    self.diagram.camera.viewbox_mouse_event
                )

                # Update the position of the lines
                self.v_line.set_data(pos[0])
                self.h_line.set_data(pos[1])

                # Update the view
                self.update()

                # update coordinates label
                if self.mouse_label.text == "":
                    self.mouse_label.pos = (self.y_axis.width, self.title_label.height)
                self.mouse_label.text = f"{pos[0]:.2f}, {pos[1]:.2f}"
                # Update the position of the label to the
                # upper right corner of the view
