import numpy as np

from vispy import io, plot as vp
from vispy.io import load_data_file, read_png


fig = vp.Fig(bgcolor='k', size=(800, 800), show=False)
img_data = read_png(load_data_file('mona_lisa/mona_lisa_sm.png'))


clim = [32, 192]
texture_format = "auto"  # None for CPUScaled, "auto" for GPUScaled

fig[0, 0].image(img_data[::-1], cmap='grays', clim=clim,
                fg_color=(0.5, 0.5, 0.5, 1), texture_format=texture_format)

if __name__ == '__main__':
    fig.show(run=True)