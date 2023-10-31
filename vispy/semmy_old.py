import sys
import numpy as np

from vispy import scene, app
from vispy.io import load_data_file, read_png


canvas = scene.SceneCanvas(keys='interactive', size=(1200, 600), show=True)
grid = canvas.central_widget.add_grid(margin=10)
grid.spacing = 0

title = scene.Label("SEM-Image", color='white')
title.height_max = 40
grid.add_widget(title, row=0, col=0, col_span=2)

yaxis = scene.AxisWidget(orientation='left',
                         axis_label='Y Axis',
                         axis_font_size=12,
                         axis_label_margin=50,
                         tick_label_margin=5)
yaxis.width_max = 80
grid.add_widget(yaxis, row=1, col=0)

xaxis = scene.AxisWidget(orientation='bottom',
                         axis_label='X Axis',
                         axis_font_size=12,
                         axis_label_margin=50,
                         tick_label_margin=15)

xaxis.height_max = 80
grid.add_widget(xaxis, row=2, col=1)

right_padding = grid.add_widget(row=1, col=3, row_span=1)
right_padding.width_max = 50

view = grid.add_view(row=1, col=1, border_color='white')

img_data = np.fliplr(np.flipud(read_png(load_data_file('mona_lisa/mona_lisa_sm.png'))))
interpolation = 'nearest'
scene.visuals.Image(img_data, 
                    interpolation=interpolation,
                    parent=view.scene, 
                    method='subdivide'
                            )
view.camera = 'panzoom'
view.camera.set_range(x=(0, img_data.shape[1]),
                      y=(0, img_data.shape[0]), 
                      margin=0)
view.camera.aspect = 1

xaxis.link_view(view)
yaxis.link_view(view)


if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()